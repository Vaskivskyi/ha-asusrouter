"""AsusRouter constants module."""

from __future__ import annotations

# INTEGRATION DATA -->

ASUSROUTER = "asusrouter"
DOMAIN = ASUSROUTER

# Connection settings live in the entry data, options are unused
ENTRY_VERSION = 6

# <-- INTEGRATION DATA

# CONFIGURATION CONSTANTS & DEFAULTS -->

# The library picks the port matching the SSL setting when none is given
CONF_DEFAULT_PORT = 0
CONF_DEFAULT_SSL = True
CONF_DEFAULT_USERNAME = "admin"

DEFAULT_IDENTITY_NAME = "AsusRouter"

# <-- CONFIGURATION

# CONSTANTS BY MODULE -->

# Configuration flow
BASE = "base"

RESULT_ACCESS_ERROR = "access_error"
RESULT_CANNOT_RESOLVE = "cannot_resolve"
RESULT_CONNECTION_ERROR = "connection_error"
RESULT_ERROR = "error"
RESULT_LOGIN_BLOCKED = "login_blocked"
RESULT_TIMEOUT = "timeout"
RESULT_UNKNOWN = "unknown"
RESULT_WRONG_CREDENTIALS = "wrong_credentials"

STEP_CREDENTIALS = "credentials"
STEP_FIND = "find"
STEP_RECONFIGURE = "reconfigure"

# <-- CONSTANTS BY MODULE
