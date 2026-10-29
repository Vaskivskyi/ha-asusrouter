"""AsusRouter helpers module."""

from __future__ import annotations

import re
from typing import Any

from asusrouter.tools.identifiers import MacAddress
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN


def to_identifier(mac: MacAddress) -> tuple[str, str]:
    """Convert a MAC to a device identifier."""

    return (DOMAIN, format_mac(str(mac)))


def to_str(value: Any) -> str | None:
    """Convert a value to string, None when missing."""

    return None if value is None else str(value)


def to_unique_id(raw: str) -> str:
    """Convert string to unique_id."""

    # Frozen: changing the output orphans every existing entity
    string = (
        re.sub(r"(?<=[a-z0-9:_])(?=[A-Z])|[^a-zA-Z0-9:_]", " ", raw)
        .strip()
        .replace(" ", "_")
    )
    result = string.lower()
    while "__" in result:
        result = result.replace("__", "_")

    return result
