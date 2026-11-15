"""AsusRouter Aura module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asusrouter.modules.aura import (
    ARAuraAction,
    ARAuraField,
    ARAuraScheme,
    ARAuraSourceUniversal,
)
from asusrouter.modules.aura.enums import AURA_COLOR_SCHEMES
from asusrouter.modules.aura.support import aura_supported
from asusrouter.tools.color import Color
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
)
from homeassistant.const import EntityCategory

from ..entity import ARLightDescription, ARSwitchDescription

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)

# Zones of a device, more than any device is known to report
_ZONES = range(1, 9)
# Every scheme showing light, by its effect name
_EFFECTS = {
    scheme.name.lower(): scheme
    for scheme in ARAuraScheme
    if scheme > ARAuraScheme.OFF
}


def _get_aura(data: Any) -> dict[ARAuraField, Any] | None:
    """Get the Aura state, None when nothing was read."""

    return data if isinstance(data, dict) and data else None


def _is_supported(bridge: ARBridge) -> bool:
    """Check whether the device has Aura."""

    return aura_supported(bridge.identity)


def _get_effect(data: dict[ARAuraField, Any]) -> str | None:
    """Get the effect of the active scheme."""

    scheme = data.get(ARAuraField.SCHEME)
    return (
        scheme.name.lower()
        if isinstance(scheme, ARAuraScheme) and scheme > ARAuraScheme.OFF
        else None
    )


def _get_color(data: dict[ARAuraField, Any], zone: int | None) -> Color | None:
    """Get the color of a zone, of every zone when None."""

    if zone is None:
        color: Color | None = data.get(ARAuraField.COLOR)
        return color

    # Only the schemes with colors set by the user report them
    scheme = data.get(ARAuraField.SCHEME)
    if scheme not in AURA_COLOR_SCHEMES:
        return None
    colors = data.get(ARAuraField.COLORS, {}).get(scheme, [])
    return colors[zone] if zone < len(colors) else None


def _get_rgb(
    data: dict[ARAuraField, Any], zone: int | None
) -> tuple[int, int, int] | None:
    """Get the RGB color of a zone, of every zone when None."""

    color = _get_color(data, zone)
    return None if color is None else (color.red, color.green, color.blue)


def _get_brightness(
    data: dict[ARAuraField, Any], zone: int | None
) -> int | None:
    """Get the brightness of a zone, of every zone when None."""

    color = _get_color(data, zone)
    return None if color is None else color.brightness


def _get_turn_on(
    kwargs: dict[str, Any], data: dict[ARAuraField, Any], zone: int | None
) -> ARAuraAction:
    """Get the action turning a zone on, every zone when None."""

    effect = kwargs.get(ATTR_EFFECT)
    if effect is not None:
        scheme: ARAuraScheme | None = _EFFECTS[effect]
    # Turning on restores the last scheme
    elif not data.get(ARAuraField.STATE):
        scheme = ARAuraScheme.ON
    else:
        scheme = None
    rgb = kwargs.get(ATTR_RGB_COLOR)

    return ARAuraAction(
        scheme=scheme,
        color=None if rgb is None else Color(*rgb),
        brightness=kwargs.get(ATTR_BRIGHTNESS),
        zone=zone,
    )


def _get_light(
    key: str,
    unique_id_name: str,
    zone: int | None,
    *,
    enabled: bool,
) -> ARLightDescription:
    """Get the description of the light of a zone, every zone when None."""

    return ARLightDescription(
        key=key,
        translation_key=key if zone is None else "aura_zone",
        translation_placeholders=(
            None if zone is None else {"zone": str(zone + 1)}
        ),
        source=ARAuraSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        # The device reports its Aura, not keyed by its MAC
        data_fn=_get_aura,
        value_fn=lambda data: data.get(ARAuraField.STATE),
        # Turning off any zone turns off every zone
        action_fn=lambda state, _: ARAuraAction(
            scheme=ARAuraScheme.ON if state else ARAuraScheme.OFF
        ),
        effects=tuple(_EFFECTS),
        effect_fn=_get_effect,
        rgb_fn=lambda data: _get_rgb(data, zone),
        brightness_fn=lambda data: _get_brightness(data, zone),
        turn_on_fn=lambda kwargs, data: _get_turn_on(kwargs, data, zone),
        exists_fn=(
            None
            if zone is None
            else lambda data: data.get(ARAuraField.ZONES, 0) > zone
        ),
        supported_fn=_is_supported,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=enabled,
    )


LIGHTS: tuple[ARLightDescription, ...] = (
    _get_light("aura", "AURA", None, enabled=True),
    *(
        _get_light(
            f"aura_zone_{zone}", f"AURA Zone {zone}", zone - 1, enabled=False
        )
        for zone in _ZONES
    ),
)

SWITCHES: tuple[ARSwitchDescription, ...] = (
    ARSwitchDescription(
        key="aura_night_mode",
        translation_key="aura_night_mode",
        source=ARAuraSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Aura night mode",
        # The device reports its Aura, not keyed by its MAC
        data_fn=_get_aura,
        value_fn=lambda data: data.get(ARAuraField.NIGHT_MODE),
        action_fn=lambda state, _: ARAuraAction(night_mode=state),
        exists_fn=lambda data: ARAuraField.NIGHT_MODE in data,
        supported_fn=_is_supported,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)
