"""Tests for the sensor module."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from asusrouter.modules.system_status import ARSystemStatusSource
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import ARRuntimeData
from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules import SENSORS
from custom_components.asusrouter.sensor import ARSensor, async_setup_entry

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
DEVICE_DATA = {"key": "value"}
VALUE = 42


def _get_entry(
    mac: MacAddress | None = MAC, nodes: list[MacAddress] | None = None
) -> Mock:
    """Create a config entry of a device with the given MAC."""

    bridge = Mock()
    bridge.identity.mac = mac
    nodes = nodes or []

    coordinators: dict[Any, Any] = {
        description.source: Mock(data={}) for description in SENSORS
    }
    for description in SENSORS:
        if description.node_source is not None:
            for node in nodes:
                coordinators[description.node_source(node)] = Mock(data={})

    entry = Mock()
    entry.runtime_data = ARRuntimeData(
        bridge=bridge, coordinators=coordinators, nodes=nodes
    )

    return entry


async def test_setup_entry() -> None:
    """Test that every sensor uses the coordinator of its source."""

    entry = _get_entry()
    add_entities = Mock()

    await async_setup_entry(Mock(), entry, add_entities)

    entities = list(add_entities.call_args.args[0])
    coordinators = entry.runtime_data.coordinators
    assert [entity.entity_description for entity in entities] == list(SENSORS)
    assert all(isinstance(entity, ARSensor) for entity in entities)
    assert all(
        entity.coordinator is coordinators[entity.entity_description.source]
        for entity in entities
    )


async def test_setup_entry_nodes() -> None:
    """Test that every node gets the sensors available on nodes."""

    entry = _get_entry(nodes=[NODE_MAC])
    add_entities = Mock()

    await async_setup_entry(Mock(), entry, add_entities)

    entities = add_entities.call_args.args[0]
    coordinators = entry.runtime_data.coordinators
    node_entities = [entity for entity in entities if entity._mac == NODE_MAC]
    node_sensors = [d for d in SENSORS if d.node_source is not None]

    assert len(entities) == len(SENSORS) + len(node_sensors)
    assert [e.entity_description for e in node_entities] == node_sensors
    assert all(
        entity.coordinator
        is coordinators[ARSystemStatusSource(target=NODE_MAC)]
        for entity in node_entities
    )


async def test_setup_entry_without_mac() -> None:
    """Test that no sensor is created for a device without a MAC."""

    add_entities = Mock()

    await async_setup_entry(Mock(), _get_entry(mac=None), add_entities)

    add_entities.assert_not_called()


async def test_native_value() -> None:
    """Test that the value is read from the device data."""

    value_fn = Mock(return_value=VALUE)
    description = replace(SENSORS[0], value_fn=value_fn)
    coordinator = Mock(data={MAC: DEVICE_DATA})

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
