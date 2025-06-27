"""Define the BRouteDataCoordinator class."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Mapping

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .adapter_factory import AdapterFactory
from .const import (
    DEFAULT_MODEL,
    DEFAULT_RETRY_COUNT,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_NAME,
)

# Diagnostic info update interval (30 minutes)
DIAGNOSTIC_UPDATE_INTERVAL = 1800

_LOGGER = logging.getLogger(__name__)


class BRouteDataCoordinator(DataUpdateCoordinator[Mapping[str, Any]]):
    """Coordinator to fetch data from B-route meter.

    Schedules regular data fetch using the appropriate adapter for the meter.
    Runs adapter operations in a thread pool to avoid blocking.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        route_b_id: str,
        route_b_pwd: str,
        serial_port: str,
        retry_count: int = DEFAULT_RETRY_COUNT,
        model: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: HomeAssistant instance
            route_b_id: B-route ID
            route_b_pwd: B-route password
            serial_port: Serial port device path
            retry_count: Number of retry attempts
            model: Model of the B-route adapter
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DEVICE_NAME,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
            # Reduce timeout for first update, fail fast
            request_refresh_debouncer=None,
        )

        # Create adapter instance for the configured model
        self.adapter = AdapterFactory.create(
            model,
            route_b_id=route_b_id,
            route_b_pwd=route_b_pwd,
            serial_port=serial_port,
        )
        self.retry_count = retry_count
        self._is_connected = False
        self._connection_lock = asyncio.Lock()
        self._last_diagnostic_update = None
        self._diagnostic_info = None

    async def _try_connect(self) -> None:
        """Connect to the meter and set the connection status."""
        if not self._is_connected:
            _LOGGER.info("Try connecting to B-Route meter")
            try:
                # Use shorter timeout to avoid blocking setup for too long
                await asyncio.wait_for(
                    self.hass.async_add_executor_job(self.adapter.connect),
                    timeout=30.0,  # 30秒超时，相比默认更短
                )
                self._is_connected = True
                _LOGGER.info("Successfully connected to B-Route meter")
            except asyncio.TimeoutError:
                self._is_connected = False
                _LOGGER.error("Connection to B-Route meter timed out after 30 seconds")
                raise UpdateFailed("Connection to B-Route meter timed out") from None
            except Exception as err:
                self._is_connected = False
                _LOGGER.error("Failed to connect to B-Route meter: %s", err)
                raise UpdateFailed("Failed to connect to B-Route meter") from err

    def _raise_update_failed(self, message: str) -> None:
        """Raise an UpdateFailed exception with the given message."""
        raise UpdateFailed(message)

    async def _update_diagnostic_info(self) -> None:
        """Update diagnostic information if needed."""
        now = datetime.now()

        # Check if diagnostic info needs update
        if (
            self._last_diagnostic_update is None
            or (now.timestamp() - self._last_diagnostic_update)
            >= DIAGNOSTIC_UPDATE_INTERVAL
        ):
            try:
                if self._is_connected:
                    self._diagnostic_info = await self.hass.async_add_executor_job(
                        self.adapter.get_diagnostic_info
                    )
                    self._last_diagnostic_update = now.timestamp()
                    _LOGGER.debug("Successfully updated diagnostic information")
            except Exception as err:
                _LOGGER.warning("Failed to update diagnostic information: %s", err)

    async def _async_update_data(self) -> Mapping[str, Any]:
        """Get the latest data from the B-route meter.

        This will connect to the meter if not already connected,
        then read data from the meter.

        Returns:
            Mapping[str, Any]: A dictionary of sensor data from the meter.
        """
        # Check if we have previous data that can be used as fallback
        previous_data = self.data
        if previous_data:
            _LOGGER.debug("Using previous data as fallback if update fails")

        # Prepare an empty result
        result = {}

        # First, try to update diagnostic info if needed
        await self._update_diagnostic_info()
        if self._diagnostic_info:
            result["diagnostic_info"] = self._diagnostic_info

            # 添加 RSSI 数据作为单独的传感器
            if self._diagnostic_info.rssi is not None:
                result["rssi"] = self._diagnostic_info.rssi

        # Initialize a counter to track update attempts
        update_attempt = 0
        max_attempts = self.retry_count

        # Keep trying to fetch data until we succeed or reach max attempts
        while update_attempt < max_attempts:
            update_attempt += 1
            _LOGGER.debug(
                "Fetching data from B-Route meter (attempt %d/%d)",
                update_attempt,
                max_attempts,
            )

            # Record start time to measure how long the update takes
            start_time = datetime.now().timestamp()
            success = False
            meter_data = None

            # First, make sure we're connected
            if not self._is_connected:
                try:
                    async with self._connection_lock:
                        await self._try_connect()
                except UpdateFailed as e:
                    _LOGGER.warning(
                        "Update attempt %d/%d failed: %s. Retrying in %d seconds",
                        update_attempt,
                        max_attempts,
                        e,
                        update_attempt,
                    )
                    # 快速失败，减少初始化时间
                    if update_attempt == 1:
                        await asyncio.sleep(1)  # 第一次失败只等待1秒
                    else:
                        await asyncio.sleep(update_attempt)
                    continue

            # Now try to get data from the meter
            try:
                meter_data = await self.hass.async_add_executor_job(
                    self.adapter.get_data
                )

                # 检查数据是否有效 - 所有主要值都为 None 可能表示通信问题
                all_none = all(
                    getattr(meter_data, attr) is None
                    for attr in ["power", "current", "voltage", "forward", "reverse"]
                )

                if all_none:
                    _LOGGER.warning(
                        "All meter readings are None. Check device communication."
                    )
                    if update_attempt < max_attempts:
                        # 重置连接并尝试重新连接
                        self._is_connected = False
                        try:
                            async with self._connection_lock:
                                await self._try_connect()
                        except Exception as e:
                            _LOGGER.error("Failed to reconnect: %s", e)
                        # 减少等待时间
                        await asyncio.sleep(min(update_attempt, 3))  # 最多等待3秒
                        continue
                    else:
                        _LOGGER.warning(
                            "After %d attempts, still no valid readings", max_attempts
                        )
                else:
                    success = True

            except Exception as e:
                _LOGGER.error("Error fetching data from B-Route meter: %s", e)
                self._is_connected = False  # 标记为断开连接，下次会尝试重新连接
                if update_attempt < max_attempts:
                    # 快速失败，减少初始化时间
                    await asyncio.sleep(min(update_attempt, 3))  # 最多等待3秒
                    continue
                elif previous_data:
                    # 如果有之前的数据，则使用之前的数据
                    _LOGGER.warning(
                        "Using previous data due to consecutive failures after %d attempts",
                        max_attempts,
                    )
                    return previous_data
                else:
                    _LOGGER.error("No previous data available as fallback")
                    self._raise_update_failed(
                        f"Failed to fetch data from B-Route meter after {max_attempts} attempts: {e}"
                    )

            # Calculate how long the update took
            end_time = datetime.now().timestamp()
            elapsed_seconds = end_time - start_time

            _LOGGER.debug(
                "Finished fetching B-Route Smart Meter data in %.3f seconds (success: %s)",
                elapsed_seconds,
                success,
            )

            # If we successfully got data, convert it to a format suitable for sensors
            if meter_data:
                # Add meter readings to result
                if meter_data.power is not None:
                    result["e7_power"] = meter_data.power
                if meter_data.current is not None:
                    result["e8_current"] = meter_data.current
                    # 添加单相电流值到结果中
                    if (
                        hasattr(meter_data, "r_phase_current")
                        and meter_data.r_phase_current is not None
                    ):
                        result["r_phase_current"] = meter_data.r_phase_current
                    if (
                        hasattr(meter_data, "t_phase_current")
                        and meter_data.t_phase_current is not None
                    ):
                        result["t_phase_current"] = meter_data.t_phase_current
                if meter_data.voltage is not None:
                    result["e9_voltage"] = meter_data.voltage
                if meter_data.forward is not None:
                    result["ea_forward"] = meter_data.forward
                if meter_data.reverse is not None:
                    result["eb_reverse"] = meter_data.reverse

                # Add timestamps if available
                if (
                    hasattr(meter_data, "forward_timestamp")
                    and meter_data.forward_timestamp
                ):
                    result["ea_forward_timestamp"] = meter_data.forward_timestamp
                if (
                    hasattr(meter_data, "reverse_timestamp")
                    and meter_data.reverse_timestamp
                ):
                    result["eb_reverse_timestamp"] = meter_data.reverse_timestamp

                # 添加新的传感器数据
                # 根据设备特性和支持情况添加数据
                # 操作状态信息 - 只有当设备明确标记了支持才添加这些传感器
                if meter_data.has_operational_info:
                    # 操作状态
                    if meter_data.operation_status is not None:
                        result["operation_status"] = (
                            "ON" if meter_data.operation_status else "OFF"
                        )
                    # 错误状态
                    if meter_data.error_status is not None:
                        result["error_status"] = (
                            "Error" if meter_data.error_status else "Normal"
                        )
                    # 设备类型
                    if meter_data.meter_type is not None:
                        result["meter_type"] = meter_data.meter_type

                # 限制信息
                if meter_data.has_limit_info and meter_data.current_limit is not None:
                    result["current_limit"] = meter_data.current_limit

                # 异常检测信息
                if (
                    meter_data.has_abnormality_detection
                    and meter_data.detected_abnormality is not None
                ):
                    result["detected_abnormality"] = meter_data.detected_abnormality

                # 电量单位
                if meter_data.power_unit is not None:
                    result["power_unit"] = meter_data.power_unit

            # If we successfully got any readings, break out of the retry loop
            if success:
                break

        # If result is still empty, use previous data if available
        if not result and previous_data:
            _LOGGER.warning("No data returned, using previous data")
            return previous_data

        # Always include diagnostic info if available, even if other readings failed
        if self._diagnostic_info and "diagnostic_info" not in result:
            result["diagnostic_info"] = self._diagnostic_info

            # 添加 RSSI 数据作为单独的传感器
            if self._diagnostic_info.rssi is not None:
                result["rssi"] = self._diagnostic_info.rssi

        return result

    async def async_close(self) -> None:
        """Close the adapter connection when coordinator is stopped."""
        if self._is_connected:
            try:
                await self.hass.async_add_executor_job(self.adapter.close)
            except Exception as err:
                _LOGGER.error("Error closing adapter connection: %s", err)
            finally:
                self._is_connected = False
