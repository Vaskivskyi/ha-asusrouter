"""ASUS Router component constants"""

DOMAIN = "asusrouter"
DATA_ASUSROUTER = DOMAIN

CONF_USE_SSL = "use_ssl"
CONF_CERT_PATH = "cert_path"
CONF_CACHE_TIME = "cache_time"
CONF_ENABLE_MONITOR = "enable_monitor"
CONF_ENABLE_CONTROL = "enable_control"

DEFAULT_USERNAME = "admin"
DEFAULT_PORT = 0
#DEFAULT_PORT = {"no_ssl": 80, "ssl": 8443}
DEFAULT_HTTP = {"no_ssl": "http", "ssl": "https"}
DEFAULT_USE_SSL = False
DEFAULT_VERIFY_SSL = True
DEFAULT_CACHE_TIME = 5
DEFAULT_ENABLE_MONITOR = True
DEFAULT_ENABLE_CONTROL = False

SENSORS_CPU = ["total", "core_1", "core_2", "core_3", "core_4", "core_5", "core_6", "core_7", "core_8"]

SENSORS_RAM = ["total", "free", "used", "usage"]

SENSORS_NETWORK_STAT = ["rx", "tx", "rx_speed", "tx_speed"]

SENSORS_CONNECTED_DEVICES = ["number"]

SENSORS_MISC = ["boottime"]

SENSORS_CHANGE = ["change"]

