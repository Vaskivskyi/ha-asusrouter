"""AsusRouter binary sensor module."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import ARBinarySensorDescription, AREntity, async_setup_entities
from .modules import BINARY_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter binary sensors."""

    async_setup_entities(
        config_entry, BINARY_SENSORS, ARBinarySensor, async_add_entities
    )


class ARBinarySensor(AREntity, BinarySensorEntity):
    """AsusRouter binary sensor."""

    entity_description: ARBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """Return the sensor state."""

        value: bool | None = self.entity_description.value_fn(
            self._device_data
        )
        return value
