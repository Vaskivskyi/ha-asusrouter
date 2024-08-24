"""Aura RGB module for AsusRouter integration.

This module allows converting AsusRouter Aura data to the
Home Assistant format. This is required due to the complex
data structure and effect handling by Home Assistant.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode
from homeassistant.const import EntityCategory

from asusrouter.modules.color import ColorRGBB
from asusrouter.tools.converters import scale_value_int

from ..const import ICON_LIGHT_OFF, ICON_LIGHT_ON
from ..dataclass import AREntityDescription, ARLightDescription

AURA_NO_EFFECT = "EFFECT_OFF"
AURA_FALLBACK_BRIGHTNESS = 128
AURA_FALLBACK_COLOR = ColorRGBB(
    (128, 128, 128),
    AURA_FALLBACK_BRIGHTNESS,
    scale=128,
)

AURA_EFFECTS = [
    "Gradient",
    "Static",
    "Breathing",
    "Evolution",
    "Rainbow",
    "Wave",
    "Marquee",
]

AURA_EFFECTS_MAP = {
    0: AURA_NO_EFFECT,
    1: "Gradient",
    2: "Static",
    3: "Breathing",
    4: "Evolution",
    5: "Rainbow",
    6: "Wave",
    7: "Marquee",
}

SUPPORTED_COLOR_MODES = {
    0: ColorMode.ONOFF,
    1: ColorMode.RGB,
    2: ColorMode.RGB,
    3: ColorMode.RGB,
    4: ColorMode.ONOFF,
    5: ColorMode.ONOFF,
    6: ColorMode.ONOFF,
    7: ColorMode.RGB,
}

ACTIVE_BRIGHTNESS = "active_brightness"
ACTIVE_COLOR = "active_color"
BRIGHTNESS = "brightness"
RGB_COLOR = "rgb_color"
SCHEME = "scheme"
STATE = "state"
ZONES = "zones"


def aura_to_ha(data: dict[str, Any]) -> dict[str, Any]:
    """Convert AsusRouter Aura data to Home Assistant format."""

    result = {
        STATE: data.get(STATE, False),
        ZONES: data.get(ZONES, 0),
    }

    # Current active effect
    _effect = data.get(SCHEME, 0)
    result["effect"] = AURA_EFFECTS_MAP.get(_effect, AURA_NO_EFFECT)

    # Colors
    if ACTIVE_COLOR in data:
        result[RGB_COLOR] = ColorRGBB(data[ACTIVE_COLOR], scale=255).as_tuple()
    if ACTIVE_BRIGHTNESS in data:
        result[BRIGHTNESS] = scale_value_int(
            data.get(ACTIVE_BRIGHTNESS, AURA_FALLBACK_BRIGHTNESS),
            255,
            128,
        )

    for i in range(result["zones"]):
        color_key = f"active_{i}_color"
        brightness_key = f"active_{i}_brightness"
        if color_key in data:
            result[f"{RGB_COLOR}_{i}"] = ColorRGBB(
                data.get(color_key, AURA_FALLBACK_COLOR),
                scale=255,
            ).as_tuple()
        if brightness_key in data:
            result[f"{BRIGHTNESS}_{i}"] = scale_value_int(
                data.get(brightness_key, AURA_FALLBACK_BRIGHTNESS),
                255,
                128,
            )

    # Color mode support
    result["color_mode"] = SUPPORTED_COLOR_MODES.get(_effect, ColorMode.ONOFF)

    return result


def per_zone_light(zones: int = 3) -> list[AREntityDescription]:
    """Create a per-zone light entity descriptions."""

    return [
        ARLightDescription(
            key=STATE,
            key_group="aura",
            name=f"AURA Zone {i+1}",
            icon_on=ICON_LIGHT_ON,
            icon_off=ICON_LIGHT_OFF,
            capabilities={"zone_id": i},
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            extra_state_attributes={
                f"{BRIGHTNESS}_{i}": BRIGHTNESS,
                f"{RGB_COLOR}_{i}": RGB_COLOR,
            },
        )
        for i in range(zones)
    ]
