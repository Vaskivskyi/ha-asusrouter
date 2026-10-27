"""Tests for the sensor module."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import Mock, patch

from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import sensor
from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules import SENSORS
from custom_components.asusrouter.sensor import ARSensor, async_setup_entry

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
DEVICE_DATA = {"key": "value"}
VALUE = 42


async def test_setup_entry() -> None:
    """Test that every sensor of the device and its nodes is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(sensor, "get_entities") as get_entities:
        await async_setup_entry(Mock(), entry, add_entities)

    get_entities.assert_called_once_with(entry.runtime_data, SENSORS, ARSensor)
    add_entities.assert_called_once_with(get_entities.return_value)


async def test_native_value() -> None:
    """Test that the value is read from the device data."""

    value_fn = Mock(return_value=VALUE)
    description = replace(SENSORS[0], value_fn=value_fn, data_fn=None)
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))

    entity = ARSensor(coordinator, description, MAC)

    assert entity.native_value == VALUE
    value_fn.assert_called_once_with(DEVICE_DATA)


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
async def test_sensor_strings(description: ARSensorDescription) -> None:
    """Test that every sensor has a name and an icon."""

    strings = json.loads((COMPONENT / "strings.json").read_text("utf-8"))
    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert description.translation_key in strings["entity"]["sensor"]
    assert description.translation_key in icons["entity"]["sensor"]
