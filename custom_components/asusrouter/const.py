"""AsusRouter constants"""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_IDENTIFIERS,
    CONF_DEVICES,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_UNIQUE_ID,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DATA_BITS,
    DATA_BYTES,
    DATA_GIGABITS,
    DATA_GIGABYTES,
    DATA_KILOBITS,
    DATA_KILOBYTES,
    DATA_MEGABITS,
    DATA_MEGABYTES,
    DATA_RATE_BITS_PER_SECOND,
    DATA_RATE_BYTES_PER_SECOND,
    DATA_RATE_GIGABITS_PER_SECOND,
    DATA_RATE_GIGABYTES_PER_SECOND,
    DATA_RATE_KILOBITS_PER_SECOND,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_RATE_MEGABITS_PER_SECOND,
    DATA_RATE_MEGABYTES_PER_SECOND,
    Platform,
)

from asusrouter.util import converters

# INTEGRATION DATA -->

DATA_ASUSROUTER = "asusrouter"
DOMAIN = "asusrouter"
KEY_COORDINATOR = "coordinator"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]

### <-- INTEGRATION DATA

### SENSORS -->

# Types
SENSORS_TYPE_CPU = "cpu"
SENSORS_TYPE_DEVICES = "devices"
SENSORS_TYPE_FIRMWARE = "firmware"
SENSORS_TYPE_GWLAN = "gwlan"
SENSORS_TYPE_LIGHT = "light"
SENSORS_TYPE_MISC = "misc"
SENSORS_TYPE_NETWORK_STAT = "network_stat"
SENSORS_TYPE_PORTS = "ports"
SENSORS_TYPE_RAM = "ram"
SENSORS_TYPE_SYSINFO = "sysinfo"
SENSORS_TYPE_TEMPERATURE = "temperature"
SENSORS_TYPE_VPN = "vpn"
SENSORS_TYPE_WAN = "wan"
SENSORS_TYPE_WLAN = "wlan"

# Sensor lists
SENSORS_CHANGE = ["change"]
SENSORS_CONNECTED_DEVICES = ["number", "devices"]
SENSORS_CPU = [
    "total",
    "core_1",
    "core_2",
    "core_3",
    "core_4",
    "core_5",
    "core_6",
    "core_7",
    "core_8",
]
SENSORS_FIRMWARE = ["state"]
SENSORS_GWLAN = {
    "sync_node": "aimesh_sync",
    "auth_mode_x": "auth_method",
    "bw_enabled": "bw_limit",
    "bw_dl": "bw_limit_download",
    "bw_ul": "bw_limit_upload",
    "expire": "expire",
    "expire_tmp": "expire_in",
    "closed": "hidden",
    "lanaccess": "lan_access",
    "maclist": "maclist",
    "macmode": "macmode",
    "wpa_psk": "password",
    "ssid": "ssid",
    "crypto": "wpa_encryption",
}
SENSORS_LIGHT = ["led"]
SENSORS_MISC = ["boottime"]
SENSORS_NETWORK_STAT = ["rx", "tx", "rx_speed", "tx_speed"]
SENSORS_PORTS = ["WAN", "LAN"]
SENSORS_RAM = ["total", "free", "used", "usage"]
SENSORS_SYSINFO = ["load_avg_1", "load_avg_5", "load_avg_15"]
SENSORS_VPN = {
    "auth_read": "auth_read",
    "errno": "error_code",
    "ip": "local_ip",
    "post_compress": "post_compress_bytes",
    "post_decompress": "post_decompress_bytes",
    "pre_compress": "pre_compress_bytes",
    "pre_decompress": "pre_decompress_bytes",
    "rip": "public_ip",
    "remote_auth": "server_auth",
    "remote_ip": "server_ip",
    "remote_port": "server_port",
    "status": "status",
    "tcp_udp_read": "tcp_udp_read_bytes",
    "tcp_udp_write": "tcp_udp_write_bytes",
    "tun_tap_read": "tun_tap_read_bytes",
    "tun_tap_write": "tun_tap_write_bytes",
    "datetime": "update_time",
}
SENSORS_VPN_SERVER = {
    "client_list": "client_list",
    "routing_table": "routing_table",
}
SENSORS_WAN = ["status", "ip", "ip_type", "gateway", "mask", "dns", "private_subnet"]
SENSORS_WLAN = {
    "auth_mode_x": "auth_method",
    "channel": "channel",
    "bw": "channel_bandwidth",
    "chanspec": "chanspec",
    "country_code": "country_code",
    "gmode_check": "gmode_check",
    "wpa_gtk_rekey": "group_key_rotation",
    "closed": "hidden",
    "maclist_x": "maclist_x",
    "macmode": "macmode",
    "mbo_enable": "mbo_enable",
    "mfp": "mfp",
    "nmode_x": "mode",
    "wpa_psk": "password",
    "radius_ipaddr": "radius_ipaddr",
    "radius_key": "radius_key",
    "radius_port": "radius_port",
    "ssid": "ssid",
    "crypto": "wpa_encryption",
    "optimizexbox_ckb": "xbox_optimized",
}

