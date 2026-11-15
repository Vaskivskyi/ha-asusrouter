"""Tests for the Aura module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.aura import (
    ARAuraAction,
    ARAuraField,
    ARAuraScheme,
    ARAuraSourceUniversal,
)
from asusrouter.modules.support.flag import ARSupportType
from asusrouter.tools.color import Color
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.entity import ARLightDescription
from custom_components.asusrouter.modules.aura import LIGHTS, SWITCHES

DESCRIPTIONS: dict[str, ARLightDescription] = {
    description.key: description for description in LIGHTS
}
AURA = DESCRIPTIONS["aura"]
ZONE = DESCRIPTIONS["aura_zone_2"]
NIGHT_MODE = SWITCHES[0]

RED = Color(255, 0, 0, 128)
GREEN = Color(0, 255, 0, 255)
BRIGHTNESS = 64
DATA: dict[ARAuraField, Any] = {
    ARAuraField.STATE: True,
    ARAuraField.SCHEME: ARAuraScheme.STATIC,
    ARAuraField.ZONES: 2,
    ARAuraField.COLORS: {
        ARAuraScheme.STATIC: [GREEN, RED],
        ARAuraScheme.GRADIENT: [GREEN, GREEN],
    },
    ARAuraField.COLOR: Color(0, 128, 0, 255),
    ARAuraField.NIGHT_MODE: False,
}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "enabled"),
    [
        ("aura", "AURA", True),
        ("aura_zone_1", "AURA Zone 1", False),
        ("aura_zone_8", "AURA Zone 8", False),
    ],
)
def test_description(key: str, unique_id_name: str, enabled: bool) -> None:
    """Test that every light keeps its unique_id and default."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.source is ARAuraSourceUniversal
    assert description.entity_category is EntityCategory.CONFIG
    assert description.entity_registry_enabled_default is enabled
    assert description.effects == (
        "gradient",
        "static",
        "breathing",
        "evolution",
        "rainbow",
        "wave",
        "marquee",
    )


def test_zone_translation() -> None:
    """Test that a zone is named by its number."""

    assert AURA.translation_placeholders is None
    assert ZONE.translation_key == "aura_zone"
    assert ZONE.translation_placeholders == {"zone": "2"}


@pytest.mark.parametrize("support", [True, False])
@pytest.mark.parametrize("description", [AURA, ZONE, NIGHT_MODE])
def test_supported(description: Any, support: bool) -> None:
    """Test that only a device with Aura has its entities."""

    bridge = Mock()
    bridge.identity.support = {ARSupportType.AURA: support}

    assert description.supported_fn is not None
    assert description.supported_fn(bridge) is support


@pytest.mark.parametrize(
    ("data", "expected"),
    [(DATA, DATA), ({}, None), (None, None)],
)
def test_data(data: Any, expected: Any) -> None:
    """Test that nothing is read before the Aura state is."""

    assert AURA.data_fn is not None
    assert AURA.data_fn(data) == expected


@pytest.mark.parametrize(
    ("key", "expected"),
    [("aura", True), ("aura_zone_2", True), ("aura_zone_3", False)],
)
def test_exists(key: str, expected: bool) -> None:
    """Test that a zone exists only when the device reports it."""

    exists_fn = DESCRIPTIONS[key].exists_fn

    assert (exists_fn is None or exists_fn(DATA)) is expected


@pytest.mark.parametrize("state", [True, False])
def test_value(state: bool) -> None:
    """Test that every light reports the Aura state."""

    data = {**DATA, ARAuraField.STATE: state}

    assert AURA.value_fn(data) is state
    assert ZONE.value_fn(data) is state


@pytest.mark.parametrize(
    ("scheme", "effect"),
    [
        (ARAuraScheme.STATIC, "static"),
        (ARAuraScheme.WAVE, "wave"),
        (ARAuraScheme.OFF, None),
        (ARAuraScheme.UNKNOWN, None),
        (None, None),
    ],
)
def test_effect(scheme: ARAuraScheme | None, effect: str | None) -> None:
    """Test that the effect is the active scheme."""

    assert AURA.effect_fn is not None
    assert AURA.effect_fn({ARAuraField.SCHEME: scheme}) == effect


