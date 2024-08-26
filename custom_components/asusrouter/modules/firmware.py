"""Firmware module for AsusRouter integration."""

from __future__ import annotations

from typing import Any, Optional


def to_ha(data: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Convert AsusRouter firmware data to Home Assistant format."""

    if not data:
        return {}

    # Current firmware
    _current = data.get("current")
    _current = str(_current) if _current else None

    # Available stable firmware
    _latest = data.get("available")
    _latest = str(_latest) if _latest else _current

    # Available beta firmware
    _latest_beta = data.get("available_beta")
    _latest_beta = str(_latest_beta) if _latest_beta else _current

    return {
        "current": _current,
        "latest": _latest,
        "latest_beta": _latest_beta,
        "release_note": data.get("release_note"),
    }
