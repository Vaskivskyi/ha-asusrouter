"""ASUS Router component constants"""

from __future__ import annotations

from typing import Any

from homeassistant.const import (
    DATA_GIGABYTES,
    DATA_RATE_MEGABITS_PER_SECOND,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)


DOMAIN = "asusrouter"
DATA_ASUSROUTER = DOMAIN

CONF_USE_SSL = "use_ssl"
CONF_CERT_PATH = "cert_path"
CONF_CACHE_TIME = "cache_time"
CONF_ENABLE_MONITOR = "enable_monitor"
CONF_ENABLE_CONTROL = "enable_control"
CONF_INTERFACES = "interfaces"

CONF_REQ_RELOAD = [CONF_INTERFACES]

DEFAULT_USERNAME = "admin"
DEFAULT_PORT = 0
#DEFAULT_PORT = {"no_ssl": 80, "ssl": 8443}
DEFAULT_HTTP = {"no_ssl": "http", "ssl": "https"}
DEFAULT_USE_SSL = False
DEFAULT_VERIFY_SSL = True
DEFAULT_CACHE_TIME = 5
DEFAULT_ENABLE_MONITOR = True
DEFAULT_ENABLE_CONTROL = False
DELAULT_INTERFACES = ["WAN"]

SENSORS_CPU = ["total", "core_1", "core_2", "core_3", "core_4", "core_5", "core_6", "core_7", "core_8"]

SENSORS_RAM = ["total", "free", "used", "usage"]

SENSORS_NETWORK_STAT = ["rx", "tx", "rx_speed", "tx_speed"]

SENSORS_CONNECTED_DEVICES = ["number"]

SENSORS_MISC = ["boottime"]

SENSORS_CHANGE = ["change"]

CONVERT_TO_MEGA = 1048576
CONVERT_TO_GIGA = 1073741824

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


