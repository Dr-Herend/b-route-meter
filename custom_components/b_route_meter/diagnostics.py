"""Diagnostics support for B-Route Meter."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_ROUTE_B_ID, CONF_ROUTE_B_PWD, CONF_SERIAL_PORT, DOMAIN

TO_REDACT = [
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SERIAL_PORT,
]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    # Get current data from coordinator
    data = coordinator.data

    # Get diagnostic info
    diagnostic_info = None
    if data and "diagnostic_info" in data:
        diagnostic_info_obj = data["diagnostic_info"]
        # Convert diagnostic_info object to a dictionary
        if diagnostic_info_obj:
            diagnostic_info = {
                "mac_address": diagnostic_info_obj.mac_address,
                "ipv6_address": diagnostic_info_obj.ipv6_address,
                "stack_version": diagnostic_info_obj.stack_version,
                "app_version": diagnostic_info_obj.app_version,
                "channel": diagnostic_info_obj.channel,
                "pan_id": diagnostic_info_obj.pan_id,
                "tcp_connections_count": len(
                    diagnostic_info_obj.active_tcp_connections or []
                ),
                "tcp_ports": diagnostic_info_obj.tcp_ports,
                "udp_ports": diagnostic_info_obj.udp_ports,
                "neighbor_devices_count": len(
                    diagnostic_info_obj.neighbor_devices or []
                ),
            }

    # Create sensor data record
    sensor_data = {}
    if data:
        if "e7_power" in data:
            sensor_data["power"] = data["e7_power"]
        if "e8_current" in data:
            sensor_data["current"] = data["e8_current"]
        if "e9_voltage" in data:
            sensor_data["voltage"] = data["e9_voltage"]
        if "ea_forward" in data:
            sensor_data["forward"] = data["ea_forward"]
        if "eb_reverse" in data:
            sensor_data["reverse"] = data["eb_reverse"]

    # Create diagnostics data
    diagnostics_data = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "title": entry.title,
            "domain": entry.domain,
            "source": entry.source,
            "state": entry.state,
            "supports_unload": entry.supports_unload,
            "supports_remove_device": entry.supports_remove_device,
            "pref_disable_new_entities": entry.pref_disable_new_entities,
            "pref_disable_polling": entry.pref_disable_polling,
            "disabled_by": entry.disabled_by,
        },
        "data": async_redact_data(dict(entry.data), TO_REDACT),
        "diagnostic_info": diagnostic_info,
        "sensor_data": sensor_data,
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": (
                str(coordinator.last_exception) if coordinator.last_exception else None
            ),
            "update_interval": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "update_success_count": getattr(coordinator, "_update_success_count", 0),
            "update_fail_count": getattr(coordinator, "_update_fail_count", 0),
        },
    }

    return diagnostics_data
