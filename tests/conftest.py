"""Configure pytest for b_route_meter integration tests."""

import asyncio

import pytest
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    return


@pytest.fixture
def config_data():
    """Return a sample config entry data."""
    return {
        "route_b_id": "00112233445566778899AABBCCDDEEFF",
        "route_b_pwd": "0123456789AB",
        "serial_port": "/dev/ttyUSB0",
    }


@pytest.fixture
def mock_get_source():
    """Mock hardware source."""
    return {
        "identifier": "mock_source",
        "type": "mock",
    }
