"""AsusRouter constants"""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    DEVICE_CLASS_CONNECTIVITY,
)
from homeassistant.components.button import ButtonDeviceClass
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
    PERCENTAGE,
    Platform,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from asusrouter.util import converters

from .dataclass import (
    ARBinarySensorDescription,
    ARButtonDescription,
    ARLightDescription,
    ARSensorDescription,
    ARSwitchDescription,
    ARUpdateDescription,
)

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
NUMERIC_GWLAN = range(1, 4)  # maximum of 4 guest WLANs from 1 to 3
NUMERIC_LAN = range(1, 9)  # maximum of 8 LAN ports from 1 to 8
NUMERIC_OVPN_CLIENT = range(1, 6)  # maximum of 5 OVPN clients from 1 to 5
NUMERIC_OVPN_SERVER = range(1, 3)  # maximum of 2 OVPN servers from 1 to 2
NUMERIC_WAN = range(0, 4)  # maximum of 4 WAN ports from 0 to 3
NUMERIC_WLAN = range(0, 4)  # maximum of 4 WLANs from 0 to 3

### <-- NUMERIC

### GENERAL DATA -->

ACTION_MODE = "action_mode"
API_ID = "api_id"
API_TYPE = "api_type"
APPLY = "apply"
BITS_PER_SECOND = "bits/s"
BOOTTIME = "boottime"
BYTES = "bytes"
CORE = "core"
CPU = "cpu"
DEVICES = "devices"
DNS = "dns"
FIRMWARE = "firmware"
FREE = "free"
GWLAN = "gwlan"
HTTP = "http"
HTTPS = "https"
IP = "ip"
LAN = "lan"
LED = "led"
LIGHT = "light"
LIST = "list"
LOAD_AVG = "load_avg"
MAC = "mac"
MISC = "misc"
NAME = "name"
NETWORK_STAT = "network_stat"
NO_SSL = "no_ssl"
PARENTAL_CONTROL = "parental_control"
PASSWORD = "password"
PORTS = "ports"
RAM = "ram"
RX = "rx"
RX_SPEED = "rx_speed"
SSID = "ssid"
SSL = "ssl"
STATE = "state"
STATUS = "status"
SYSINFO = "sysinfo"
TEMPERATURE = "temperature"
TOTAL = "total"
TX = "tx"
TX_SPEED = "tx_speed"
UNKNOWN = "unknown"
USAGE = "usage"
USED = "used"
VPN = "vpn"
WAN = "wan"
WLAN = "wlan"
WLAN_2GHZ = "2ghz"
WLAN_5GHZ = "5ghz"
WLAN_5GHZ2 = "5ghz2"
WLAN_6GHZ = "6ghz"

### <-- GENERAL DATA

### GENERAL STATES -->

CONNECTED = "connected"

### <-- GENERAL STATES

### LABELS -->

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
LABEL_OVPN_CLIENT = "OpenVPN Client"
LABEL_OVPN_SERVER = "OpenVPN Server"
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

