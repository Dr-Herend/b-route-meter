# B-Route Meter Integration for Home Assistant

Integration with B-route capable smart meters (such as ROHM BP35A1).

## Features

### Core Features

- Real-time power consumption monitoring
- Current and voltage readings
- Cumulative energy consumption (forward/reverse)

### Diagnostic Features

A diagnostic sensor is provided to monitor the device status and network configuration:

- Device information (MAC address, firmware versions)
- Network status (active connections, ports)
- Connection parameters (channel, PAN ID)
- Network neighbors

## Installation

Install through HACS (recommended):

1. Add this repository to HACS as a custom repository
2. Install the "B-Route Meter" integration
3. Restart Home Assistant

## Configuration

1. Add the integration through Home Assistant UI
2. Enter the required information:
   - B-route ID
   - B-route password
   - Serial port path
3. The integration will set up the sensors automatically

## Diagnostic Sensor

The diagnostic sensor is disabled by default. To enable it:

1. Go to Settings → Devices & Services
2. Find the B-Route Meter device
3. Enable the diagnostic sensor from the entity list
4. The sensor will update every 30 minutes with device status

## Development

### Setting up development environment

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install pytest pytest-asyncio pytest-cov pytest-homeassistant-custom-component black pylint

# Run tests
uv run pytest

# Check code style
uv run black custom_components/b_route_meter/
uv run pylint custom_components/b_route_meter/
```

Note: We use [uv](https://github.com/astral-sh/uv) for dependency management and test running for better performance.

### Running Tests

The test suite includes:

- Unit tests for core functionality
- Diagnostic feature tests
- Error handling scenarios
- Network status updates

## Troubleshooting

If you encounter issues:

1. Enable diagnostic sensor to check device status
2. Check the debug logs for detailed information
3. Verify serial port permissions and connection

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
