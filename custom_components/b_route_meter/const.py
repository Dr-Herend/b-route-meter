# const.py
"""Constants for the B-Route Smart Meter integration."""

DOMAIN = "b_route_meter"

# Configuration
CONF_ROUTE_B_ID = "route_b_id"
CONF_ROUTE_B_PWD = "route_b_pwd"
CONF_SERIAL_PORT = "serial_port"
CONF_RETRY_COUNT = "retry_count"
CONF_MODEL = "model"

# Defaults
DEFAULT_RETRY_COUNT = 3
DEFAULT_SERIAL_PORT = "/dev/ttyS0"
DEFAULT_UPDATE_INTERVAL = 10  # seconds

# Model Info
MODEL_BP35A1 = "BP35A1"
MODEL_BP35C2 = "BP35C2"
DEFAULT_MODEL = MODEL_BP35A1

# Device Info
DEVICE_MANUFACTURER = "ROHM Co., Ltd."
DEVICE_NAME = "B-Route Smart Meter"
DEVICE_UNIQUE_ID = "b_route_meter_device"
DEVICE_MODEL = DEFAULT_MODEL  # Using the default model as device model

# Supported Models - Add new models here
SUPPORTED_MODELS = [
    MODEL_BP35A1,
    MODEL_BP35C2,
]
