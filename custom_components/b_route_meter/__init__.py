"""B-Route Smart Meter Integration.

This file is typically used to set up the integration at runtime:
 - async_setup_entry: Called when user adds the integration
 - async_unload_entry: Called to remove it
"""

import logging
import sys
import traceback

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from .const import (
    CONF_MODEL,
    CONF_RETRY_COUNT,
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_SERIAL_PORT,
    DEFAULT_MODEL,
    DEFAULT_RETRY_COUNT,
    DEFAULT_SERIAL_PORT,
    DOMAIN,
)
from .coordinator import BRouteDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up B-Route meter from a config entry."""
    try:
        data = entry.data
        route_b_id = data[CONF_ROUTE_B_ID]
        route_b_pwd = data[CONF_ROUTE_B_PWD]
        serial_port = data.get(CONF_SERIAL_PORT, DEFAULT_SERIAL_PORT)
        retry_count = data.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)
        model = data.get(CONF_MODEL, DEFAULT_MODEL)

        # Enhanced logging for debugging
        _LOGGER.info(
            "Setting up B-Route meter integration (entry_id: %s) with: model=%s, serial_port=%s, retry_count=%s",
            entry.entry_id,
            model,
            serial_port,
            retry_count,
        )

        # Log Python version and module information for debugging
        _LOGGER.debug(
            "Python version: %s",
            sys.version,
        )

        # Initialize coordinator with detailed error handling
        try:
            coordinator = BRouteDataCoordinator(
                hass,
                route_b_id=route_b_id,
                route_b_pwd=route_b_pwd,
                serial_port=serial_port,
                retry_count=retry_count,
                model=model,
            )
            entry.runtime_data = coordinator
            _LOGGER.debug("Successfully created BRouteDataCoordinator")
        except Exception as err:
            _LOGGER.error(
                "Failed to create data coordinator: %s - %s",
                err,
                traceback.format_exc(),
            )
            raise

        # Set up cleanup on HA stop
        async def _async_cleanup(event: Event) -> None:
            """Clean up resources when Home Assistant stops."""
            _LOGGER.info(
                "Cleaning up B-Route meter integration (entry_id: %s)", entry.entry_id
            )
            try:
                await coordinator.async_close()
                _LOGGER.debug("Successfully closed coordinator connection")
            except Exception as err:
                _LOGGER.error("Error during cleanup: %s", err)

        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_cleanup)
        )

        # Store coordinator instance in hass.data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Set up platforms with enhanced error handling
        # 使用异步并发设置，避免阻塞
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        _LOGGER.info("B-Route meter integration setup completed successfully")
        return True

    except Exception as err:
        _LOGGER.error(
            "Error during B-Route meter integration setup: %s - %s",
            err,
            traceback.format_exc(),
        )
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    _LOGGER.info("Unloading B-Route meter integration (entry_id: %s)", entry.entry_id)

    try:
        coordinator = entry.runtime_data

        # Properly close coordinator connection
        try:
            await coordinator.async_close()
            _LOGGER.debug("Successfully closed coordinator connection on unload")
        except Exception as err:
            _LOGGER.error("Error closing coordinator connection: %s", err)

        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

        if unload_ok:
            _LOGGER.debug("Successfully unloaded platforms")
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.info("B-Route meter integration successfully unloaded")
        else:
            _LOGGER.warning("Failed to unload platforms properly")

        return unload_ok

    except Exception as err:
        _LOGGER.error(
            "Error during B-Route meter integration unload: %s - %s",
            err,
            traceback.format_exc(),
        )
        return False
