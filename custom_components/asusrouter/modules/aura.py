"""AsusRouter Aura module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

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

# Every scheme showing light, by its effect name
_EFFECTS = {
    scheme.name.lower(): scheme
    for scheme in ARAuraScheme
    if scheme > ARAuraScheme.OFF
}


class _Zone(NamedTuple):
    """The Aura state with the zone it is read for."""

    position: int
    data: dict[ARAuraField, Any]


def _get_zones(data: dict[ARAuraField, Any]) -> range:
    """Get the indexes of the zones the device reports."""

    zones = data.get(ARAuraField.ZONES)
    return range(zones if isinstance(zones, int) else 0)


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


# Shared by the light of every zone and those of a single zone
_LIGHT: dict[str, Any] = {
    "source": ARAuraSourceUniversal,
    "update_interval": UPDATE_INTERVAL,
    # The device reports its Aura, not keyed by its MAC
    "data_fn": _get_aura,
    # Turning off any zone turns off every zone
    "action_fn": lambda state, _: ARAuraAction(
        scheme=ARAuraScheme.ON if state else ARAuraScheme.OFF
    ),
    "effects": tuple(_EFFECTS),
    "supported_fn": _is_supported,
    "entity_category": EntityCategory.CONFIG,
}

LIGHTS: tuple[ARLightDescription, ...] = (
    ARLightDescription(
        key="aura",
        translation_key="aura",
        unique_id_name="AURA",
        value_fn=lambda data: data.get(ARAuraField.STATE),
        effect_fn=_get_effect,
        rgb_fn=lambda data: _get_rgb(data, None),
        brightness_fn=lambda data: _get_brightness(data, None),
        turn_on_fn=lambda kwargs, data: _get_turn_on(kwargs, data, None),
        **_LIGHT,
    ),
    ARLightDescription(
        key="aura_zone",
        translation_key="aura_zone",
        keys_fn=_get_zones,
        item_fn=lambda data, index: (
            _Zone(index, data) if index in _get_zones(data) else None
        ),
        unique_id_fn=lambda index: f"AURA Zone {index + 1}",
        placeholders_fn=lambda index: {"zone": str(index + 1)},
        value_fn=lambda zone: zone.data.get(ARAuraField.STATE),
        effect_fn=lambda zone: _get_effect(zone.data),
        rgb_fn=lambda zone: _get_rgb(zone.data, zone.position),
        brightness_fn=lambda zone: _get_brightness(zone.data, zone.position),
        turn_on_fn=lambda kwargs, zone: _get_turn_on(
            kwargs, zone.data, zone.position
        ),
        entity_registry_enabled_default=False,
        **_LIGHT,
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
