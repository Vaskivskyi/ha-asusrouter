"""AsusRouter constants"""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_IDENTIFIERS,
    CONF_DEVICES,
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
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from asusrouter.util import converters

from .dataclass import ARSensorDescription

# INTEGRATION DATA -->

ASUSROUTER = "asusrouter"
DOMAIN = ASUSROUTER
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

### NUMERIC -->

NUMERIC_CORES = range(1, 9)  # maximum of 8 cores from 1 to 8
NUMERIC_GWLAN = range(1, 5)  # maximum of 4 guest WLANs from 1 to 4

### <-- NUMERIC

### GENERAL DATA -->

FREE = "free"
RX = "rx"
RX_SPEED = "rx_speed"
TOTAL = "total"
TX = "tx"
TX_SPEED = "tx_speed"
UNKNOWN = "unknown"
USAGE = "usage"
USED = "used"

### <-- GENERAL DATA

### GENERAL STATES -->

CONNECTED = "connected"

### <-- GENERAL STATES

### GENERAL TYPES -->

CONNECTION_2G = "2.4 GHz"
CONNECTION_5G = "5 GHz"
CONNECTION_5G2 = "5 GHz-2"
CONNECTION_6G = "6 GHz"
CONNECTION_LIST = [
    CONNECTION_2G,
    CONNECTION_5G,
    CONNECTION_5G2,
    CONNECTION_6G,
]
CONNECTION_WIRED = "Wired"
CORE = "core"
CPU = "cpu"
DEVICES = "devices"
FIRMWARE = "firmware"
GWLAN = "gwlan"
LIGHT = "light"
LOAD_AVG = "load_avg"
MISC = "misc"
NETWORK_STAT = "network_stat"
PARENTAL_CONTROL = "parental_control"
PORTS = "ports"
RAM = "ram"
SYSINFO = "sysinfo"
TEMPERATURE = "temperature"
VPN = "vpn"
WAN = "wan"
WLAN = "wlan"
WLAN_2GHZ = "2ghz"
WLAN_5GHZ = "5ghz"
WLAN_5GHZ2 = "5ghz2"
WLAN_6GHZ = "6ghz"

### <-- GENERAL TYPES

### LABELS -->

LABEL_LOAD_AVG = "Load Average"
LABEL_RX = "Download"
LABEL_SPEED = "Speed"
LABEL_TX = "Upload"

LABELS_LOAD_AVG = {
    f"{sensor}": f"{LABEL_LOAD_AVG} ({sensor} min)" for sensor in ["1", "5", "15"]
}
LABELS_TEMPERATURE = {
    CPU: f"{TEMPERATURE} {CPU.upper()}",
    WLAN_2GHZ: f"{TEMPERATURE} {CONNECTION_2G}",
    WLAN_5GHZ: f"{TEMPERATURE} {CONNECTION_5G}",
    WLAN_5GHZ2: f"{TEMPERATURE} {CONNECTION_5G2}",
    WLAN_6GHZ: f"{TEMPERATURE} {CONNECTION_6G}",
}

### <-- LABELS

### GENERAL VALUES -->

BITS_PER_SECOND = "bits/s"
BYTES = "bytes"
IP = "ip"
MAC = "mac"
NAME = "name"
PASSWORD = "password"
SSID = "ssid"
STATE = "state"

### <-- GENERAL VALUES

### SENSORS -->

# Sensor lists
SENSORS_CHANGE = ["change"]
SENSORS_CONNECTED_DEVICES = ["number", DEVICES, "latest", "latest_time"]
SENSORS_CPU = [TOTAL]
for i in NUMERIC_CORES:
    SENSORS_CPU.append(f"{CORE}_{i}")
SENSORS_FIRMWARE = [STATE]
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
    "wpa_psk": PASSWORD,
    SSID: SSID,
    "crypto": "wpa_encryption",
}
SENSORS_LIGHT = ["led"]
SENSORS_MISC = ["boottime"]
SENSORS_NETWORK_STAT = [RX, RX_SPEED, TX, TX_SPEED]
SENSORS_PARENTAL_CONTROL = [STATE]
SENSORS_PORTS = ["LAN", "WAN"]
SENSORS_RAM = [FREE, TOTAL, USAGE, USED]
SENSORS_SYSINFO = ["load_avg_1", "load_avg_5", "load_avg_15"]
SENSORS_VPN = {
    "auth_read": "auth_read",
    "errno": "error_code",
    IP: "local_ip",
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
SENSORS_WAN = ["status", IP, "ip_type", "gateway", "mask", "dns", "private_subnet"]
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
    "wpa_psk": PASSWORD,
    "radius_ipaddr": "radius_ipaddr",
    "radius_key": "radius_key",
    "radius_port": "radius_port",
    SSID: SSID,
    "crypto": "wpa_encryption",
    "optimizexbox_ckb": "xbox_optimized",
}

