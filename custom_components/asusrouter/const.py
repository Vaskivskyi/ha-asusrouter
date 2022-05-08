"""ASUS Router component constants"""

from __future__ import annotations
from datetime import timedelta

from typing import Any

from homeassistant.const import (
    DATA_GIGABYTES,
    DATA_RATE_MEGABITS_PER_SECOND,
    Platform,
)
from homeassistant.components.sensor import (
    SensorStateClass,
)


# Main integrartion info
DOMAIN = "asusrouter"
DATA_ASUSROUTER = DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.DEVICE_TRACKER]


# Configurartion keys
CONF_CACHE_TIME = "cache_time"
CONF_CERT_PATH = "cert_path"
CONF_ENABLE_CONTROL = "enable_control"
CONF_ENABLE_MONITOR = "enable_monitor"
CONF_INTERFACES = "interfaces"

# Configuration keys that rerquire reload of integration
CONF_REQ_RELOAD = [CONF_INTERFACES]


# Default configuration
DEFAULT_CACHE_TIME = 5
DEFAULT_ENABLE_CONTROL = False
DEFAULT_ENABLE_MONITOR = True
DEFAULT_HTTP = {"no_ssl": "http", "ssl": "https"}
DELAULT_INTERFACES = ["WAN"]
DEFAULT_PORT = 0
DEFAULT_PORTS = {"no_ssl": 80, "ssl": 8443}
DEFAULT_SCAN_INTERVAL = timedelta(seconds = 30)
DEFAULT_SSL = False
DEFAULT_USERNAME = "admin"
DEFAULT_VERIFY_SSL = True


# Sensors types
SENSORS_TYPE_CPU = "cpu"
SENSORS_TYPE_DEVICES = "devices"
SENSORS_TYPE_MISC = "misc"
SENSORS_TYPE_NETWORK_STAT = "network_stat"
SENSORS_TYPE_PORTS = "ports"
SENSORS_TYPE_RAM = "ram"

# Sensors
SENSORS_CHANGE = ["change"]
SENSORS_CONNECTED_DEVICES = ["number"]
SENSORS_CPU = ["total", "core_1", "core_2", "core_3", "core_4", "core_5", "core_6", "core_7", "core_8"]
SENSORS_MISC = ["boottime"]
SENSORS_NETWORK_STAT = ["rx", "tx", "rx_speed", "tx_speed"]
SENSORS_PORTS = ["WAN", "LAN"]
SENSORS_RAM = ["total", "free", "used", "usage"]


# Types of results on actions
RESULT_ERROR = "error"
RESULT_SUCCESS = "success"
RESULT_UNKNOWN = "unknown"


# Constants
CONVERT_TO_MEGA = 1048576
CONVERT_TO_GIGA = 1073741824


# Keys
KEY_COORDINATOR = "coordinator"


# Params to generate sensors
KEY_SENSOR_ID = "{}_{}"

SENSORS_PARAM : dict[str, dict[str, Any]] = {
    "key": {},
    "key_group": {},
    "name": {},
    "icon": {},
    "state_class": {},
    "native_unit_of_measurement": {},
    "factor": {},
    "entity_registry_enabled_default": {},
    "extra_state_attributes": {},
}

SENSORS_PARAM_NETWORK : dict[str, dict[str, Any]] = {
    "rx": {
        "name": "{} Download",
        "icon": "mdi:download-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": DATA_GIGABYTES,
        "factor": CONVERT_TO_GIGA,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bytes",
    },
    "tx": {
        "name": "{} Upload",
        "icon": "mdi:upload-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": DATA_GIGABYTES,
        "factor": CONVERT_TO_GIGA,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bytes",
    },
    "rx_speed": {
        "name": "{} Download Speed",
        "icon": "mdi:download-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": DATA_RATE_MEGABITS_PER_SECOND,
        "factor": CONVERT_TO_MEGA,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bits/s",
    },
    "tx_speed": {
        "name": "{} Upload Speed",
        "icon": "mdi:upload-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": DATA_RATE_MEGABITS_PER_SECOND,
        "factor": CONVERT_TO_MEGA,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bits/s",
    },
}