def test_color() -> None:
    """Test that the Aura reports its blended color and each zone its own."""

    assert AURA.rgb_fn is not None
    assert AURA.brightness_fn is not None
    assert ZONE.rgb_fn is not None
    assert ZONE.brightness_fn is not None

    assert AURA.rgb_fn(DATA) == (0, 128, 0)
    assert AURA.brightness_fn(DATA) == GREEN.brightness
    assert ZONE.rgb_fn(DATA) == (255, 0, 0)
    assert ZONE.brightness_fn(DATA) == RED.brightness


@pytest.mark.parametrize(
    "data",
    [
        # Only the schemes with colors set by the user report them
        {**DATA, ARAuraField.SCHEME: ARAuraScheme.RAINBOW},
        # A zone without a stored color
        {**DATA, ARAuraField.SCHEME: ARAuraScheme.BREATHING},
        {
            **DATA,
            ARAuraField.COLORS: {ARAuraScheme.STATIC: [GREEN]},
        },
        {ARAuraField.STATE: True},
    ],
)
def test_color_missing(data: dict[ARAuraField, Any]) -> None:
    """Test that a zone without a color reports none."""

    assert ZONE.rgb_fn is not None
    assert ZONE.brightness_fn is not None

    assert ZONE.rgb_fn(data) is None
    assert ZONE.brightness_fn(data) is None


def test_color_missing_aura() -> None:
    """Test that the Aura without a color reports none."""

    assert AURA.rgb_fn is not None
    assert AURA.brightness_fn is not None

    assert AURA.rgb_fn({}) is None
    assert AURA.brightness_fn({}) is None


@pytest.mark.parametrize(
    ("state", "scheme"),
    [(True, ARAuraScheme.ON), (False, ARAuraScheme.OFF)],
)
def test_action(state: bool, scheme: ARAuraScheme) -> None:
    """Test that the Aura is turned on and off by its scheme."""

    action = ZONE.action_fn(state, DATA)

    assert isinstance(action, ARAuraAction)
    assert action.scheme is scheme
    assert action.zone is None


@pytest.mark.parametrize(
    ("kwargs", "state", "scheme"),
    [
        ({"effect": "wave"}, True, ARAuraScheme.WAVE),
        ({"effect": "wave"}, False, ARAuraScheme.WAVE),
        # Turning on restores the last scheme
        ({}, False, ARAuraScheme.ON),
        # A light already on keeps its scheme
        ({"brightness": 64}, True, None),
    ],
)
def test_turn_on(
    kwargs: dict[str, Any], state: bool, scheme: ARAuraScheme | None
) -> None:
    """Test that the Aura turns on with the requested effect."""

    assert AURA.turn_on_fn is not None
    action = AURA.turn_on_fn(kwargs, {**DATA, ARAuraField.STATE: state})

    assert isinstance(action, ARAuraAction)
    assert action.scheme is scheme
    assert action.brightness == kwargs.get("brightness")
    assert action.color is None
    assert action.zone is None


def test_turn_on_zone() -> None:
    """Test that a zone turns on with its own color and brightness."""

    assert ZONE.turn_on_fn is not None
    action = ZONE.turn_on_fn(
        {"rgb_color": (0, 0, 255), "brightness": BRIGHTNESS}, DATA
    )

    assert isinstance(action, ARAuraAction)
    assert action.color == Color(0, 0, 255)
    assert action.brightness == BRIGHTNESS
    assert action.zone == 1


def test_night_mode() -> None:
    """Test that the night mode is switched on its own."""

    assert NIGHT_MODE.unique_id_name == "Aura night mode"
    assert NIGHT_MODE.entity_registry_enabled_default is False
    assert NIGHT_MODE.value_fn(DATA) is False
    action = NIGHT_MODE.action_fn(True, DATA)
    assert isinstance(action, ARAuraAction)
    assert action.night_mode is True
    assert action.scheme is None


@pytest.mark.parametrize(
    ("data", "expected"),
    [(DATA, True), ({ARAuraField.STATE: True}, False)],
)
def test_night_mode_exists(
    data: dict[ARAuraField, Any], expected: bool
) -> None:
    """Test that the night mode exists only when the device reports it."""

    assert NIGHT_MODE.exists_fn is not None
    assert NIGHT_MODE.exists_fn(data) is expected