### SENSORS LIST -->

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
SENSORS_LIGHT = [LED]
SENSORS_MISC = [BOOTTIME]
SENSORS_NETWORK_STAT = [RX, RX_SPEED, TX, TX_SPEED]
SENSORS_PARENTAL_CONTROL = [STATE]
SENSORS_PORTS = [LAN.upper(), WAN.upper()]
SENSORS_RAM = [FREE, TOTAL, USAGE, USED]
SENSORS_SYSINFO = [f"{LOAD_AVG}_{sensor}" for sensor in LABELS_LOAD_AVG]
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
    STATUS: STATUS,
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
SENSORS_WAN = [STATUS, IP, "ip_type", "gateway", "mask", "dns", "private_subnet"]
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
DEFAULT_HTTP = {NO_SSL: HTTP, SSL: HTTPS}
DELAULT_INTERFACES = [WAN.upper()]
DEFAULT_INTERVALS = {CONF_INTERVAL + FIRMWARE: 21600}
DEFAULT_LATEST_CONNECTED = 5
DEFAULT_PORT = 0
DEFAULT_PORTS = {NO_SSL: 80, SSL: 8443}
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
    SSL: {
        CONF_PORT: DEFAULT_PORTS[SSL],
        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        CONF_CERT_PATH: "",
    },
    NO_SSL: {
        CONF_PORT: DEFAULT_PORTS[NO_SSL],
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
TO_REDACT_ATTRS = {CONF_DEVICES, PASSWORD, IP, SSID, LIST}

### <-- DIAGNOSTICS

### SERVICES -->

REBOOT = "reboot"
RESTART_FIREWALL = "restart_firewall"
RESTART_HTTPD = "restart_httpd"
RESTART_WIRELESS = "restart_wireless"
START_VPNCLIENT = "start_vpnclient"
STOP_VPNCLIENT = "stop_vpnclient"
START_VPNSERVER = "start_vpnserver"
STOP_VPNSERVER = "stop_vpnserver"

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

### ICONS -->

ICON_CPU = "mdi:cpu-32-bit"
ICON_DEVICES = "mdi:devices"
ICON_ETHERNET = "mdi:ethernet-cable"
ICON_IP = "mdi:ip"
ICON_LIGHT_OFF = "mdi:led-off"
ICON_LIGHT_ON = "mdi:led-on"
ICON_PARENTAL_CONTROL_OFF = "mdi:magnify"
ICON_PARENTAL_CONTROL_ON = "mdi:magnify-expand"
ICON_RAM = "mdi:memory"
ICON_RESTART = "mdi:restart"
ICON_ROUTER = "mdi:router-network"
ICON_TEMPERATURE = "mdi:thermometer"
ICON_UPDATE = "mdi:update"
ICON_VPN_OFF = "mdi:close-network-outline"
ICON_VPN_ON = "mdi:check-network-outline"
ICON_WLAN_OFF = "mdi:wifi-off"
ICON_WLAN_ON = "mdi:wifi"

### <-- ICONS

### SENSORS -->
STATIC_BINARY_SENSORS = {
    # WAN state
    (WAN, STATUS): ARBinarySensorDescription(
        key=STATUS,
        key_group=WAN,
        name=WAN.upper(),
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            DNS: DNS,
            "gateway": "gateway",
            IP: IP,
            "ip_type": "ip_type",
            "mask": "mask",
            "private_subnet": "private_subnet",
        },
    ),
}
STATIC_BINARY_SENSORS_OPTIONAL = {
    # Parental control state
    (PARENTAL_CONTROL, STATE): ARBinarySensorDescription(
        key=STATE,
        key_group=PARENTAL_CONTROL,
        name="Parental control",
        icon_off=ICON_PARENTAL_CONTROL_OFF,
        icon_on=ICON_PARENTAL_CONTROL_ON,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            LIST: LIST,
        },
    ),
}
STATIC_BINARY_SENSORS_OPTIONAL.update(
    {
        # OVPN clients
        (VPN, f"{KEY_OVPN_CLIENT}{num}_{STATE}"): ARBinarySensorDescription(
            key=f"{KEY_OVPN_CLIENT}{num}_{STATE}",
            key_group=VPN,
            name=f"{LABEL_OVPN_CLIENT} {num}",
            device_class=DEVICE_CLASS_CONNECTIVITY,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{KEY_OVPN_CLIENT}{num}_{key}": SENSORS_VPN[key] for key in SENSORS_VPN
            },
        )
        for num in NUMERIC_OVPN_CLIENT
    }
)
STATIC_BINARY_SENSORS_OPTIONAL.update(
    {
        # OVPN servers
        (VPN, f"{KEY_OVPN_SERVER}{num}_{STATE}"): ARBinarySensorDescription(
            key=f"{KEY_OVPN_SERVER}{num}_{STATE}",
            key_group=VPN,
            name=f"{LABEL_OVPN_SERVER} {num}",
            device_class=DEVICE_CLASS_CONNECTIVITY,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{KEY_OVPN_SERVER}{num}_{key}": SENSORS_VPN_SERVER[key]
                for key in SENSORS_VPN_SERVER
            },
        )
        for num in NUMERIC_OVPN_SERVER
    }
)
STATIC_BINARY_SENSORS_OPTIONAL.update(
    {
        # WLANs
        (WLAN, f"{KEY_WLAN}{num}_radio"): ARBinarySensorDescription(
            key=f"{KEY_WLAN}{num}_radio",
            key_group=WLAN,
            name=f"{NAME_WLAN[num]}",
            device_class=DEVICE_CLASS_CONNECTIVITY,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_WLAN}{num}_{key}": SENSORS_WLAN[key] for key in SENSORS_WLAN
            },
        )
        for num in NUMERIC_WLAN
    }
)
STATIC_BINARY_SENSORS_OPTIONAL.update(
    {
        # Guest WLANs
        (GWLAN, f"{KEY_GWLAN}{num}.{gnum}_bss_enabled",): ARBinarySensorDescription(
            key=f"{KEY_GWLAN}{num}.{gnum}_bss_enabled",
            key_group=GWLAN,
            name=NAME_GWLAN[f"{num}.{gnum}"],
            device_class=DEVICE_CLASS_CONNECTIVITY,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_GWLAN}{num}.{gnum}_{key}": SENSORS_GWLAN[key]
                for key in SENSORS_GWLAN
            },
        )
        for gnum in NUMERIC_GWLAN
        for num in NUMERIC_WLAN
    }
)
STATIC_BUTTONS = {
    REBOOT: ARButtonDescription(
        key=REBOOT,
        name="Reboot",
        icon=ICON_RESTART,
        service=REBOOT,
        service_args={},
        device_class=ButtonDeviceClass.RESTART,
        service_expect_modify=False,
        entity_registry_enabled_default=True,
    ),
    RESTART_FIREWALL: ARButtonDescription(
        key=RESTART_FIREWALL,
        name="Restart firewall",
        icon=ICON_RESTART,
        service=RESTART_FIREWALL,
        service_args={},
        service_expect_modify=False,
        entity_registry_enabled_default=False,
    ),
    RESTART_HTTPD: ARButtonDescription(
        key=RESTART_HTTPD,
        name="Restart HTTP daemon",
        icon=ICON_RESTART,
        service=RESTART_HTTPD,
        service_args={},
        service_expect_modify=False,
        entity_registry_enabled_default=False,
    ),
    RESTART_WIRELESS: ARButtonDescription(
        key=RESTART_WIRELESS,
        name="Restart wireless",
        icon=ICON_RESTART,
        service=RESTART_WIRELESS,
        service_args={},
        service_expect_modify=False,
        entity_registry_enabled_default=False,
    ),
}
STATIC_LIGHTS = {
    (LIGHT, LED): ARLightDescription(
        key=LED,
        key_group=LIGHT,
        name="LED",
        icon_off=ICON_LIGHT_OFF,
        icon_on=ICON_LIGHT_ON,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
}
STATIC_SENSORS = {
    # Boot time
    (MISC, BOOTTIME): ARSensorDescription(
        key=BOOTTIME,
        key_group=MISC,
        name="Boot Time",
        icon=ICON_RESTART,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Connected devices
    (DEVICES, "number"): ARSensorDescription(
        key="number",
        key_group=DEVICES,
        name="Connected Devices",
        icon=ICON_ROUTER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            DEVICES: DEVICES,
        },
    ),
    # CPU
    (CPU, TOTAL): ARSensorDescription(
        key=TOTAL,
        key_group=CPU,
        name=CPU.upper(),
        icon=ICON_CPU,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            f"{CORE}_{num}": f"{CORE}_{num}" for num in NUMERIC_CORES
        },
    ),
    # LAN
    (PORTS, "LAN_total"): ARSensorDescription(
        key="LAN_total",
        key_group=PORTS,
        name="LAN Speed",
        icon=ICON_ETHERNET,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_RATE_MEGABITS_PER_SECOND,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            f"{LAN.upper()}_{num}": f"{LAN}_{num}" for num in NUMERIC_LAN
        },
    ),
    # Latest connected
    (DEVICES, "latest_time"): ARSensorDescription(
        key="latest_time",
        key_group=DEVICES,
        name="Latest Connected",
        icon=ICON_DEVICES,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "latest": LIST,
        },
    ),
    # RAM
    (RAM, USAGE): ARSensorDescription(
        key=USAGE,
        key_group=RAM,
        name=RAM.upper(),
        icon=ICON_RAM,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=2,
        extra_state_attributes={
            FREE: FREE,
            TOTAL: TOTAL,
            USED: USED,
        },
    ),
    # WAN
    (PORTS, "WAN_total"): ARSensorDescription(
        key="WAN_total",
        key_group=PORTS,
        name="WAN Speed",
        icon=ICON_ETHERNET,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_RATE_MEGABITS_PER_SECOND,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            f"{WAN.upper()}_{num}": f"{WAN}_{num}" for num in NUMERIC_WAN
        },
    ),
    # WAN IP
    (WAN, IP): ARSensorDescription(
        key=IP,
        key_group=WAN,
        name="WAN IP",
        icon=ICON_IP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            DNS: DNS,
            "gateway": "gateway",
            "ip_type": "ip_type",
            "mask": "mask",
            "private_subnet": "private_subnet",
        },
    ),
}
# Temperature sensors
STATIC_SENSORS.update(
    {
        (TEMPERATURE, sensor): ARSensorDescription(
            key=sensor,
            key_group=TEMPERATURE,
            name=LABELS_TEMPERATURE[sensor],
            icon=ICON_TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for sensor in LABELS_TEMPERATURE
    }
)
# Load avg sensors
STATIC_SENSORS.update(
    {
        (SYSINFO, f"{LOAD_AVG}_{sensor}"): ARSensorDescription(
            key=f"{LOAD_AVG}_{sensor}",
            key_group=SYSINFO,
            name=LABELS_LOAD_AVG[sensor],
            icon=ICON_CPU,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for sensor in LABELS_LOAD_AVG
    }
)
STATIC_SWITCHES = {}
STATIC_SWITCHES_OPTIONAL = {
    (PARENTAL_CONTROL, STATE): ARSwitchDescription(
        key=STATE,
        key_group=PARENTAL_CONTROL,
        name="Parental control",
        icon_on=ICON_PARENTAL_CONTROL_ON,
        icon_off=ICON_PARENTAL_CONTROL_OFF,
        service_off=RESTART_FIREWALL,
        service_off_args={
            ACTION_MODE: APPLY,
            "MULTIFILTER_ALL": 0,
        },
        service_on=RESTART_FIREWALL,
        service_on_args={
            ACTION_MODE: APPLY,
            "MULTIFILTER_ALL": 1,
        },
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            LIST: LIST,
        },
    ),
}
STATIC_SWITCHES_OPTIONAL.update(
    {
        # OVPN clients
        (VPN, f"{KEY_OVPN_CLIENT}{num}_{STATE}"): ARSwitchDescription(
            key=f"{KEY_OVPN_CLIENT}{num}_{STATE}",
            key_group=VPN,
            name=f"{LABEL_OVPN_CLIENT} {num}",
            icon_on=ICON_VPN_ON,
            icon_off=ICON_VPN_OFF,
            service_on=f"{START_VPNCLIENT}{num}",
            service_off=f"{STOP_VPNCLIENT}{num}",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_OVPN_CLIENT}{num}_{key}": SENSORS_VPN[key] for key in SENSORS_VPN
            },
        )
        for num in NUMERIC_OVPN_CLIENT
    }
)
STATIC_SWITCHES_OPTIONAL.update(
    {
        # OVPN servers
        (VPN, f"{KEY_OVPN_SERVER}{num}_{STATE}"): ARSwitchDescription(
            key=f"{KEY_OVPN_SERVER}{num}_{STATE}",
            key_group=VPN,
            name=f"{LABEL_OVPN_SERVER} {num}",
            icon_on=ICON_VPN_ON,
            icon_off=ICON_VPN_OFF,
            service_on=f"{START_VPNSERVER}{num}",
            service_off=f"{STOP_VPNSERVER}{num}",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_OVPN_SERVER}{num}_{key}": SENSORS_VPN_SERVER[key]
                for key in SENSORS_VPN_SERVER
            },
        )
        for num in NUMERIC_OVPN_SERVER
    }
)
STATIC_SWITCHES_OPTIONAL.update(
    {
        # WLANs
        (WLAN, f"{KEY_WLAN}{num}_radio"): ARSwitchDescription(
            key=f"{KEY_WLAN}{num}_radio",
            key_group=WLAN,
            name=f"{NAME_WLAN[num]}",
            icon_on=ICON_WLAN_ON,
            icon_off=ICON_WLAN_OFF,
            service_on=RESTART_WIRELESS,
            service_on_args={
                ACTION_MODE: APPLY,
                f"wl{num}_radio": 1,
            },
            service_off=RESTART_WIRELESS,
            service_off_args={
                ACTION_MODE: APPLY,
                f"wl{num}_radio": 0,
            },
            device_class=WLAN,
            capabilities={
                API_TYPE: WLAN,
                API_ID: num,
            },
            service_expect_modify=True,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_WLAN}{num}_{key}": SENSORS_WLAN[key] for key in SENSORS_WLAN
            },
        )
        for num in NUMERIC_WLAN
    }
)
STATIC_SWITCHES_OPTIONAL.update(
    {
        # Guest WLANs
        (GWLAN, f"{KEY_GWLAN}{num}.{gnum}_bss_enabled"): ARSwitchDescription(
            key=f"{KEY_GWLAN}{num}.{gnum}_bss_enabled",
            key_group=GWLAN,
            name=NAME_GWLAN[f"{num}.{gnum}"],
            icon_on=ICON_WLAN_ON,
            icon_off=ICON_WLAN_OFF,
            service_on=f"{RESTART_WIRELESS};{RESTART_FIREWALL}",
            service_on_args={
                ACTION_MODE: APPLY,
                f"wl{num}.{gnum}_bss_enabled": 1,
                f"wl{num}.{gnum}_expire": 0,
            },
            service_off=f"{RESTART_WIRELESS};{RESTART_FIREWALL}",
            service_off_args={
                ACTION_MODE: APPLY,
                f"wl{num}.{gnum}_bss_enabled": 0,
            },
            device_class=WLAN,
            capabilities={
                API_TYPE: GWLAN,
                API_ID: f"{num}.{gnum}",
            },
            service_expect_modify=True,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=True,
            extra_state_attributes={
                f"{KEY_GWLAN}{num}.{gnum}_{key}": SENSORS_GWLAN[key]
                for key in SENSORS_GWLAN
            },
        )
        for gnum in NUMERIC_GWLAN
        for num in NUMERIC_WLAN
    }
)
STATIC_UPDATES = {
    (FIRMWARE, STATE): ARUpdateDescription(
        key=STATE,
        key_group=FIRMWARE,
        name="Firmware update",
        icon=ICON_UPDATE,
        extra_state_attributes={
            "current": "current",
            "available": "available",
        },
    )
}

### <-- SENSORS
