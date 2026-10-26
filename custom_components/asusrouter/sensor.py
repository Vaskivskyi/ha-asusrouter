"""AsusRouter sensor module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import AREntity, ARSensorDescription
from .modules import SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter sensors."""

    runtime_data = config_entry.runtime_data
    mac = runtime_data.bridge.identity.mac
    # Entities are tied to the device MAC, nothing to attach them to
    if mac is None:
        return

    coordinators = runtime_data.coordinators
    entities = [
        ARSensor(coordinators[description.source], description, mac)
        for description in SENSORS
    ]
    entities.extend(
        ARSensor(
            coordinators[description.node_source(node)], description, node
        )
        for description in SENSORS
        if description.node_source is not None
        for node in runtime_data.nodes
    )

    async_add_entities(entities)


class ARSensor(AREntity, SensorEntity):
    """AsusRouter sensor."""

    entity_description: ARSensorDescription

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""

        return self.entity_description.value_fn(self._device_data)
