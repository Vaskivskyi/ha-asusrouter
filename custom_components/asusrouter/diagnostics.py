"""AsusRouter diagnostics module."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any

from asusrouter.tools.security import REDACTED, ARSensitive
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import ARConfigEntry

# Entry data identifying the user or the device
TO_REDACT_ENTRY = {
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    "title",
    "unique_id",
}
# Free text of the device data, which the library cannot mask
TO_REDACT_DATA = {
    "name",
    "password",
    "private_key",
    "public_key",
    "serial",
    "ssid",
    "ssid_fh",
    "ssid_parent",
    "username",
}


def _to_scalar(value: Any) -> Any:
    """Convert a value without items to plain data."""

    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()

    return str(value)


def _to_plain(value: Any) -> Any:
    """Convert a value to plain data, masking every identifier."""

    # An identifier that cannot be masked, like an SSID, is redacted
    if isinstance(value, ARSensitive):
        return _to_scalar(value.mask() if value.maskable else REDACTED)
    # A number member reads better by its name
    if isinstance(value, Enum):
        return value.value if isinstance(value, str) else value.name.lower()
    if isinstance(value, dict):
        return {
            str(_to_plain(key)): _to_plain(item) for key, item in value.items()
        }
    if isinstance(value, list | tuple | set | frozenset):
        return [_to_plain(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_plain(getattr(value, field.name))
            for field in fields(value)
        }

    return _to_scalar(value)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ARConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of a config entry."""

    runtime_data = config_entry.runtime_data
    identity = runtime_data.bridge.identity

    return {
        "entry": async_redact_data(config_entry.as_dict(), TO_REDACT_ENTRY),
        "device": {
            "brand": identity.brand,
            "firmware": str(identity.firmware),
            "model": identity.model,
            "model_original": identity.model_original,
            "operation_mode": _to_plain(identity.operation_mode),
            "support": _to_plain(identity.support),
            "wifi": _to_plain(identity.wifi),
        },
        "nodes": len(runtime_data.nodes),
        "sources": [
            {
                "source": type(source).__name__,
                "last_update_success": coordinator.last_update_success,
                "data": async_redact_data(
                    _to_plain(coordinator.data), TO_REDACT_DATA
                ),
            }
            for source, coordinator in runtime_data.coordinators.items()
        ],
    }
