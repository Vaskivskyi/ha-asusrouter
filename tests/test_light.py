"""Tests for the light module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from custom_components.asusrouter import light
from custom_components.asusrouter.entity import ARLightDescription
from custom_components.asusrouter.light import ARLight, async_setup_entry
from custom_components.asusrouter.modules import LIGHTS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")


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
