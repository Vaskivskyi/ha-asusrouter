"""Tests for the light module."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import light
from custom_components.asusrouter.entity import ARLightDescription
from custom_components.asusrouter.light import ARLight, async_setup_entry
from custom_components.asusrouter.modules import LIGHTS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
DEVICE_DATA = {"key": "value"}


def _get_light(**kwargs: Any) -> ARLight:
    """Create a light reading the test device data."""

    description = replace(LIGHTS[0], data_fn=None, **kwargs)
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))

    return ARLight(coordinator, description, MAC)


async def test_setup_entry() -> None:
    """Test that every light of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(light, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, LIGHTS, ARLight, add_entities
    )


async def test_is_on() -> None:
    """Test that the state is read from the device data."""

    value_fn = Mock(return_value=True)
    entity = _get_light(value_fn=value_fn)

    assert entity.is_on is True
    value_fn.assert_called_once_with(DEVICE_DATA)


@pytest.mark.parametrize(("method", "state"), [("on", True), ("off", False)])
async def test_turn(method: str, state: bool) -> None:
    """Test that turning the light runs its action."""

    action_fn = Mock()
    entity = _get_light(action_fn=action_fn)

    with patch.object(ARLight, "_async_run_action", AsyncMock()) as run:
        await getattr(entity, f"async_turn_{method}")()

    action_fn.assert_called_once_with(state)
    run.assert_awaited_once_with(action_fn.return_value)


@pytest.mark.parametrize("description", LIGHTS, ids=lambda d: d.key)
async def test_light_strings(description: ARLightDescription) -> None:
    """Test that every light has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["light"]
    assert description.translation_key in icons["entity"]["light"]
