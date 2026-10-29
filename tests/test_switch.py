"""Tests for the switch module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from custom_components.asusrouter import switch
from custom_components.asusrouter.entity import ARSwitchDescription
from custom_components.asusrouter.modules import SWITCHES
from custom_components.asusrouter.switch import ARSwitch, async_setup_entry

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")


async def test_setup_entry() -> None:
    """Test that every switch of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(switch, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, SWITCHES, ARSwitch, add_entities
    )


@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
async def test_switch_strings(description: ARSwitchDescription) -> None:
    """Test that every switch has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["switch"]
    assert description.translation_key in icons["entity"]["switch"]