# Defaults
DEFAULT_SENSORS: dict[str, list[str]] = {SENSORS_TYPE_CPU: ["total"]}

### <-- SENSORS

### CONFIGURATION ->

# Keys
CONF_CACHE_TIME = "cache_time"
CONF_CERT_PATH = "cert_path"
CONF_CONFIRM = "confirm"
CONF_CONSIDER_HOME = "consider_home"
CONF_ENABLE_CONTROL = "enable_control"
CONF_ENABLE_MONITOR = "enable_monitor"
CONF_EVENT_DEVICE_CONNECTED = "device_connected"
CONF_EVENT_DEVICE_DISCONNECTED = "device_disconnected"
CONF_EVENT_DEVICE_RECONNECTED = "device_reconnected"
CONF_HIDE_PASSWORDS = "hide_passwords"
CONF_INTERFACES = "interfaces"
CONF_INTERVAL = "interval_"
CONF_INTERVAL_DEVICES = CONF_INTERVAL + SENSORS_TYPE_DEVICES
CONF_INTERVALS = [
    CONF_INTERVAL + SENSORS_TYPE_CPU,
    CONF_INTERVAL + SENSORS_TYPE_FIRMWARE,
    CONF_INTERVAL + SENSORS_TYPE_GWLAN,
    CONF_INTERVAL + SENSORS_TYPE_LIGHT,
    CONF_INTERVAL + SENSORS_TYPE_MISC,
    CONF_INTERVAL + SENSORS_TYPE_NETWORK_STAT,
    CONF_INTERVAL + SENSORS_TYPE_PORTS,
    CONF_INTERVAL + SENSORS_TYPE_RAM,
    CONF_INTERVAL + SENSORS_TYPE_SYSINFO,
    CONF_INTERVAL + SENSORS_TYPE_TEMPERATURE,
    CONF_INTERVAL + SENSORS_TYPE_VPN,
    CONF_INTERVAL + SENSORS_TYPE_WAN,
    CONF_INTERVAL + SENSORS_TYPE_WLAN,
]
CONF_SPLIT_INTERVALS = "split_intervals"
CONF_TRACK_DEVICES = "track_devices"
CONF_UNITS = "units"
CONF_UNITS_SPEED = "units_speed"
CONF_UNITS_TRAFFIC = "units_traffic"
CONF_VALUES_DATA = [
    DATA_BITS,
    DATA_KILOBITS,
    DATA_MEGABITS,
    DATA_GIGABITS,
    DATA_BYTES,
    DATA_KILOBYTES,
    DATA_MEGABYTES,
    DATA_GIGABYTES,
]
CONF_VALUES_DATARATE = [
    DATA_RATE_BITS_PER_SECOND,
    DATA_RATE_KILOBITS_PER_SECOND,
    DATA_RATE_MEGABITS_PER_SECOND,
    DATA_RATE_GIGABITS_PER_SECOND,
    DATA_RATE_BYTES_PER_SECOND,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_RATE_MEGABYTES_PER_SECOND,
    DATA_RATE_GIGABYTES_PER_SECOND,
]

# Keys that require reload of integration
CONF_REQ_RELOAD = [
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_CONFIRM,
    CONF_CONSIDER_HOME,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    CONF_INTERFACES,
]