# Defaults
DEFAULT_SENSORS: dict[str, list[str]] = {CPU: [TOTAL]}

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
CONF_INTERVAL_DEVICES = CONF_INTERVAL + DEVICES
CONF_INTERVALS = [
    CONF_INTERVAL + CPU,
    CONF_INTERVAL + FIRMWARE,
    CONF_INTERVAL + GWLAN,
    CONF_INTERVAL + LIGHT,
    CONF_INTERVAL + MISC,
    CONF_INTERVAL + NETWORK_STAT,
    CONF_INTERVAL + PARENTAL_CONTROL,
    CONF_INTERVAL + PORTS,
    CONF_INTERVAL + RAM,
    CONF_INTERVAL + SYSINFO,
    CONF_INTERVAL + TEMPERATURE,
    CONF_INTERVAL + VPN,
    CONF_INTERVAL + WAN,
    CONF_INTERVAL + WLAN,
]
CONF_LATEST_CONNECTED = "latest_connected"
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
DEFAULT_INTERVALS = {CONF_INTERVAL + FIRMWARE: 21600}
DEFAULT_LATEST_CONNECTED = 5
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
CONNECTION_TYPE_2G = CONNECTION_2G
CONNECTION_TYPE_5G = CONNECTION_5G
CONNECTION_TYPE_5G2 = CONNECTION_5G2
CONNECTION_TYPE_6G = CONNECTION_6G
CONNECTION_TYPE_WIRED = CONNECTION_WIRED
CONNECTION_TYPE_UNKNOWN = UNKNOWN

# Device attributes
DEVICE_ATTRIBUTE_CONNECTION_TIME = "connection_time"
DEVICE_ATTRIBUTE_CONNECTION_TYPE = "connection_type"
DEVICE_ATTRIBUTE_GUEST = "guest"
DEVICE_ATTRIBUTE_GUEST_ID = "guest_id"
DEVICE_ATTRIBUTE_INTERNET = "internet"
DEVICE_ATTRIBUTE_INTERNET_MODE = "internet_mode"
DEVICE_ATTRIBUTE_IP_TYPE = "ip_type"
DEVICE_ATTRIBUTE_LAST_ACTIVITY = "last_activity"
DEVICE_ATTRIBUTE_RSSI = "rssi"
DEVICE_ATTRIBUTE_RX_SPEED = RX_SPEED
DEVICE_ATTRIBUTE_TX_SPEED = TX_SPEED
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

# Generate wireless networks
NAME_GWLAN = {}
NAME_WLAN = {}
for i in range(len(CONNECTION_LIST)):
    # WLAN
    NAME_WLAN[i] = f"Wireless {CONNECTION_LIST[i]}"
    # Guest WLAN
    for j in NUMERIC_GWLAN:
        NAME_GWLAN[f"{i}.{j}"] = f"Guest {CONNECTION_LIST[i]} {j}"

NAME_OVPN_CLIENT = "OpenVPN Client"
NAME_OVPN_SERVER = "OpenVPN Server"

SENSORS_PARAM: dict[str, dict[str, Any]] = {
    "key": {},
    "key_group": {},
    NAME: {},
    "icon": {},
    "state_class": {},
    "native_unit_of_measurement": {},
    "factor": {},
    "entity_registry_enabled_default": {},
    "extra_state_attributes": {},
}

SENSORS_PARAM_NETWORK: dict[str, dict[str, Any]] = {
    RX: {
        NAME: f"{LABEL_RX}",
        "icon": "mdi:download-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "factor": CONVERT_TRAFFIC,
        "entity_registry_enabled_default": True,
        "raw_attribute": BYTES,
    },
    RX_SPEED: {
        NAME: f"{LABEL_RX} {LABEL_SPEED}",
        "icon": "mdi:download-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "factor": CONVERT_SPEED,
        "entity_registry_enabled_default": True,
        "raw_attribute": BITS_PER_SECOND,
    },
    TX: {
        NAME: f"{LABEL_TX}",
        "icon": "mdi:upload-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "factor": CONVERT_TRAFFIC,
        "entity_registry_enabled_default": True,
        "raw_attribute": BYTES,
    },
    TX_SPEED: {
        NAME: f"{LABEL_TX} {LABEL_SPEED}",
        "icon": "mdi:upload-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "factor": CONVERT_SPEED,
        "entity_registry_enabled_default": True,
        "raw_attribute": BITS_PER_SECOND,
    },
}

### <-- MISC

### DIAGNOSTICS -->

TO_REDACT = {PASSWORD, CONF_UNIQUE_ID, CONF_USERNAME}
TO_REDACT_DEV = {ATTR_CONNECTIONS, ATTR_IDENTIFIERS}
TO_REDACT_STATE = {"WAN IP"}
TO_REDACT_ATTRS = {CONF_DEVICES, PASSWORD, IP, SSID, "list"}

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
    SSID: None,
}

SERVICE_ALLOWED_ADJUST_WLAN: dict[str, Callable | None] = {
    "closed": converters.int_from_bool,
    SSID: None,
}

SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS: list[str] = [
    "block",
    "disable",
]

### <-- SERVICES

### SENSORS -->

STATIC_SENSORS_TEMPERATURE = {
    (TEMPERATURE, sensor): ARSensorDescription(
        key=sensor,
        key_group=TEMPERATURE,
        name=LABELS_TEMPERATURE[sensor],
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )
    for sensor in LABELS_TEMPERATURE
}
STATIC_SENSORS_LOAD_AVG = {
    (SYSINFO, f"{LOAD_AVG}_{sensor}"): ARSensorDescription(
        key=f"{LOAD_AVG}_{sensor}",
        key_group=SYSINFO,
        name=LABELS_LOAD_AVG[sensor],
        icon="mdi:cpu-32-bit",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )
    for sensor in LABELS_LOAD_AVG
}

### <-- SENSORS
