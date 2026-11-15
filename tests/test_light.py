"""Tests for the light module."""

from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter.modules.led import ARLedSourceUniversal
from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.light import ColorMode, LightEntityFeature
import pytest

from custom_components.asusrouter import light
from custom_components.asusrouter.entity import (
    ARLightDescription,
    ARToggleEntity,
)
from custom_components.asusrouter.light import ARLight, async_setup_entry
from custom_components.asusrouter.modules import LIGHTS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
DEVICE_DATA = {"key": "value"}
BRIGHTNESS = 128


async def test_setup_entry() -> None:
    """Test that every light of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(light, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, LIGHTS, ARLight, add_entities
    )


@pytest.mark.parametrize("description", LIGHTS, ids=lambda d: d.key)
async def test_light_strings(description: ARLightDescription) -> None:
    """Test that every light has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["light"]
    assert description.translation_key in icons["entity"]["light"]


def _get_light(**kwargs: Any) -> ARLight:
    """Create a light of the test device."""

    description = ARLightDescription(
        key="test",
        translation_key="test",
        source=ARLedSourceUniversal,
        update_interval=timedelta(seconds=30),
        unique_id_name="Test Name",
        **{"value_fn": Mock(), "action_fn": Mock(), **kwargs},
    )
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))

    return ARLight(coordinator, description, MAC)


async def test_light_onoff() -> None:
    """Test that a light without colors or effects is only on or off."""

    entity = _get_light()

    assert entity.color_mode is ColorMode.ONOFF
    assert entity.supported_color_modes == {ColorMode.ONOFF}
    assert entity.supported_features == LightEntityFeature(0)
    assert entity.effect_list is None
    assert entity.brightness is None
    assert entity.effect is None
    assert entity.rgb_color is None


async def test_light_color() -> None:
    """Test that a light with colors and effects reads them from its data."""

    brightness_fn = Mock(return_value=BRIGHTNESS)
    effect_fn = Mock(return_value="static")
    rgb_fn = Mock(return_value=(255, 0, 0))
    entity = _get_light(
        effects=("static", "wave"),
        effect_fn=effect_fn,
        rgb_fn=rgb_fn,
        brightness_fn=brightness_fn,
    )

    assert entity.color_mode is ColorMode.RGB
    assert entity.supported_color_modes == {ColorMode.RGB}
    assert entity.supported_features == LightEntityFeature.EFFECT
    assert entity.effect_list == ["static", "wave"]
    assert entity.brightness == BRIGHTNESS
    assert entity.effect == "static"
    assert entity.rgb_color == (255, 0, 0)
    for read_fn in (brightness_fn, effect_fn, rgb_fn):
        read_fn.assert_called_once_with(DEVICE_DATA)


async def test_light_turn_on() -> None:
    """Test that a light turns on with the requested settings."""

    action_fn = Mock()
    turn_on_fn = Mock()
    entity = _get_light(action_fn=action_fn, turn_on_fn=turn_on_fn)

    with patch.object(
        ARToggleEntity, "_async_run_action", AsyncMock()
    ) as run_action:
        await entity.async_turn_on(effect="wave")

    turn_on_fn.assert_called_once_with({"effect": "wave"}, DEVICE_DATA)
    run_action.assert_awaited_once_with(turn_on_fn.return_value)
    action_fn.assert_not_called()


async def test_light_turn_on_plain() -> None:
    """Test that a light without settings turns on by its action."""

    action_fn = Mock()
    entity = _get_light(action_fn=action_fn)

    with patch.object(
        ARToggleEntity, "_async_run_action", AsyncMock()
    ) as run_action:
        await entity.async_turn_on()

    action_fn.assert_called_once_with(True, DEVICE_DATA)
    run_action.assert_awaited_once_with(action_fn.return_value)
