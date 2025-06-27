"""Sensor platform for B-Route Smart Meter.

Defines the sensor entities that read E7/E8/E9/EA/EB data from
the B-route meter using a DataUpdateCoordinator.

Also provides a diagnostic sensor that shows device status and network information.
"""

import dataclasses
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DEVICE_UNIQUE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="diagnostic_info",
        translation_key="diagnostic_info",
        icon="mdi:information",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, user needs to enable manually
    ),
    SensorEntityDescription(
        key="e7_power",
        translation_key="instantaneous_power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,  # Basic power data, enabled by default
    ),
    SensorEntityDescription(
        key="e8_current",
        translation_key="instantaneous_current",
        icon="mdi:current-ac",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,  # Basic current data, enabled by default
    ),
    SensorEntityDescription(
        key="e9_voltage",
        translation_key="instantaneous_voltage",
        icon="mdi:power-plug",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,  # Basic voltage data, enabled by default
    ),
    SensorEntityDescription(
        key="ea_forward",
        translation_key="cumulative_forward",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=True,  # Basic forward energy data, enabled by default
    ),
    SensorEntityDescription(
        key="eb_reverse",
        translation_key="cumulative_reverse",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=True,  # Basic reverse energy data, enabled by default
    ),
    # Additional optional sensors
    SensorEntityDescription(
        key="operation_status",
        translation_key="operation_status",
        icon="mdi:power",
        device_class=SensorDeviceClass.ENUM,
        options=["ON", "OFF"],
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="error_status",
        translation_key="error_status",
        icon="mdi:alert-circle",
        device_class=SensorDeviceClass.ENUM,
        options=["Normal", "Error"],
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="current_limit",
        translation_key="current_limit",
        icon="mdi:current-ac",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="meter_type",
        translation_key="meter_type",
        icon="mdi:meter-electric",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="detected_abnormality",
        translation_key="detected_abnormality",
        icon="mdi:alert",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="power_unit",
        translation_key="power_unit",
        icon="mdi:scale",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, auto-detected
    ),
    SensorEntityDescription(
        key="rssi",
        translation_key="signal_strength",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Disabled by default, but included in diagnostic info
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator = entry.runtime_data
    _LOGGER.debug("Setting up B-Route meter sensor platform")

    # Modification: avoid blocking setup, use background refresh
    try:
        # Use short timeout for first refresh to avoid blocking setup for too long
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Initial data fetch failed, will retry in background: %s", err)
        # Even if initial refresh fails, continue to set up entities so they can auto-update later

    # Entity list
    entities = []

    # Initial data
    data = coordinator.data

    # Create all sensor entities
    for description in SENSOR_TYPES:
        # Check if sensor should be enabled
        should_enable = True

        # 如果是高级功能传感器，检查它们是否被支持
        key = description.key

        # Sensors disabled by default need support check
        if not description.entity_registry_enabled_default:
            should_enable = False

            # Check if this feature is supported
            if data:
                # Operation status related sensors
                if key in ["operation_status", "error_status", "meter_type"]:
                    if (
                        data.get("operation_status") is not None
                        or data.get("error_status") is not None
                        or data.get("meter_type") is not None
                    ):
                        _LOGGER.info("Enabling operation status sensor: %s", key)
                        should_enable = True

                # Current limit sensor
                elif key == "current_limit" and data.get("current_limit") is not None:
                    _LOGGER.info("Enabling current limit sensor")
                    should_enable = True

                # Abnormality detection sensor
                elif (
                    key == "detected_abnormality"
                    and data.get("detected_abnormality") is not None
                ):
                    _LOGGER.info("Enabling abnormality detection sensor")
                    should_enable = True

                # Power unit sensor
                elif key == "power_unit" and data.get("power_unit") is not None:
                    _LOGGER.info("Enabling power unit sensor")
                    should_enable = True

                # RSSI sensor
                elif key == "rssi" and data.get("rssi") is not None:
                    _LOGGER.info("Enabling RSSI sensor")
                    should_enable = True

                # Basic sensors and diagnostic sensors are always added
                elif key in [
                    "e7_power",
                    "e8_current",
                    "e9_voltage",
                    "ea_forward",
                    "eb_reverse",
                    "diagnostic_info",
                ]:
                    should_enable = True

        # Create sensor and set entity_registry_enabled_default
        sensor = BRouteSensorEntity(entry, description)
        if should_enable != description.entity_registry_enabled_default:
            sensor.entity_description = SensorEntityDescription(
                **{
                    **dataclasses.asdict(description),
                    "entity_registry_enabled_default": should_enable,
                }
            )
            _LOGGER.debug(
                "Modified entity_registry_enabled_default for %s to %s",
                key,
                should_enable,
            )

        entities.append(sensor)

    # Add all entities
    async_add_entities(entities)


class BRouteSensorEntity(SensorEntity):
    """B-Route sensor entity referencing a SensorEntityDescription.

    We store a reference to the DataUpdateCoordinator and a SensorEntityDescription,
    and we get the current sensor value from coordinator.data.
    """

    # According to HA latest specifications, new integrations must set has_entity_name to True
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""

        self._coordinator = config_entry.runtime_data
        self.entity_description = description
        self._attr_unique_id = f"b_route_{description.key}"
        self._last_state = None
        self._last_timestamp = None
        _LOGGER.debug(
            "Setting up B-Route sensor entity for %s", self.entity_description.key
        )

    @property
    def should_poll(self) -> bool:
        """Disable polling, because DataUpdateCoordinator handles updates."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this sensor."""
        return DeviceInfo(
            identifiers={(DOMAIN, DEVICE_UNIQUE_ID)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            sw_version="1.0.0",
        )

    @property
    def available(self) -> bool:
        """Is sensor available."""
        # Always available regardless of coordinator update status
        # This allows sensors to show the last known value even when updates fail
        return True

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return entity specific state attributes."""
        attributes = {}
        data = self._coordinator.data
        timestamp_key = None

        if not data:
            return attributes

        # Add detailed attributes for diagnostic_info sensor
        if self.entity_description.key == "diagnostic_info":
            diagnostic_data = data.get("diagnostic_info")
            if diagnostic_data:
                # Device information
                if diagnostic_data.mac_address:
                    attributes["mac_address"] = diagnostic_data.mac_address
                if diagnostic_data.ipv6_address:
                    attributes["ipv6_address"] = diagnostic_data.ipv6_address
                if diagnostic_data.stack_version:
                    attributes["stack_version"] = diagnostic_data.stack_version
                if diagnostic_data.app_version:
                    attributes["app_version"] = diagnostic_data.app_version
                # Add RSSI data
                if diagnostic_data.rssi is not None:
                    attributes["rssi"] = f"{diagnostic_data.rssi} dBm"

                # Network configuration
                if diagnostic_data.channel:
                    attributes["channel"] = diagnostic_data.channel
                if diagnostic_data.pan_id:
                    attributes["pan_id"] = diagnostic_data.pan_id

                # Network status
                if diagnostic_data.active_tcp_connections:
                    attributes["tcp_connections_count"] = len(
                        diagnostic_data.active_tcp_connections
                    )
                    # Add details for each TCP connection
                    for i, conn in enumerate(diagnostic_data.active_tcp_connections):
                        attributes[f"tcp_connection_{i+1}"] = str(conn)

                if diagnostic_data.udp_ports:
                    attributes["udp_ports"] = ", ".join(
                        str(port) for port in diagnostic_data.udp_ports
                    )

                if diagnostic_data.tcp_ports:
                    attributes["tcp_ports"] = ", ".join(
                        str(port) for port in diagnostic_data.tcp_ports
                    )

                if diagnostic_data.neighbor_devices:
                    attributes["neighbor_devices_count"] = len(
                        diagnostic_data.neighbor_devices
                    )
                    # Add details for each neighbor device
                    for i, neighbor in enumerate(diagnostic_data.neighbor_devices):
                        attributes[f"neighbor_device_{i+1}"] = str(neighbor)

            # Add timestamp if available
            if self._last_timestamp:
                attributes["last_update"] = self._last_timestamp

            return attributes

        # Add R-phase and T-phase current attributes for current sensor
        if self.entity_description.key == "e8_current":
            # Add R-phase current value
            if "r_phase_current" in data and data["r_phase_current"] is not None:
                attributes["r_phase_current"] = f"{data['r_phase_current']} A"
            # Add T-phase current value
            if "t_phase_current" in data and data["t_phase_current"] is not None:
                attributes["t_phase_current"] = f"{data['t_phase_current']} A"

        # Handle attributes for other sensors
        if self.entity_description.key == "e7_power":
            timestamp_key = "power_timestamp"
        elif self.entity_description.key == "ea_forward":
            timestamp_key = "forward_timestamp"
        elif self.entity_description.key == "eb_reverse":
            timestamp_key = "reverse_timestamp"

        if data and timestamp_key in data:
            self._last_timestamp = data[timestamp_key]

        if self._last_timestamp:
            attributes["last_update"] = self._last_timestamp

        return attributes

    @property
    def native_value(self) -> float | str | None:
        """Current sensor reading."""
        data = self._coordinator.data
        _LOGGER.debug(
            "Getting value for %s, data: %s", self.entity_description.key, data
        )
        if not data:
            return None  # Return None instead of "Unknown" string
        key = self.entity_description.key

        # Special handling for diagnostic info
        if key == "diagnostic_info":
            diagnostic_data = data.get(key)
            if diagnostic_data:
                # Intelligently determine connection status - check multiple dimensions
                is_online = False

                # 1. If has IPv6 address, consider it online
                if diagnostic_data.ipv6_address:
                    is_online = True

                # 2. Or if has neighbor devices, connection still exists
                elif diagnostic_data.neighbor_devices:
                    is_online = True

                # 3. If has TCP connections, also indicates connection exists
                elif diagnostic_data.active_tcp_connections:
                    is_online = True

                # Final status determination
                connection_status = "ONLINE" if is_online else "OFFLINE"

                # Add signal strength information (if available)
                if diagnostic_data.rssi is not None:
                    # Add signal quality indicator
                    signal_quality = "GOOD"
                    if diagnostic_data.rssi < -80:
                        signal_quality = "POOR"
                    elif diagnostic_data.rssi < -70:
                        signal_quality = "FAIR"

                    connection_status = f"{connection_status} ({signal_quality} {diagnostic_data.rssi}dBm)"

                # Add connection and neighbor count information
                connection_info = []
                if diagnostic_data.active_tcp_connections:
                    tcp_count = len(diagnostic_data.active_tcp_connections)
                    connection_info.append(f"{tcp_count} CONN")

                if diagnostic_data.neighbor_devices:
                    neighbor_count = len(diagnostic_data.neighbor_devices)
                    connection_info.append(f"{neighbor_count} NEIGH")

                # Combine status components
                if connection_info:
                    return f"{connection_status} ({', '.join(connection_info)})"
                return connection_status
            return "NO DATA"

        # Normal handling for other sensors
        value = data.get(key)

        # If the value is None, try to use the last valid value
        if value is None:
            if self._last_state is not None:
                _LOGGER.debug(
                    "Using last known value for %s: %s", key, self._last_state
                )
                return self._last_state
            # If no last valid value, return None instead of "Unknown"
            return None

        # Save current value as the last valid value for next time
        self._last_state = value

        # Format numeric-type sensors
        if key in ["e7_power", "e8_current", "e9_voltage", "ea_forward", "eb_reverse"]:
            # Ensure the value is numeric
            try:
                numeric_value = float(value)
                # Use different precision based on sensor type
                if key == "e7_power":  # Power, integer
                    return int(numeric_value)
                elif key in [
                    "e8_current",
                    "e9_voltage",
                ]:  # Current and voltage, 1 decimal place
                    return round(numeric_value, 1)
                elif key in ["ea_forward", "eb_reverse"]:  # Energy, 2 decimal places
                    return round(numeric_value, 2)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid numeric value for %s: %s", key, value)
                return None  # Return None instead of "Invalid data" string

        return value

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, DEVICE_UNIQUE_ID)},
            "name": DEVICE_NAME,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
        }

    async def async_added_to_hass(self) -> None:
        """Register update listener when entity is added."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_remove_listener(self) -> None:
        """Remove the listener."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)
