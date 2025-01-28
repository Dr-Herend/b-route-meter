"""
Sensor platform for B-Route Smart Meter
Bルートスマートメーターのセンサープラットフォーム

Defines the sensor entities that read E7/E8/E9/EA/EB data from
the B-route meter using a DataUpdateCoordinator.

BルートメーターからE7/E8/E9/EA/EBデータを取得するセンサーエンティティを
DataUpdateCoordinatorを使用して定義します。

"""

import asyncio
import logging
from datetime import timedelta
from typing import List

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .broute_reader import BRouteReader
from .const import (
    CONF_RETRY_COUNT,
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_SERIAL_PORT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_SERIAL_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DEVICE_UNIQUE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Sensor descriptions for E7/E8/E9/EA/EB
# E7/E8/E9/EA/EB向けのSensorEntityDescriptionを定義
# -----------------------------------------------------------------------------

SENSOR_TYPES: List[SensorEntityDescription] = [
    SensorEntityDescription(
        key="e7_power",
        name="B-Route Instantaneous Power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="e8_current",
        name="B-Route Instantaneous Current",
        icon="mdi:current-ac",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="e9_voltage",
        name="B-Route Instantaneous Voltage",
        icon="mdi:power-plug",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="ea_forward",
        name="B-Route Cumulative Forward",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="eb_reverse",
        name="B-Route Cumulative Reverse",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up sensor entities from a config entry
    コンフィグエントリからセンサーエンティティをセットアップ
    """
    data = entry.data
    route_b_id = data[CONF_ROUTE_B_ID]
    route_b_pwd = data[CONF_ROUTE_B_PWD]
    serial_port = data.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT)
    retry_count = data.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)

    coordinator = BRouteDataCoordinator(
        hass,
        route_b_id,
        route_b_pwd,
        serial_port,
        retry_count=retry_count,
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        BRouteSensorEntity(coordinator, description) for description in SENSOR_TYPES
    ]

    async_add_entities(sensors)


class BRouteDataCoordinator(DataUpdateCoordinator):
    """
    Coordinator to fetch data from B-route meter
    Bルートメーターからデータを取得するコーディネーター

    Schedules regular data fetch. We'll store or reuse the BRouteReader,
    and run its get_data() in a thread pool.

    一定間隔でBルートメーターからデータを取得し、取得結果を他のエンティティと共有します。
    BRouteReaderを保持して、get_data()をスレッドプールで実行します。
    """

    def __init__(
        self,
        hass,
        route_b_id,
        route_b_pwd,
        serial_port,
        retry_count=DEFAULT_RETRY_COUNT,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=DEVICE_NAME,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.reader = BRouteReader(route_b_id, route_b_pwd, serial_port)
        self.retry_count = retry_count
        self._is_connected = False
        self._connection_lock = asyncio.Lock()

    async def _try_connect(self):
        """尝试连接到设备"""
        if not self._is_connected:
            try:
                await self.hass.async_add_executor_job(self.reader.connect)
                self._is_connected = True
                _LOGGER.info("Successfully connected to B-Route meter")
            except Exception as err:
                self._is_connected = False
                _LOGGER.error("Failed to connect to B-Route meter: %s", err)
                raise

    async def _async_update_data(self):
        """获取数据并支持重试"""
        async with self._connection_lock:
            for attempt in range(self.retry_count):
                try:
                    # 如果未连接，先尝试连接
                    if not self._is_connected:
                        await self._try_connect()

                    # 获取数据
                    data = await self.hass.async_add_executor_job(self.reader.get_data)
                    if data is None:
                        raise UpdateFailed("Received empty data from meter")
                    return data

                except Exception as err:
                    self._is_connected = False  # 标记连接状态为断开
                    last_error = str(err)

                    if attempt + 1 < self.retry_count:
                        _LOGGER.warning(
                            "Update attempt %d/%d failed: %s. Retrying...",
                            attempt + 1,
                            self.retry_count,
                            last_error,
                        )
                        await asyncio.sleep(2**attempt)  # 指数退避
                    else:
                        _LOGGER.error(
                            "Update failed after %d attempts. Last error: %s",
                            self.retry_count,
                            last_error,
                        )
                        raise UpdateFailed(
                            f"Failed after {self.retry_count} attempts: {last_error}"
                        )


class BRouteSensorEntity(SensorEntity):
    """
    B-Route sensor entity referencing a SensorEntityDescription
    SensorEntityDescriptionを参照するBルートセンサーエンティティ

    We store a reference to the DataUpdateCoordinator and a SensorEntityDescription,
    and we get the current sensor value from coordinator.data.

    DataUpdateCoordinatorとSensorEntityDescriptionを参照し、
    coordinator.dataから現在値を取得してセンサーとして公開します。
    """

    def __init__(
        self,
        coordinator: BRouteDataCoordinator,
        description: SensorEntityDescription,
    ):
        self._coordinator = coordinator
        self.entity_description = description

        # Generate a unique_id from the description's key
        self._attr_unique_id = f"b_route_{description.key}"
        self._last_state = None

    @property
    def should_poll(self) -> bool:
        """
        Disable polling, because DataUpdateCoordinator handles updates
        ポーリングしない（コーディネーターが更新を通知する）
        """
        return False

    @property
    def available(self) -> bool:
        """
        Is sensor available?
        コーディネーターが正常更新していればTrue
        """
        return self._coordinator.last_update_success

    @property
    def native_value(self):
        """
        Current sensor reading
        センサーの現在値
        """
        data = self._coordinator.data
        if not data:
            return None
        # The "key" in description matches the dict key in data
        value = data.get(self.entity_description.key)
        if value is None:
            return self._last_state
        self._last_state = value
        return value

    @property
    def device_info(self):
        """
        Return device information
        デバイス情報を返す
        """
        return {
            "identifiers": {(DOMAIN, DEVICE_UNIQUE_ID)},
            "name": DEVICE_NAME,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
        }

    async def async_added_to_hass(self):
        """
        Register update listener when entity is added
        エンティティが追加された際に、コーディネーターにリスナーを登録
        """
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """
        Remove update listener when entity is removed
        エンティティが削除される際に、リスナーを解除
        """
        self._coordinator.async_remove_listener(self.async_write_ha_state)
