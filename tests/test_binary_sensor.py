"""Tests for the binary sensor module."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import Mock, patch

from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import binary_sensor
from custom_components.asusrouter.binary_sensor import (
    ARBinarySensor,
    async_setup_entry,
)
from custom_components.asusrouter.entity import ARBinarySensorDescription
from custom_components.asusrouter.modules import BINARY_SENSORS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
DEVICE_DATA = {"key": "value"}
VALUE = True


async def test_setup_entry() -> None:
    """Test that every binary sensor of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(binary_sensor, "async_setup_entities") as setup_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    setup_entities.assert_called_once_with(
        entry, BINARY_SENSORS, ARBinarySensor, add_entities
    )


async def test_is_on() -> None:
    """Test that the state is read from the device data."""

    value_fn = Mock(return_value=VALUE)
    description = replace(BINARY_SENSORS[0], value_fn=value_fn, data_fn=None)
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))

    entity = ARBinarySensor(coordinator, description, MAC)

    assert entity.is_on is VALUE
    value_fn.assert_called_once_with(DEVICE_DATA)


@pytest.mark.parametrize("description", BINARY_SENSORS, ids=lambda d: d.key)
async def test_binary_sensor_strings(
    description: ARBinarySensorDescription,
) -> None:
    """Test that every binary sensor has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["binary_sensor"]
    assert description.translation_key in icons["entity"]["binary_sensor"]
