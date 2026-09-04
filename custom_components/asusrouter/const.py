"""AsusRouter constants module."""

from __future__ import annotations

# INTEGRATION DATA -->

ASUSROUTER = "asusrouter"
DOMAIN = ASUSROUTER

# <-- INTEGRATION DATA

# GENERAL DATA -->

ACCESS_POINT = "access_point"
CPU = "cpu"
FIRMWARE = "firmware"
GWLAN = "gwlan"
LIGHT = "light"
MEDIA_BRIDGE = "media_bridge"
METHOD = "method"
MISC = "misc"
NETWORK = "network"
NEXT = "next"
NODE = "node"
PARENTAL_CONTROL = "parental_control"
PORTS = "ports"
RAM = "ram"
ROUTER = "router"
SYSINFO = "sysinfo"
TEMPERATURE = "temperature"
UNIQUE_ID = "unique_id"
VPN = "vpn"
WAN = "wan"
WLAN = "wlan"

# <-- GENERAL DATA

# CONFIGURATION CONSTANTS & DEFAULTS -->

# Keys
CONF_CACHE_TIME = "cache_time"
CONF_EVENT_DEVICE_CONNECTED = "device_connected"
CONF_EVENT_DEVICE_DISCONNECTED = "device_disconnected"
CONF_EVENT_DEVICE_RECONNECTED = "device_reconnected"
CONF_EVENT_NODE_CONNECTED = "node_connected"
CONF_EVENT_NODE_DISCONNECTED = "node_disconnected"
CONF_EVENT_NODE_RECONNECTED = "node_reconnected"
CONF_HIDE_PASSWORDS = "hide_passwords"
CONF_INTERVAL = "interval_"
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
CONF_MODE = "mode"
CONF_SPLIT_INTERVALS = "split_intervals"

# Defaults
CONF_DEFAULT_CACHE_TIME = 5
CONF_DEFAULT_EVENT: dict[str, bool] = {
    CONF_EVENT_DEVICE_CONNECTED: True,
    CONF_EVENT_DEVICE_DISCONNECTED: False,
    CONF_EVENT_DEVICE_RECONNECTED: False,
    CONF_EVENT_NODE_CONNECTED: True,
    CONF_EVENT_NODE_DISCONNECTED: True,
    CONF_EVENT_NODE_RECONNECTED: True,
}
CONF_DEFAULT_HIDE_PASSWORDS = False
CONF_DEFAULT_INTERVALS = {CONF_INTERVAL + FIRMWARE: 600}
CONF_DEFAULT_MODE = ROUTER
CONF_DEFAULT_PORT = 0
CONF_DEFAULT_SCAN_INTERVAL = 30
CONF_DEFAULT_SPLIT_INTERVALS = False
CONF_DEFAULT_SSL = True
CONF_DEFAULT_USERNAME = "admin"

# Labels
CONF_LABELS_MODE = {
    ROUTER: "Router",
    NODE: "AiMesh node",
    ACCESS_POINT: "Access Point",
    MEDIA_BRIDGE: "Media bridge",
}

# Defaults
DEFAULT_IDENTITY_NAME = "AsusRouter"

# Input values
CONF_VALUES_MODE = [
    ROUTER,
    NODE,
    ACCESS_POINT,
    MEDIA_BRIDGE,
]

# <-- CONFIGURATION

# CONSTANTS BY MODULE -->

# __init__ constants
STOP_LISTENER = "stop_listener"

# Configuration flow
BASE = "base"
CONFIGS = "configs"
ERRORS = "errors"

RESULT_ACCESS_ERROR = "access_error"
RESULT_CANNOT_RESOLVE = "cannot_resolve"
RESULT_CONNECTION_ERROR = "connection_error"
RESULT_ERROR = "error"
RESULT_LOGIN_BLOCKED = "login_blocked"
RESULT_SUCCESS = "success"
RESULT_TIMEOUT = "timeout"
RESULT_UNKNOWN = "unknown"
RESULT_WRONG_CREDENTIALS = "wrong_credentials"

STEP_CREDENTIALS = "credentials"
STEP_EVENTS = "events"
STEP_FIND = "find"
STEP_FINISH = "finish"
STEP_INTERVALS = "intervals"
STEP_OPERATION = "operation"
STEP_OPTIONS = "options"
STEP_SECURITY = "security"

# <-- CONSTANTS BY MODULE
