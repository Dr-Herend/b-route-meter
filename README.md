# B-Route Smart Meter Integration for Home Assistant

A custom integration for Home Assistant that reads data from Japanese smart meters via the B-route interface.

## Features

- Reads the following data via B-route interface:
  - Instantaneous Power (E7)
  - Instantaneous Current (E8)
  - Instantaneous Voltage (E9)
  - Cumulative Forward Power (EA)
  - Cumulative Reverse Power (EB)
- Automatic channel scanning and PANA authentication
- Updates every 10 seconds
- Configurable through Home Assistant UI

## Requirements

- Home Assistant 2023.x or higher
- Smart meter with B-route support
- B-route authentication ID and password
- USB to Wi-SUN adapter

## Installation

1. Copy the `b_route_meter` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Add the "B-Route Smart Meter" integration from the Integrations page
4. Enter the following configuration:
   - B-route ID (obtained from power company)
   - B-route password
   - Serial port path (default: /dev/ttyS0)

## Configuration Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| route_b_id | B-route ID | Yes | - |
| route_b_pwd | B-route password | Yes | - |
| serial_port | Serial port path | No | /dev/ttyS0 |

## Sensor Entities

The following sensor entities will be created:

- `sensor.b_route_instantaneous_power`: Instantaneous power (W)
- `sensor.b_route_instantaneous_current`: Instantaneous current (A)
- `sensor.b_route_instantaneous_voltage`: Instantaneous voltage (V)
- `sensor.b_route_cumulative_forward`: Cumulative forward power (kWh)
- `sensor.b_route_cumulative_reverse`: Cumulative reverse power (kWh)

## Troubleshooting

If you experience connection issues:

1. Verify your B-route ID and password are correct
2. Check if the serial port path is correct
3. Confirm your smart meter supports B-route functionality
4. Check Home Assistant logs for detailed error messages

## References

- [B-route ID Application (TEPCO)](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)
- [ECHONET Lite Specification](https://echonet.jp/spec_g/)

