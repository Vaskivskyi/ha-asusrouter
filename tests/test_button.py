"""Tests for the button module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import button
from custom_components.asusrouter.button import ARButton, async_setup_entry
from custom_components.asusrouter.entity import ARButtonDescription
from custom_components.asusrouter.modules import BUTTONS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")


async def test_setup_entry() -> None:
    """Test that every button of the device is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(button, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, BUTTONS, ARButton, add_entities
    )


async def test_press() -> None:
    """Test that pressing runs the action without reading anything back."""

    entity = ARButton(Mock(), BUTTONS[0], MAC)

    with patch.object(ARButton, "_async_run_action", AsyncMock()) as run:
        await entity.async_press()

    run.assert_awaited_once()
    assert run.await_args is not None
    assert run.await_args.kwargs == {"refresh": False}


async def test_no_value() -> None:
    """Test that a button reads no value from its source."""

    assert BUTTONS[0].value_fn({"key": "value"}) is None


@pytest.mark.parametrize("description", BUTTONS, ids=lambda d: d.key)
async def test_button_strings(description: ARButtonDescription) -> None:
    """Test that every button has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["button"]
    assert description.translation_key in icons["entity"]["button"]
