"""Tests for the update module."""

from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from asusrouter.modules.firmware import ARFirmwareSourceUniversal
from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.update import UpdateEntityFeature
import pytest

from custom_components.asusrouter import update
from custom_components.asusrouter.entity import ARUpdateDescription
from custom_components.asusrouter.modules import UPDATES
from custom_components.asusrouter.update import ARUpdate, async_setup_entry

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
DEVICE_DATA = {"key": "value"}


async def test_setup_entry() -> None:
    """Test that every update of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(update, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, UPDATES, ARUpdate, add_entities
    )


@pytest.mark.parametrize("description", UPDATES, ids=lambda d: d.key)
async def test_update_strings(description: ARUpdateDescription) -> None:
    """Test that every update has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["update"]
    assert description.translation_key in icons["entity"]["update"]


def _get_update(**kwargs: Any) -> ARUpdate:
    """Create an update of the test device."""

    description = ARUpdateDescription(
        key="test",
        translation_key="test",
        source=ARFirmwareSourceUniversal,
        update_interval=timedelta(seconds=30),
        unique_id_name="Test Name",
        **{
            "value_fn": Mock(return_value="1.0"),
            "latest_fn": Mock(return_value="2.0"),
            **kwargs,
        },
    )
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))

    return ARUpdate(coordinator, description, MAC)


async def test_versions() -> None:
    """Test that the versions are read from the device data."""

    entity = _get_update()

    assert entity.installed_version == "1.0"
    assert entity.latest_version == "2.0"
    assert entity.supported_features == UpdateEntityFeature(0)
    assert await entity.async_release_notes() is None


async def test_release_notes() -> None:
    """Test that the release notes are read from the device data."""

    release_notes_fn = Mock(return_value="Notes")
    entity = _get_update(release_notes_fn=release_notes_fn)

    assert entity.supported_features == UpdateEntityFeature.RELEASE_NOTES
    assert await entity.async_release_notes() == "Notes"
    release_notes_fn.assert_called_once_with(DEVICE_DATA)
