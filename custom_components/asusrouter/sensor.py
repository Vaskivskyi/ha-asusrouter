"""AsusRouter sensor module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import AREntity, ARSensorDescription, get_entities
from .modules import SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter sensors."""

    async_add_entities(
        get_entities(config_entry.runtime_data, SENSORS, ARSensor)
    )


class ARSensor(AREntity, SensorEntity):
    """AsusRouter sensor."""

    entity_description: ARSensorDescription

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""

        return self.entity_description.value_fn(self._device_data)