# Defaults
DEFAULT_CACHE_TIME = 5
DEFAULT_CONSIDER_HOME = 45
DEFAULT_DEVICE_NAME = "Unknown device"
DEFAULT_ENABLE_CONTROL = False
DEFAULT_ENABLE_MONITOR = True
DEFAULT_EVENT: dict[str, bool] = {
    CONF_EVENT_DEVICE_CONNECTED: True,
    CONF_EVENT_DEVICE_DISCONNECTED: False,
    CONF_EVENT_DEVICE_RECONNECTED: False,
}
DEFAULT_HIDE_PASSWORDS = False
DEFAULT_HTTP = {"no_ssl": "http", "ssl": "https"}
DELAULT_INTERFACES = ["WAN"]
DEFAULT_INTERVALS = {CONF_INTERVAL + SENSORS_TYPE_FIRMWARE: 21600}
DEFAULT_PORT = 0
DEFAULT_PORTS = {"no_ssl": 80, "ssl": 8443}
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SPLIT_INTERVALS = False
DEFAULT_SSL = False
DEFAULT_TRACK_DEVICES = True
DEFAULT_UNITS_SPEED = DATA_RATE_MEGABITS_PER_SECOND
DEFAULT_UNITS_TRAFFIC = DATA_GIGABYTES
DEFAULT_USERNAME = "admin"
DEFAULT_VERIFY_SSL = True

# Simplified setup
SIMPLE_SETUP_PARAMETERS = {
    "ssl": {
        CONF_PORT: DEFAULT_PORTS["ssl"],
        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        CONF_CERT_PATH: "",
    },
    "no_ssl": {
        CONF_PORT: DEFAULT_PORTS["no_ssl"],
        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        CONF_CERT_PATH: "",
    },
}

# Types of steps
STEP_TYPE_COMPLETE = "complete"
STEP_TYPE_SIMPLE = "simplified"

# Types of results on actions
RESULT_CONNECTION_REFUSED = "connection_refused"
RESULT_ERROR = "error"
RESULT_LOGIN_BLOCKED = "login_blocked"
RESULT_SUCCESS = "success"
RESULT_UNKNOWN = "unknown"
RESULT_WRONG_CREDENTIALS = "wrong_credentials"

### <-- CONFIGURATION

### CONSTANTS & CONVERTERS -->

CONVERT_SPEED = {
    DATA_RATE_BITS_PER_SECOND: 1,
    DATA_RATE_KILOBITS_PER_SECOND: 1024,
    DATA_RATE_MEGABITS_PER_SECOND: 1048576,
    DATA_RATE_GIGABITS_PER_SECOND: 1073741824,
    DATA_RATE_BYTES_PER_SECOND: 8,
    DATA_RATE_KILOBYTES_PER_SECOND: 8192,
    DATA_RATE_MEGABYTES_PER_SECOND: 8388608,
    DATA_RATE_GIGABYTES_PER_SECOND: 8589934592,
}
CONVERT_TO_MEGA = 1048576
CONVERT_TO_GIGA = 1073741824
CONVERT_TRAFFIC = {
    DATA_BITS: 0.125,
    DATA_KILOBITS: 128,
    DATA_MEGABITS: 131072,
    DATA_GIGABITS: 134217728,
    DATA_BYTES: 1,
    DATA_KILOBYTES: 1024,
    DATA_MEGABYTES: 1048576,
    DATA_GIGABYTES: 1073741824,
}

### <-- CONSTANTS & CONVERTERS

### MISC -->

# Connection state
CONNECTION_BLOCKED = "blocked"
CONNECTION_CONNECTED = "connected"
CONNECTION_DISCONNECTED = "disconnected"

# Connection type
CONNECTION_TYPE_2G = "2.4 GHz"
CONNECTION_TYPE_5G = "5 GHz"
CONNECTION_TYPE_6G = "6 GHz"
CONNECTION_TYPE_WIRED = "Wired"

