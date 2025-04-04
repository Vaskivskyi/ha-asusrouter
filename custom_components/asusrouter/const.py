"""AsusRouter constants module."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.update import UpdateDeviceClass
from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_IDENTIFIERS,
    CONF_DEVICES,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_UNIQUE_ID,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    PERCENTAGE,
    EntityCategory,
    Platform,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)

from asusrouter.modules.openvpn import AsusOVPNClient, AsusOVPNServer
from asusrouter.modules.parental_control import (
    AsusBlockAll,
    AsusParentalControl,
)
from asusrouter.modules.port_forwarding import AsusPortForwarding
from asusrouter.modules.system import AsusSystem
from asusrouter.modules.wireguard import (
    AsusWireGuardClient,
    AsusWireGuardServer,
)
from asusrouter.modules.wlan import AsusWLAN, Wlan
from asusrouter.tools import converters

from .dataclass import (
    ARBinarySensorDescription,
    ARButtonDescription,
    AREntityDescription,
    ARLightDescription,
    ARSensorDescription,
    ARSwitchDescription,
    ARUpdateDescription,
)

# INTEGRATION DATA -->

ASUSROUTER = "asusrouter"
DOMAIN = ASUSROUTER
MANUFACTURER = "ASUSTek"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]

# <-- INTEGRATION DATA

# NUMERIC -->

NUMERIC_CORES = range(1, 9)  # maximum of 8 cores from 1 to 8
NUMERIC_GWLAN = range(1, 4)  # maximum of 4 guest WLANs from 1 to 3
NUMERIC_LAN = range(1, 9)  # maximum of 8 LAN ports from 1 to 8
NUMERIC_OVPN_SERVER = range(1, 3)  # maximum of 2 OVPN servers from 1 to 2
NUMERIC_WAN = range(0, 4)  # maximum of 4 WAN ports from 0 to 3
NUMERIC_WLAN = range(0, 4)  # maximum of 4 WLANs from 0 to 3

# <-- NUMERIC

# GENERAL DATA -->

ACCESS_POINT = "access_point"
ACTION = "action"
ACTION_MODE = "action_mode"
AIMESH = "aimesh"
ALIAS = "alias"
ALL_CLIENTS = "all_clients"
API_ID = "api_id"
API_TYPE = "api_type"
APPLY = "apply"
AURA = "aura"
BITS_PER_SECOND = "bits/s"
BOOTTIME = "boottime"
BRIDGE = "bridge"
BYTES = "bytes"
CONFIG = "config"
CONNECTION = "connection"
COORDINATOR = "coordinator"
CORE = "core"
CPU = "cpu"
DEVICES = "devices"
DNS = "dns"
DSL = "dsl"
FIRMWARE = "firmware"
FREE = "free"
GWLAN = "gwlan"
HTTP = "http"
HTTPS = "https"
IP = "ip"
IP_EXTERNAL = "ip_external"
IPS = "ips"
ISO = "iso"
LACP = "lacp"
LAN = "lan"
LED = "led"
LEVEL = "level"
LIGHT = "light"
LIST = "list"
LOAD_AVG = "load_avg"
MAC = "mac"
MEDIA_BRIDGE = "media_bridge"
METHOD = "method"
MISC = "misc"
MODEL = "model"
NAME = "name"
NETWORK = "network"
NETWORK_STAT = "network_stat"
NEXT = "next"
NODE = "node"
NO_SSL = "no_ssl"
NUMBER = "number"
PARENT = "parent"
PARENTAL_CONTROL = "parental_control"
PASSWORD = "password"
PORT = "port"
PORT_EXTERNAL = "port_external"
PORT_FORWARDING = "port_forwarding"
PORTS = "ports"
PRODUCT_ID = "product_id"
PROTOCOL = "protocol"
RAM = "ram"
ROUTER = "router"
RX = "rx"
RX_SPEED = "rx_speed"
SENSORS = "sensors"
SSID = "ssid"
SSL = "ssl"
STATE = "state"
STATUS = "status"
SYSINFO = "sysinfo"
TEMPERATURE = "temperature"
TIMESTAMP = "timestamp"
TOTAL = "total"
TX = "tx"
TX_SPEED = "tx_speed"
TYPE = "type"
UNIQUE_ID = "unique_id"
UNKNOWN = "unknown"
USAGE = "usage"
USB = "usb"
USED = "used"
VPN = "vpn"
WAN = "wan"
WIRED = "wired"
WLAN = "wlan"
WLAN_2GHZ = "2ghz"
WLAN_5GHZ = "5ghz"
WLAN_5GHZ2 = "5ghz2"
WLAN_6GHZ = "6ghz"

# <-- GENERAL DATA

LIST_PORTS = [
    LAN,
    USB,
    WAN,
]

MAP_WLAN = {
    WLAN_2GHZ: 0,
    WLAN_5GHZ: 1,
    WLAN_5GHZ2: 2,
    WLAN_6GHZ: 3,
}

# MIGRATION TEMP -->

MAP_NETWORK_TEMP = {
    BRIDGE.upper(): BRIDGE,
    USB.upper(): USB,
    WAN.upper(): WAN,
    WIRED.upper(): WIRED,
    "WLAN0": WLAN_2GHZ,
    "WLAN1": WLAN_5GHZ,
    "WLAN2": WLAN_5GHZ2,
    "WLAN3": WLAN_6GHZ,
}

# <-- MIGRATION TEMP

# GENERAL STATES -->

CONNECTED = "connected"

# <-- GENERAL STATES

# LABELS -->

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

LABEL_LOAD_AVG = "Load Average"
LABEL_RX = "Download"
LABEL_SPEED = "Speed"
LABEL_TEMPERATURE = "Temperature"
LABEL_TX = "Upload"
LABEL_WLAN = "Wireless"
LABEL_WLAN_2GHZ = "2.4 GHz"
LABEL_WLAN_5GHZ = "5 GHz"
LABEL_WLAN_5GHZ2 = "5 GHz-2"
LABEL_WLAN_6GHZ = "6 GHz"
LABELS_LOAD_AVG = {
    sensor: f"{LABEL_LOAD_AVG} ({sensor} min)" for sensor in ("1", "5", "15")
}
LABELS_TEMPERATURE = {
    "cpu": "Temperature CPU",
    Wlan.FREQ_2G: "Temperature 2.4 GHz",
    Wlan.FREQ_5G: "Temperature 5 GHz",
    Wlan.FREQ_5G2: "Temperature 5 GHz-2",
    Wlan.FREQ_6G: "Temperature 6 GHz",
}
LABELS_WLAN = {
    WLAN_2GHZ: LABEL_WLAN_2GHZ,
    WLAN_5GHZ: LABEL_WLAN_5GHZ,
    WLAN_5GHZ2: LABEL_WLAN_5GHZ2,
    WLAN_6GHZ: LABEL_WLAN_6GHZ,
}

# <-- LABELS

# MODES -->

# AiMesh Node
MODE_NODE = [
    BOOTTIME,
    CPU,
    FIRMWARE,
    LED,
    NETWORK,
    PORTS,
    RAM,
    SYSINFO,
    TEMPERATURE,
]

# Access Point
MODE_ACCESS_POINT = MODE_NODE.copy()
MODE_ACCESS_POINT.extend([WLAN, AURA])

# Media Bridge
MODE_MEDIA_BRIDGE = MODE_ACCESS_POINT.copy()

# Router
MODE_ROUTER = MODE_ACCESS_POINT.copy()
MODE_ROUTER.extend(
    [
        DSL,
        GWLAN,
        "ovpn_client",
        "ovpn_server",
        PARENTAL_CONTROL,
        PORT_FORWARDING,
        "speedtest",
        VPN,
        "wan",
        "wireguard_client",
        "wireguard_server",
    ]
)

MODE_SENSORS = {
    ACCESS_POINT: MODE_ACCESS_POINT,
    MEDIA_BRIDGE: MODE_MEDIA_BRIDGE,
    NODE: MODE_NODE,
    ROUTER: MODE_ROUTER,
}

# <-- MODES

# SENSORS LIST -->

SENSORS_AIMESH = [NUMBER, LIST]
SENSORS_BOOTTIME = ["datetime"]
SENSORS_CHANGE = ["change"]
SENSORS_CONNECTED_DEVICES = [
    NUMBER,
    DEVICES,
    "latest",
    "latest_time",
    "gn_number",
]
SENSORS_CPU = [TOTAL, USED, USAGE]
SENSORS_FIRMWARE = [STATE, "state_beta"]
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
SENSORS_LED = [STATE]
SENSORS_MISC = [BOOTTIME]
SENSORS_NETWORK = [RX, RX_SPEED, TX, TX_SPEED]
SENSORS_OVPN_CLIENT = {
    "active": "active",
    "auth_read": "auth_read",
    "datetime": "update_time",
    "errno": "error",
    "error": "error",
    IP: "local_ip",
    "login": "login",
    "name": "name",
    "password": "password",
    "post_compress": "post_compress_bytes",
    "post_decompress": "post_decompress_bytes",
    "pre_compress": "pre_compress_bytes",
    "pre_decompress": "pre_decompress_bytes",
    "rip": "public_ip",
    "remote_auth": "server_auth",
    "remote_ip": "server_ip",
    "remote_port": "server_port",
    STATUS: STATUS,
    "tcp_udp_read": "tcp_udp_read_bytes",
    "tcp_udp_write": "tcp_udp_write_bytes",
    "tun_tap_read": "tun_tap_read_bytes",
    "tun_tap_write": "tun_tap_write_bytes",
    "vpnc_id": "vpnc_id",
    "vpnc_unit": "vpnc_unit",
}
SENSORS_OVPN_SERVER = {
    "address": "address",
    "advertise_dns": "advertise_dns",
    "allow_lan": "allow_lan",
    "allow_specific_clients": "allow_specific_clients",
    "allow_wan": "allow_wan",
    "auth_mode": "auth_mode",
    "cipher": "cipher",
    "client_list": "clients",
    "client_specific_config": "client_specific_config",
    "client_to_client": "client_to_client",
    "clients": "clients",
    "compression": "compression",
    "dhcp": "dhcp",
    "digest": "digest",
    "hmac": "hmac",
    "interface": "interface",
    "netmask": "netmask",
    "password_only": "password_only",
    "port": "port",
    "protocol": "protocol",
    "remote_address": "remote_address",
    "response_to_dns": "response_to_dns",
    "routing_table": "routing_table",
    "server_r1": "server_r1",
    "server_r2": "server_r2",
    "subnet": "subnet",
    "tls_keysize": "tls_keysize",
    "tls_reneg": "tls_reneg",
    "unit": "unit",
}

SENSORS_PARENTAL_CONTROL = ["block_all", STATE]
SENSORS_PORT_FORWARDING = [STATE]
SENSORS_PORTS = [LAN, WAN]
SENSORS_RAM = [FREE, TOTAL, USAGE, USED]
SENSORS_SYSINFO = [f"{LOAD_AVG}_{sensor}" for sensor in LABELS_LOAD_AVG]
SENSORS_WAN = {
    "dns": "dns",
    "expires": "expires",
    "gateway": "gateway",
    "ip_address": "ip_address",
    "lease": "lease",
    "mask": "mask",
}
SENSORS_WIREGUARD_CLIENT = {
    "active": "active",
    "address": "address",
    "allowed_ips": "allowed_ips",
    "endpoint_address": "endpoint_address",
    "endpoint_port": "endpoint_port",
    "error": "error",
    "keep_alive": "keep_alive",
    "login": "login",
    "name": "name",
    "nat": "nat",
    "password": "password",
    "private_key": "private_key",
    "psk": "psk",
    "public_key": "public_key",
    "vpnc_id": "vpnc_id",
    "vpnc_unit": "vpnc_unit",
}
SENSORS_WIREGUARD_SERVER = {
    "address": "address",
    "dns": "dns",
    "keep_alive": "keep_alive",
    "lan_access": "lan_access",
    "nat6": "nat6",
    "port": "port",
    "private_key": "private_key",
    "psk": "psk_state",
    "public_key": "public_key",
    "clients": "clients",
}
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

# <-- SENSORS

# CONFIGURATION CONSTANTS & DEFAULTS -->

# Keys
CONF_CACHE_TIME = "cache_time"
CONF_CERT_PATH = "cert_path"
CONF_CLIENT_DEVICE = "client_device"
CONF_CLIENT_FILTER = "client_filter"
CONF_CLIENT_FILTER_LIST = "client_filter_list"
CONF_CLIENTS_IN_ATTR = "clients_in_attr"
CONF_CONFIRM = "confirm"
CONF_CONSIDER_HOME = "consider_home"
CONF_CREATE_DEVICES = "create_devices"
CONF_ENABLE_CONTROL = "enable_control"
CONF_EVENT_DEVICE_CONNECTED = "device_connected"
CONF_EVENT_DEVICE_DISCONNECTED = "device_disconnected"
CONF_EVENT_DEVICE_RECONNECTED = "device_reconnected"
CONF_EVENT_NODE_CONNECTED = "node_connected"
CONF_EVENT_NODE_DISCONNECTED = "node_disconnected"
CONF_EVENT_NODE_RECONNECTED = "node_reconnected"
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
    CONF_INTERVAL + NETWORK,
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
CONF_MODE = "mode"
CONF_SPLIT_INTERVALS = "split_intervals"
CONF_TRACK_DEVICES = "track_devices"
CONF_UNITS = "units"
CONF_UNITS_SPEED = "units_speed"
CONF_UNITS_TRAFFIC = "units_traffic"

# Defaults
CONF_DEFAULT_CACHE_TIME = 5
CONF_DEFAULT_CLIENT_DEVICE = False
CONF_DEFAULT_CLIENT_FILTER = "no_filter"
CONF_DEFAULT_CLIENTS_IN_ATTR = True
CONF_DEFAULT_CONSIDER_HOME = 45
CONF_DEFAULT_CREATE_DEVICES = False
CONF_DEFAULT_ENABLE_CONTROL = False
CONF_DEFAULT_EVENT: dict[str, bool] = {
    CONF_EVENT_DEVICE_CONNECTED: True,
    CONF_EVENT_DEVICE_DISCONNECTED: False,
    CONF_EVENT_DEVICE_RECONNECTED: False,
    CONF_EVENT_NODE_CONNECTED: True,
    CONF_EVENT_NODE_DISCONNECTED: True,
    CONF_EVENT_NODE_RECONNECTED: True,
}
CONF_DEFAULT_HIDE_PASSWORDS = False
CONF_DEFAULT_INTERFACES = [WAN.upper()]
CONF_DEFAULT_INTERVALS = {CONF_INTERVAL + FIRMWARE: 600}
CONF_DEFAULT_LATEST_CONNECTED = 5
CONF_DEFAULT_MODE = ROUTER
CONF_DEFAULT_PORT = 0
CONF_DEFAULT_PORTS = {NO_SSL: 80, SSL: 8443}
CONF_DEFAULT_SCAN_INTERVAL = 30
CONF_DEFAULT_SPLIT_INTERVALS = False
CONF_DEFAULT_SSL = True
CONF_DEFAULT_TRACK_DEVICES = True
CONF_DEFAULT_UNITS_SPEED = UnitOfDataRate.MEGABITS_PER_SECOND
CONF_DEFAULT_UNITS_TRAFFIC = UnitOfInformation.GIGABYTES
CONF_DEFAULT_USERNAME = "admin"

# Labels
CONF_LABELS_CLIENT_FILTER = {
    "no_filter": "No filter / All clients",
    "include": "Include only",
    "exclude": "Exclude devices",
}
CONF_LABELS_INTERFACES = {
    BRIDGE: "Bridge",
    f"{LACP}1": "LACP1",
    f"{LACP}2": "LACP2",
    USB: USB.upper(),
    WAN: WAN.upper(),
    WIRED: CONNECTION_WIRED,
    WLAN_2GHZ: CONNECTION_2G,
    WLAN_5GHZ: CONNECTION_5G,
    WLAN_5GHZ2: CONNECTION_5G2,
    WLAN_6GHZ: CONNECTION_6G,
}
CONF_LABELS_MODE = {
    ROUTER: "Router",
    NODE: "AiMesh node",
    ACCESS_POINT: "Access Point",
    MEDIA_BRIDGE: "Media bridge",
}

# Options that require restarting the integration
CONF_REQ_RELOAD = [
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_CLIENT_DEVICE,
    CONF_CLIENT_FILTER,
    CONF_CLIENT_FILTER_LIST,
    CONF_CLIENTS_IN_ATTR,
    CONF_CONFIRM,
    CONF_CONSIDER_HOME,
    CONF_CREATE_DEVICES,
    CONF_ENABLE_CONTROL,
    CONF_EVENT_DEVICE_CONNECTED,
    CONF_EVENT_DEVICE_DISCONNECTED,
    CONF_EVENT_DEVICE_RECONNECTED,
    CONF_EVENT_NODE_CONNECTED,
    CONF_EVENT_NODE_DISCONNECTED,
    CONF_EVENT_NODE_RECONNECTED,
    CONF_HIDE_PASSWORDS,
    CONF_INTERFACES,
    CONF_INTERVAL_DEVICES,
    CONF_LATEST_CONNECTED,
    CONF_MODE,
    CONF_SPLIT_INTERVALS,
    CONF_SCAN_INTERVAL,
    CONF_TRACK_DEVICES,
]
CONF_REQ_RELOAD.extend(CONF_INTERVALS)

# Input values
CONF_VALUES_DATA = [
    UnitOfInformation.BITS,
    UnitOfInformation.KILOBITS,
    UnitOfInformation.MEGABITS,
    UnitOfInformation.GIGABITS,
    UnitOfInformation.BYTES,
    UnitOfInformation.KILOBYTES,
    UnitOfInformation.MEGABYTES,
    UnitOfInformation.GIGABYTES,
]
CONF_VALUES_DATARATE = [
    UnitOfDataRate.BITS_PER_SECOND,
    UnitOfDataRate.KILOBITS_PER_SECOND,
    UnitOfDataRate.MEGABITS_PER_SECOND,
    UnitOfDataRate.GIGABITS_PER_SECOND,
    UnitOfDataRate.BYTES_PER_SECOND,
    UnitOfDataRate.KILOBYTES_PER_SECOND,
    UnitOfDataRate.MEGABYTES_PER_SECOND,
    UnitOfDataRate.GIGABYTES_PER_SECOND,
]
CONF_VALUES_MODE = [
    ROUTER,
    NODE,
    ACCESS_POINT,
    MEDIA_BRIDGE,
]

# Defaults
DEFAULT_DEVICE_NAME = "Unknown device"
DEFAULT_HTTP = {NO_SSL: HTTP, SSL: HTTPS}
DEFAULT_VERIFY_SSL = True

# Simplified setup
SIMPLE_SETUP_PARAMETERS = {
    SSL: {
        CONF_PORT: CONF_DEFAULT_PORTS[SSL],
        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        CONF_CERT_PATH: "",
    },
    NO_SSL: {
        CONF_PORT: CONF_DEFAULT_PORTS[NO_SSL],
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

# <-- CONFIGURATION

# CONSTANTS & CONVERTERS -->

CONVERT_SPEED = {
    UnitOfDataRate.BITS_PER_SECOND: 1,
    UnitOfDataRate.KILOBITS_PER_SECOND: 1024,
    UnitOfDataRate.MEGABITS_PER_SECOND: 1048576,
    UnitOfDataRate.GIGABITS_PER_SECOND: 1073741824,
    UnitOfDataRate.BYTES_PER_SECOND: 8,
    UnitOfDataRate.KILOBYTES_PER_SECOND: 8192,
    UnitOfDataRate.MEGABYTES_PER_SECOND: 8388608,
    UnitOfDataRate.GIGABYTES_PER_SECOND: 8589934592,
}
CONVERT_TRAFFIC = {
    UnitOfInformation.BITS: 0.125,
    UnitOfInformation.KILOBITS: 128,
    UnitOfInformation.MEGABITS: 131072,
    UnitOfInformation.GIGABITS: 134217728,
    UnitOfInformation.BYTES: 1,
    UnitOfInformation.KILOBYTES: 1024,
    UnitOfInformation.MEGABYTES: 1048576,
    UnitOfInformation.GIGABYTES: 1073741824,
}

# <-- CONSTANTS & CONVERTERS

# MISC -->

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

# Generate wireless networks
NAME_GWLAN = {}
NAME_WLAN = {}
for i in NUMERIC_WLAN:
    # WLAN
    NAME_WLAN[i] = f"Wireless {CONNECTION_LIST[i]}"
    # Guest WLAN
    for j in NUMERIC_GWLAN:
        NAME_GWLAN[f"{i}.{j}"] = f"Guest {CONNECTION_LIST[i]} {j}"

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
        "device_class": SensorDeviceClass.DATA_SIZE,
        "native_unit_of_measurement": UnitOfInformation.BYTES,
        "suggested_unit_of_measurement": UnitOfInformation.GIGABYTES,
        "suggested_display_precision": 3,
        "entity_registry_enabled_default": True,
    },
    RX_SPEED: {
        NAME: f"{LABEL_RX} {LABEL_SPEED}",
        "icon": "mdi:download-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.DATA_RATE,
        "native_unit_of_measurement": UnitOfDataRate.BITS_PER_SECOND,
        "suggested_unit_of_measurement": UnitOfDataRate.MEGABITS_PER_SECOND,
        "suggested_display_precision": 3,
        "entity_registry_enabled_default": True,
    },
    TX: {
        NAME: f"{LABEL_TX}",
        "icon": "mdi:upload-outline",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "device_class": SensorDeviceClass.DATA_SIZE,
        "native_unit_of_measurement": UnitOfInformation.BYTES,
        "suggested_unit_of_measurement": UnitOfInformation.GIGABYTES,
        "suggested_display_precision": 3,
        "entity_registry_enabled_default": True,
    },
    TX_SPEED: {
        NAME: f"{LABEL_TX} {LABEL_SPEED}",
        "icon": "mdi:upload-network-outline",
        "state_class": SensorStateClass.MEASUREMENT,
        "device_class": SensorDeviceClass.DATA_RATE,
        "native_unit_of_measurement": UnitOfDataRate.BITS_PER_SECOND,
        "suggested_unit_of_measurement": UnitOfDataRate.MEGABITS_PER_SECOND,
        "suggested_display_precision": 3,
        "entity_registry_enabled_default": True,
    },
}

# <-- MISC

# DIAGNOSTICS -->

TO_REDACT: list[str] = [PASSWORD, CONF_UNIQUE_ID, CONF_USERNAME]
TO_REDACT_DEV: list[str] = [ATTR_CONNECTIONS, ATTR_IDENTIFIERS]
TO_REDACT_STATE: list[str] = ["WAN IP"]
TO_REDACT_ATTRS: list[str] = [
    CONF_DEVICES,
    PASSWORD,
    IP,
    SSID,
    LIST,
    "private_key",
    "psk",
]

# <-- DIAGNOSTICS

# SERVICES -->

SERVICE_ALLOWED_ADJUST_GWLAN: dict[str, Callable | None] = {
    "sync_node": converters.safe_int,
    "bw_enabled": converters.safe_int,
    "bw_dl": None,
    "bw_ul": None,
    "expire": None,
    "closed": converters.safe_int,
    "lanaccess": converters.safe_int,
    SSID: None,
}

SERVICE_ALLOWED_ADJUST_WLAN: dict[str, Callable | None] = {
    "closed": converters.safe_int,
    SSID: None,
}

SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS: list[str] = [
    "block",
    "disable",
]

SERVICE_ALLOWED_PORT_FORWARDING_ACTION: list[str] = [
    "remove_ip",
    "remove",
    "set",
]

SERVICE_ALLOWED_PORT_FORWARDING_PROTOCOL: list[str] = [
    "TCP",
    "UDP",
    "BOTH",
]

# <-- SERVICES

# ICONS -->

ICON_CPU = "mdi:cpu-32-bit"
ICON_DEVICES = "mdi:devices"
ICON_DUALWAN = "mdi:call-split"
ICON_ETHERNET_ON = "mdi:ethernet-cable"
ICON_ETHERNET_OFF = "mdi:ethernet-cable-off"
ICON_INTERNET_ACCESS_OFF = "mdi:lock-outline"
ICON_INTERNET_ACCESS_ON = "mdi:lock-open-variant-outline"
ICON_IP = "mdi:ip"
ICON_LIGHT_OFF = "mdi:led-off"
ICON_LIGHT_ON = "mdi:led-on"
ICON_PARENTAL_CONTROL_OFF = "mdi:magnify"
ICON_PARENTAL_CONTROL_ON = "mdi:magnify-expand"
ICON_PORT_FORWARDING_OFF = "mdi:lan-disconnect"
ICON_PORT_FORWARDING_ON = "mdi:lan-connect"
ICON_RAM = "mdi:memory"
ICON_RESTART = "mdi:restart"
ICON_ROUTER = "mdi:router-network"
ICON_SPEEDTEST = "mdi:speedometer"
ICON_TEMPERATURE = "mdi:thermometer"
ICON_UPDATE = "mdi:update"
ICON_USB = "mdi:usb-port"
ICON_VPN_OFF = "mdi:close-network-outline"
ICON_VPN_ON = "mdi:check-network-outline"
ICON_WAN_AGGREGATION = "mdi:call-merge"
ICON_WLAN_OFF = "mdi:wifi-off"
ICON_WLAN_ON = "mdi:wifi"

# <-- ICONS

# SENSORS -->
STATIC_BINARY_SENSORS: list[AREntityDescription] = [
    # Dual WAN
    ARBinarySensorDescription(
        key="dualwan_state",
        key_group="wan",
        name="Dual WAN",
        icon=ICON_DUALWAN,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "dualwan_mode": "mode",
            "dualwan_priority": "priority",
        },
    ),
    # Port status / LAN
    ARBinarySensorDescription(
        key="lan",
        key_group="ports",
        name="Port Status (LAN)",
        icon_on=ICON_ETHERNET_ON,
        icon_off=ICON_ETHERNET_OFF,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "lan_list": "list",
        },
    ),
    # Port status / USB
    ARBinarySensorDescription(
        key="usb",
        key_group="ports",
        name="Port Status (USB)",
        icon=ICON_USB,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "usb_list": "list",
        },
    ),
    # Port status / WAN
    ARBinarySensorDescription(
        key="wan",
        key_group="ports",
        name="Port Status (WAN)",
        icon_on=ICON_ETHERNET_ON,
        icon_off=ICON_ETHERNET_OFF,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "wan_list": "list",
        },
    ),
    # Internet state
    ARBinarySensorDescription(
        key="internet_link",
        key_group="wan",
        name="Internet",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "internet_ip_address": "ip_address",
            "internet_unit": "wan_unit",
        },
    ),
    # WAN Aggregation
    ARBinarySensorDescription(
        key="aggregation_state",
        key_group="wan",
        name="WAN Aggregation",
        icon=ICON_WAN_AGGREGATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "aggregation_ports": "ports",
        },
    ),
]
STATIC_BINARY_SENSORS.extend(
    [
        # WAN state
        ARBinarySensorDescription(
            key=f"{num}_state",
            key_group="wan",
            name=f"WAN{label}",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_link": "link",
                f"{num}_primary": "primary",
            },
        )
        for num, label in zip((0, 1), ("", " (Secondary)"))
    ]
)
STATIC_BUTTONS: list[ARButtonDescription] = [
    ARButtonDescription(
        key="check_update",
        name="Check for updates",
        icon=ICON_UPDATE,
        state=AsusSystem.FIRMWARE_CHECK,
        entity_registry_enabled_default=True,
    ),
    ARButtonDescription(
        key="reboot",
        name="Reboot",
        icon=ICON_RESTART,
        state=AsusSystem.REBOOT,
        device_class=ButtonDeviceClass.RESTART,
        entity_registry_enabled_default=True,
    ),
    ARButtonDescription(
        key="restart_httpd",
        name="Restart HTTP daemon",
        icon=ICON_RESTART,
        state=AsusSystem.RESTART_HTTPD,
        entity_registry_enabled_default=False,
    ),
    ARButtonDescription(
        key="restart_wired",
        name="Restart wired",
        icon=ICON_ETHERNET_ON,
        state=AsusSystem.RESTART_NET,
    ),
    ARButtonDescription(
        key="restart_wireless",
        name="Restart wireless",
        icon=ICON_RESTART,
        state=AsusSystem.RESTART_WIRELESS,
        entity_registry_enabled_default=False,
    ),
]
STATIC_BUTTONS_OPTIONAL: list[ARButtonDescription] = [
    ARButtonDescription(
        key="reboot_aimesh",
        name="Reboot AiMesh",
        icon=ICON_RESTART,
        state=AsusSystem.AIMESH_REBOOT,
        device_class=ButtonDeviceClass.RESTART,
        entity_registry_enabled_default=True,
    ),
    ARButtonDescription(
        key="rebuild_aimesh",
        name="Rebuild AiMesh",
        icon=ICON_DEVICES,
        state=AsusSystem.AIMESH_REBUILD,
        device_class=ButtonDeviceClass.RESTART,
        entity_registry_enabled_default=True,
    ),
    ARButtonDescription(
        key="restart_firewall",
        name="Restart firewall",
        icon=ICON_RESTART,
        state=AsusSystem.RESTART_FIREWALL,
        entity_registry_enabled_default=False,
    ),
    ARButtonDescription(
        key="refresh_clients",
        name="Refresh clients",
        icon=ICON_DEVICES,
        state=AsusSystem.UPDATE_CLIENTS,
        entity_registry_enabled_default=True,
    ),
]
STATIC_LIGHTS: list[AREntityDescription] = [
    ARLightDescription(
        key="state",
        key_group="led",
        name="LED",
        icon_on=ICON_LIGHT_ON,
        icon_off=ICON_LIGHT_OFF,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
]
STATIC_AURA: list[AREntityDescription] = [
    ARLightDescription(
        key="state",
        key_group="aura",
        name="AURA",
        icon_on=ICON_LIGHT_ON,
        icon_off=ICON_LIGHT_OFF,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "brightness": "brightness",
            "rgb_color": "rgb_color",
            "zones": "zones",
        },
    ),
]
STATIC_SENSORS: list[AREntityDescription] = [
    # AiMesh
    ARSensorDescription(
        key="number",
        key_group="aimesh",
        name="AiMesh",
        icon=ICON_DEVICES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "list": "list",
        },
    ),
    # Boottime
    ARSensorDescription(
        key="datetime",
        key_group="boottime",
        name="Boot Time",
        icon=ICON_RESTART,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Connected devices
    ARSensorDescription(
        key="number",
        key_group="devices",
        name="Connected Devices",
        icon=ICON_ROUTER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "devices": "devices",
        },
    ),
    # Connected GuestNetwork devices
    ARSensorDescription(
        key="gn_number",
        key_group="devices",
        name="Connected GuestNetwork Devices",
        icon=ICON_ROUTER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={},
    ),
    # CPU
    ARSensorDescription(
        key="total_usage",
        key_group="cpu",
        name="CPU",
        icon=ICON_CPU,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            f"{num}_usage": f"core_{num}" for num in NUMERIC_CORES
        },
    ),
    # DSL
    ARSensorDescription(
        key="datarate_up",
        key_group=DSL,
        name="DSL Datarate Up",
        icon="mdi:upload-network-outline",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_display_precision=0,
        entity_registry_enabled_default=True,
    ),
    ARSensorDescription(
        key="datarate_down",
        key_group=DSL,
        name="DSL Datarate Down",
        icon="mdi:download-network-outline",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_display_precision=0,
        entity_registry_enabled_default=True,
    ),
    # Latest connected
    ARSensorDescription(
        key="latest_time",
        key_group="devices",
        name="Latest Connected",
        icon=ICON_DEVICES,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "latest": "list",
        },
    ),
    # RAM
    ARSensorDescription(
        key="usage",
        key_group="ram",
        name="RAM",
        icon=ICON_RAM,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "free": "free",
            "total": "total",
            "used": "used",
        },
    ),
    # Speedtest
    ARSensorDescription(
        key="download_bandwidth",
        key_group="speedtest",
        name="Speedtest Download",
        icon=ICON_SPEEDTEST,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "timestamp": "run_time",
            "download_bytes": "downloaded_bytes",
        },
    ),
    ARSensorDescription(
        key="upload_bandwidth",
        key_group="speedtest",
        name="Speedtest Upload",
        icon=ICON_SPEEDTEST,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "timestamp": "run_time",
            "upload_bytes": "uploaded_bytes",
        },
    ),
    ARSensorDescription(
        key="ping_latency",
        key_group="speedtest",
        name="Speedtest Ping",
        icon=ICON_SPEEDTEST,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        suggested_unit_of_measurement=UnitOfTime.MILLISECONDS,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "ping_jitter": "jitter",
            "ping_low": "low",
            "ping_high": "high",
        },
    ),
    # WAN IP
    ARSensorDescription(
        key="ip_address",
        key_group="wan",
        name="WAN IP",
        icon=ICON_IP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "dns": "dns",
            "gateway": "gateway",
            "ip_type": "ip_type",
            "mask": "mask",
            "private_subnet": "private_subnet",
            "xdns": "xdns",
            "xgateway": "xgateway",
            "xip": "xip",
            "xtype": "xip_type",
            "xmask": "xmask",
        },
    ),
]
# Temperature sensors
STATIC_SENSORS.extend(
    [
        ARSensorDescription(
            key=sensor,
            key_group="temperature",
            name=label,
            icon=ICON_TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for sensor, label in LABELS_TEMPERATURE.items()
    ]
)
# Load avg sensors
STATIC_SENSORS.extend(
    [
        ARSensorDescription(
            key=f"load_avg_{sensor}",
            key_group="sysinfo",
            name=label,
            icon=ICON_CPU,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for sensor, label in LABELS_LOAD_AVG.items()
    ]
)
# WAN IPs
STATIC_SENSORS.extend(
    [
        ARSensorDescription(
            key=f"{num}_{extra_key}_ip_address",
            key_group="wan",
            name=f"WAN IP{label}{extra_label}",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_{extra_key}_{key}": attribute
                for key, attribute in SENSORS_WAN.items()
            },
        )
        for extra_key, extra_label in zip(("main", "extra"), ("", " (Extra)"))
        for num, label in zip((0, 1), ("", " (Secondary)"))
    ]
)
STATIC_SWITCHES: list[AREntityDescription] = [
    # Block Internet
    ARSwitchDescription(
        key="block_all",
        key_group="parental_control",
        name="Block Internet",
        icon_on=ICON_INTERNET_ACCESS_OFF,
        state_on=AsusBlockAll.ON,
        icon_off=ICON_INTERNET_ACCESS_ON,
        state_off=AsusBlockAll.OFF,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
    # Parental control
    ARSwitchDescription(
        key="state",
        key_group="parental_control",
        name="Parental control",
        icon_on=ICON_PARENTAL_CONTROL_ON,
        state_on=AsusParentalControl.ON,
        icon_off=ICON_PARENTAL_CONTROL_OFF,
        state_off=AsusParentalControl.OFF,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "list": "list",
        },
    ),
]
STATIC_SWITCHES.extend(
    [
        # OpenVPN clients
        ARSwitchDescription(
            key=f"{num}_state",
            key_group="ovpn_client",
            name=f"OpenVPN Client {num}",
            icon_on=ICON_VPN_ON,
            state_on=AsusOVPNClient.ON,
            state_on_args={"id": num},
            icon_off=ICON_VPN_OFF,
            state_off=AsusOVPNClient.OFF,
            state_off_args={"id": num},
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_{key}": value
                for key, value in SENSORS_OVPN_CLIENT.items()
            },
        )
        for num in range(1, 6)
    ]
)
STATIC_SWITCHES.extend(
    [
        # OpenVPN servers
        ARSwitchDescription(
            key=f"{num}_{STATE}",
            key_group="ovpn_server",
            name=f"OpenVPN Server {num}",
            icon_on=ICON_VPN_ON,
            state_on=AsusOVPNServer.ON,
            state_on_args={"id": num},
            icon_off=ICON_VPN_OFF,
            state_off=AsusOVPNServer.OFF,
            state_off_args={"id": num},
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_{key}": value
                for key, value in SENSORS_OVPN_SERVER.items()
            },
        )
        for num in NUMERIC_OVPN_SERVER
    ]
)
STATIC_SWITCHES.extend(
    [
        # WireGuard clients
        ARSwitchDescription(
            key=f"{num}_state",
            key_group="wireguard_client",
            name=f"WireGuard Client {num}",
            icon_on=ICON_VPN_ON,
            state_on=AsusWireGuardClient.ON,
            state_on_args={"id": num},
            icon_off=ICON_VPN_OFF,
            state_off=AsusWireGuardClient.OFF,
            state_off_args={"id": num},
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_{key}": value
                for key, value in SENSORS_WIREGUARD_CLIENT.items()
            },
        )
        for num in range(1, 6)
    ]
)
STATIC_SWITCHES.extend(
    [
        # WireGuard Server
        ARSwitchDescription(
            key=f"{num}_state",
            key_group="wireguard_server",
            name=f"WireGuard Server {num}",
            icon_on=ICON_VPN_ON,
            state_on=AsusWireGuardServer.ON,
            state_on_args={"id": num},
            icon_off=ICON_VPN_OFF,
            state_off=AsusWireGuardServer.OFF,
            state_off_args={"id": num},
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{num}_{key}": value
                for key, value in SENSORS_WIREGUARD_SERVER.items()
            },
        )
        for num in range(1, 2)
    ]
)
STATIC_SWITCHES.extend(
    [
        # WLANs
        ARSwitchDescription(
            key=f"{wlan}_radio",
            key_group="wlan",
            name=f"Wireless {LABELS_WLAN[wlan]}",
            icon_on=ICON_WLAN_ON,
            state_on=AsusWLAN.ON,
            state_on_args={
                API_ID: wlan_id,
                API_TYPE: "wlan",
            },
            icon_off=ICON_WLAN_OFF,
            state_off=AsusWLAN.OFF,
            state_off_args={
                API_ID: wlan_id,
                API_TYPE: "wlan",
            },
            state_expect_modify=True,
            device_class="wlan",
            capabilities={
                API_TYPE: "wlan",
                API_ID: wlan_id,
            },
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{wlan}_{key}": value for key, value in SENSORS_WLAN.items()
            },
        )
        for wlan, wlan_id in MAP_WLAN.items()
    ]
)
STATIC_SWITCHES.extend(
    [
        # Guest WLANs
        ARSwitchDescription(
            key=f"{wlan}_{gwlan}_bss_enabled",
            key_group="gwlan",
            name=f"Guest {LABELS_WLAN[wlan]} {gwlan}",
            icon_on=ICON_WLAN_ON,
            state_on=AsusWLAN.ON,
            state_on_args={
                API_ID: f"{wlan_id}.{gwlan}",
                API_TYPE: "gwlan",
            },
            icon_off=ICON_WLAN_OFF,
            state_off=AsusWLAN.OFF,
            state_off_args={
                API_ID: f"{wlan_id}.{gwlan}",
                API_TYPE: "gwlan",
            },
            state_expect_modify=True,
            device_class="wlan",
            capabilities={
                API_TYPE: "gwlan",
                API_ID: f"{wlan_id}.{gwlan}",
            },
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{wlan}_{gwlan}_{key}": value
                for key, value in SENSORS_GWLAN.items()
            },
        )
        for gwlan in NUMERIC_GWLAN
        for wlan, wlan_id in MAP_WLAN.items()
    ]
)
STATIC_SWITCHES.extend(
    [
        # Port forwarding
        ARSwitchDescription(
            key="state",
            key_group="port_forwarding",
            name="Port forwarding",
            icon_on=ICON_PORT_FORWARDING_ON,
            state_on=AsusPortForwarding.ON,
            icon_off=ICON_PORT_FORWARDING_OFF,
            state_off=AsusPortForwarding.OFF,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                "list": "list",
            },
        )
    ]
)
STATIC_UPDATES: list[AREntityDescription] = [
    ARUpdateDescription(
        key="state",
        key_group="firmware",
        name="Firmware update",
        icon=ICON_UPDATE,
        device_class=UpdateDeviceClass.FIRMWARE,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "current": "current",
            "latest": "latest",
            "release_note": "release_note",
        },
    ),
    ARUpdateDescription(
        key="state_beta",
        key_group="firmware",
        name="Firmware update (Beta)",
        icon=ICON_UPDATE,
        device_class=UpdateDeviceClass.FIRMWARE,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "current": "current",
            "latest_beta": "latest",
            "release_note": "release_note",
        },
    ),
]

# <-- SENSORS

# CONSTANTS BY MODULE -->

# __init__ constants
STOP_LISTENER = "stop_listener"

# Configuration flow
BASE = "base"
CONFIGS = "configs"
ERRORS = "errors"
INTERFACES = "interfaces"

RESULT_ACCESS_ERROR = "access_error"
RESULT_CANNOT_RESOLVE = "cannot_resolve"
RESULT_CONNECTION_ERROR = "connection_error"
RESULT_CONNECTION_REFUSED = "connection_refused"
RESULT_ERROR = "error"
RESULT_LOGIN_BLOCKED = "login_blocked"
RESULT_SUCCESS = "success"
RESULT_TIMEOUT = "timeout"
RESULT_UNKNOWN = "unknown"
RESULT_WRONG_CREDENTIALS = "wrong_credentials"

STEP_CONNECTED_DEVICES = "connected_devices"
STEP_CREDENTIALS = "credentials"
STEP_EVENTS = "events"
STEP_FIND = "find"
STEP_FINISH = "finish"
STEP_INTERFACES = "interfaces"
STEP_INTERVALS = "intervals"
STEP_NAME = "name"
STEP_OPERATION = "operation"
STEP_OPTIONS = "options"
STEP_SECURITY = "security"
