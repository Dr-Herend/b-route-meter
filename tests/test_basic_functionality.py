"""Basic functionality tests for b_route_meter integration."""

import pytest

from custom_components.b_route_meter.adapter_factory import AdapterFactory
from custom_components.b_route_meter.adapter_interface import (
    AdapterInterface,
    DiagnosticInfo,
    MeterReading,
)
from custom_components.b_route_meter.const import (
    CONF_ADAPTER_TYPE,
    CONF_ROUTE_B_ID,
    CONF_ROUTE_B_PWD,
    CONF_SERIAL_PORT,
)


def test_meter_reading_dataclass():
    """Test MeterReading dataclass functionality."""
    reading = MeterReading()

    # Test that we can set attributes
    reading.power = 123.45
    reading.forward = 67.89
    reading.power_unit = 0.1
    reading.operation_status = True

    # Test that attributes are correctly set
    assert reading.power == 123.45
    assert reading.forward == 67.89
    assert reading.power_unit == 0.1
    assert reading.operation_status is True


def test_diagnostic_info_dataclass():
    """Test DiagnosticInfo dataclass functionality."""
    diag = DiagnosticInfo()

    # Test that we can set basic attributes
    diag.mac_address = "001D129012345678"
    diag.ipv6_address = "FE80::1234:5678:9ABC:DEF0"
    diag.stack_version = "1.2.3"
    diag.app_version = "4.5.6"
    diag.channel = 33
    diag.pan_id = "8888"

    # Test that we can set list attributes
    diag.active_tcp_connections = [{"handle": "1", "remote_addr": "test"}]
    diag.udp_ports = [3610, 716]
    diag.tcp_ports = [3610]
    diag.neighbor_devices = [{"ipv6_addr": "FE80::1", "mac_addr": "001D1290"}]

    # Test that all attributes are correctly set
    assert diag.mac_address == "001D129012345678"
    assert diag.ipv6_address == "FE80::1234:5678:9ABC:DEF0"
    assert diag.stack_version == "1.2.3"
    assert diag.app_version == "4.5.6"
    assert diag.channel == 33
    assert diag.pan_id == "8888"
    assert len(diag.active_tcp_connections) == 1
    assert diag.udp_ports == [3610, 716]
    assert diag.tcp_ports == [3610]
    assert len(diag.neighbor_devices) == 1


def test_adapter_factory():
    """Test adapter factory functionality."""
    config = {
        CONF_ROUTE_B_ID: "00112233445566778899AABBCCDDEEFF",
        CONF_ROUTE_B_PWD: "0123456789AB",
        CONF_SERIAL_PORT: "/dev/ttyUSB0",
        CONF_ADAPTER_TYPE: "BP35A1",
    }

    adapter = AdapterFactory.create(
        config[CONF_ADAPTER_TYPE],
        route_b_id=config[CONF_ROUTE_B_ID],
        route_b_pwd=config[CONF_ROUTE_B_PWD],
        serial_port=config[CONF_SERIAL_PORT],
    )

    # Test that adapter is created and has correct type
    assert adapter is not None
    assert hasattr(adapter, "connect")
    assert hasattr(adapter, "close")
    assert hasattr(adapter, "get_data")
    assert hasattr(adapter, "get_diagnostic_info")


def test_adapter_interface_methods():
    """Test that adapter interface defines required methods."""
    # Test that the interface has the required methods
    interface_methods = ["connect", "close", "get_data", "get_diagnostic_info"]

    for method in interface_methods:
        assert hasattr(AdapterInterface, method)


class TestMockAdapter(AdapterInterface):
    """Mock adapter for testing."""

    def __init__(self, route_b_id: str, route_b_pwd: str, serial_port: str):
        self.route_b_id = route_b_id
        self.route_b_pwd = route_b_pwd
        self.serial_port = serial_port
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def get_data(self) -> MeterReading:
        reading = MeterReading()
        reading.power = 123.45
        reading.forward = 67.89
        reading.power_unit = 0.1
        reading.operation_status = True
        return reading

    def get_diagnostic_info(self) -> DiagnosticInfo:
        diag = DiagnosticInfo()
        diag.mac_address = "001D129012345678"
        diag.ipv6_address = "FE80::1234:5678:9ABC:DEF0"
        return diag


def test_mock_adapter():
    """Test mock adapter implementation."""
    adapter = TestMockAdapter(
        route_b_id="00112233445566778899AABBCCDDEEFF",
        route_b_pwd="0123456789AB",
        serial_port="/dev/ttyUSB0",
    )

    # Test connection
    assert not adapter.connected
    adapter.connect()
    assert adapter.connected

    # Test data retrieval
    data = adapter.get_data()
    assert isinstance(data, MeterReading)
    assert data.power == 123.45
    assert data.forward == 67.89
    assert data.power_unit == 0.1
    assert data.operation_status is True

    # Test diagnostic info
    diag = adapter.get_diagnostic_info()
    assert isinstance(diag, DiagnosticInfo)
    assert diag.mac_address == "001D129012345678"
    assert diag.ipv6_address == "FE80::1234:5678:9ABC:DEF0"

    # Test disconnection
    adapter.close()
    assert not adapter.connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