# Device attributes
DEVICE_ATTRIBUTE_CONNECTION_TIME = "connection_time"
DEVICE_ATTRIBUTE_CONNECTION_TYPE = "connection_type"
DEVICE_ATTRIBUTE_GUEST = "guest"
DEVICE_ATTRIBUTE_INTERNET = "internet"
DEVICE_ATTRIBUTE_INTERNET_MODE = "internet_mode"
DEVICE_ATTRIBUTE_IP_TYPE = "ip_type"
DEVICE_ATTRIBUTE_LAST_ACTIVITY = "last_activity"
DEVICE_ATTRIBUTE_RSSI = "rssi"
DEVICE_ATTRIBUTE_RX_SPEED = "rx_speed"
DEVICE_ATTRIBUTE_TX_SPEED = "tx_speed"
DEVICE_ATTRIBUTES: list[str] = [
    DEVICE_ATTRIBUTE_CONNECTION_TIME,
    DEVICE_ATTRIBUTE_CONNECTION_TYPE,
    DEVICE_ATTRIBUTE_GUEST,
    DEVICE_ATTRIBUTE_INTERNET,
    DEVICE_ATTRIBUTE_INTERNET_MODE,
    DEVICE_ATTRIBUTE_IP_TYPE,
    DEVICE_ATTRIBUTE_RSSI,
    DEVICE_ATTRIBUTE_RX_SPEED,
    DEVICE_ATTRIBUTE_TX_SPEED,
]

# Params to generate sensors
KEY_GWLAN = "wl"
KEY_OVPN_CLIENT = "vpn_client"
KEY_OVPN_SERVER = "vpn_server"
KEY_SENSOR_ID = "{}_{}"
KEY_WLAN = "wl"

NAME_GWLAN = {
    "0.1": "Guest 2.4 GHz 1",
    "0.2": "Guest 2.4 GHz 2",
    "0.3": "Guest 2.4 GHz 3",
    "0.4": "Guest 2.4 GHz 4",
    "1.1": "Guest 5 GHz 1",
    "1.2": "Guest 5 GHz 2",
    "1.3": "Guest 5 GHz 3",
    "1.4": "Guest 5 GHz 4",
    "2.1": "Guest 5 GHz (2) 1",
    "2.2": "Guest 5 GHz (2) 2",
    "2.3": "Guest 5 GHz (2) 3",
    "2.4": "Guest 5 GHz (2) 4",
    "3.1": "Guest 6 GHz 1",
    "3.2": "Guest 6 GHz 2",
    "3.3": "Guest 6 GHz 3",
    "3.4": "Guest 6 GHz 4",
}
NAME_OVPN_CLIENT = "OpenVPN Client"
NAME_OVPN_SERVER = "OpenVPN Server"
NAME_WLAN = {
    0: "Wireless 2.4 GHz",
    1: "Wireless 5 GHz",
    2: "Wireless 5 GHz (2)",
    3: "Wireless 6 GHz",
}

SENSORS_PARAM: dict[str, dict[str, Any]] = {
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

SENSORS_PARAM_NETWORK: dict[str, dict[str, Any]] = {
    "rx": {
        "name": "{} Download",
        "icon": "mdi:download-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "factor": CONVERT_TRAFFIC,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bytes",
    },
    "tx": {
        "name": "{} Upload",
        "icon": "mdi:upload-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "factor": CONVERT_TRAFFIC,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bytes",
    },
    "rx_speed": {
        "name": "{} Download Speed",
        "icon": "mdi:download-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "factor": CONVERT_SPEED,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bits/s",
    },
    "tx_speed": {
        "name": "{} Upload Speed",
        "icon": "mdi:upload-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "factor": CONVERT_SPEED,
        "entity_registry_enabled_default": True,
        "raw_attribute": "bits/s",
    },
}

### <-- MISC

### DIAGNOSTICS -->

TO_REDACT = {CONF_PASSWORD, CONF_UNIQUE_ID, CONF_USERNAME}
TO_REDACT_DEV = {ATTR_CONNECTIONS, ATTR_IDENTIFIERS}
TO_REDACT_STATE = {"WAN IP"}
TO_REDACT_ATTRS = {CONF_DEVICES, CONF_PASSWORD, "ip", "ssid"}

### <-- DIAGNOSTICS

### SERVICES -->

SERVICE_ALLOWED_ADJUST_GWLAN: dict[str, Callable | None] = {
    "sync_node": converters.int_from_bool,
    "bw_enabled": converters.int_from_bool,
    "bw_dl": None,
    "bw_ul": None,
    "expire": None,
    "closed": converters.int_from_bool,
    "lanaccess": converters.int_from_bool,
    "ssid": None,
}

SERVICE_ALLOWED_ADJUST_WLAN: dict[str, Callable | None] = {
    "closed": converters.int_from_bool,
    "ssid": None,
}

### <-- SERVICES
