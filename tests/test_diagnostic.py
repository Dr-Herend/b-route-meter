"""Test the diagnostic functionality of the b_route_meter integration."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant

from custom_components.b_route_meter.adapter_interface import DiagnosticInfo
from custom_components.b_route_meter.coordinator import (
    DIAGNOSTIC_UPDATE_INTERVAL,
    BRouteDataCoordinator,
)
from custom_components.b_route_meter.sensor import SENSOR_TYPES, BRouteSensorEntity


class MockBP35A1:
    """Mock BP35A1 adapter for testing."""

    def __init__(self):
        self.connected = False
        self._mock_diagnostic_info = DiagnosticInfo(
            mac_address="001D129012345678",
            ipv6_address="FE80::1234:5678:9ABC:DEF0",
            stack_version="1.2.3",
            app_version="4.5.6",
            channel=33,
            pan_id="8888",
            active_tcp_connections=[
                {
                    "handle": "1",
                    "remote_addr": "FE80::1111:2222:3333:4444",
                    "remote_port": "0E1A",
                    "local_port": "0E1A",
                }
            ],
            udp_ports=[3610, 716],
            tcp_ports=[3610],
            neighbor_devices=[
                {
                    "ipv6_addr": "FE80::1111:2222:3333:4444",
                    "mac_addr": "001D1290ABCDEF01",
                }
            ],
        )

    def connect(self):
        """Mock connect method."""
        self.connected = True

    def close(self):
        """Mock close method."""
        self.connected = False

    def get_diagnostic_info(self):
        """Return mock diagnostic info."""
        if not self.connected:
            raise RuntimeError("Not connected")
        return self._mock_diagnostic_info


@pytest.fixture
def mock_coordinator(hass: HomeAssistant) -> BRouteDataCoordinator:
    """Create a mock coordinator with a mock adapter."""
    with patch(
        "custom_components.b_route_meter.adapter_factory.AdapterFactory.create"
    ) as mock_create:
        # Set up mock adapter
        mock_adapter = MockBP35A1()
        mock_create.return_value = mock_adapter

        # Create coordinator with mock adapter
        coordinator = BRouteDataCoordinator(
            hass=hass,
            route_b_id="00112233445566778899AABBCCDDEEFF",
            route_b_pwd="0123456789AB",
            serial_port="/dev/ttyUSB0",
        )
        return coordinator


def test_diagnostic_sensor_entity():
    """Test the diagnostic sensor entity."""
    # Find diagnostic sensor description
    diagnostic_description = next(
        desc for desc in SENSOR_TYPES if desc.device_class == SensorDeviceClass.ENUM
    )

    # Create mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.data = {
        "route_b_id": "00112233445566778899AABBCCDDEEFF",
        "route_b_pwd": "0123456789AB",
        "serial_port": "/dev/ttyUSB0",
    }

    # Create entity
    entity = BRouteSensorEntity(mock_config_entry, diagnostic_description)

    # Verify entity attributes
    assert entity.unique_id == "b_route_diagnostic_info"
    assert not entity.should_poll
    assert entity.entity_description.entity_registry_enabled_default is False


@pytest.mark.asyncio
async def test_diagnostic_info_update(hass: HomeAssistant, mock_coordinator):
    """Test diagnostic info update timing."""
    # Initial update
    await mock_coordinator._async_update_data()
    assert "diagnostic_info" in mock_coordinator.data
    initial_update_time = mock_coordinator._last_diagnostic_update

    # Update before interval - should not update diagnostic info
    await mock_coordinator._async_update_data()
    assert mock_coordinator._last_diagnostic_update == initial_update_time

    # Simulate time passing
    mock_coordinator._last_diagnostic_update = (
        datetime.now().timestamp() - DIAGNOSTIC_UPDATE_INTERVAL - 1
    )

    # Update after interval - should update diagnostic info
    await mock_coordinator._async_update_data()
    assert mock_coordinator._last_diagnostic_update > initial_update_time


@pytest.mark.asyncio
async def test_diagnostic_info_format(hass: HomeAssistant, mock_coordinator):
    """Test the format of diagnostic information."""
    mock_adapter = mock_coordinator.adapter
    diagnostic_info = mock_adapter.get_diagnostic_info()

    # Verify diagnostic info structure
    assert diagnostic_info.mac_address == "001D129012345678"
    assert diagnostic_info.ipv6_address == "FE80::1234:5678:9ABC:DEF0"
    assert diagnostic_info.stack_version == "1.2.3"
    assert diagnostic_info.app_version == "4.5.6"
    assert diagnostic_info.channel == 33
    assert diagnostic_info.pan_id == "8888"

    # Verify network status
    assert len(diagnostic_info.active_tcp_connections) == 1
    assert len(diagnostic_info.udp_ports) == 2
    assert len(diagnostic_info.tcp_ports) == 1
    assert len(diagnostic_info.neighbor_devices) == 1


@pytest.mark.asyncio
async def test_diagnostic_info_error_handling(hass: HomeAssistant, mock_coordinator):
    """Test error handling in diagnostic info updates."""
    mock_adapter = mock_coordinator.adapter

    # Test when adapter is not connected
    mock_adapter.connected = False
    data = mock_coordinator.data
    assert data is not None  # Regular meter data should still be available

    # Verify diagnostic info errors don't crash the coordinator
    mock_adapter._mock_diagnostic_info = None
    data = mock_coordinator.data
    assert data is not None  # Coordinator should continue working
