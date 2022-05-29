"""Migrate between versions module for AsusRouter integration."""

from __future__ import annotations

from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

from .const import CONF_CERT_PATH, CONF_ENABLE_CONTROL, CONF_ENABLE_MONITOR

# Deprecated values
CONF_USE_SSL = "use_ssl"

# Values to replace from to
DEPRECATED: dict[dict[str, str]] = dict()
DEPRECATED["1_2"] = {
    CONF_USE_SSL: CONF_SSL,
}
MOVE_TO_OPTIONS: dict[list[str]] = dict()
MOVE_TO_OPTIONS["2_3"] = [
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
    CONF_CERT_PATH,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
]
