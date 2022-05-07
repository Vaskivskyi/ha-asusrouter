"""Migrate between versions module for AsusRouter integration"""

from __future__ import annotations

from homeassistant.const import (
    CONF_SSL,
)

# Deprecated values
CONF_USE_SSL = "use_ssl"

# Values to replace from to
DEPRECATED : dict[dict[str, str]] = dict()
DEPRECATED["1_2"] = {
    CONF_USE_SSL: CONF_SSL,
}
