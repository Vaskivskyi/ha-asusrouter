"""AsusRouter switch module."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import ARSwitchDescription, ARToggleEntity, async_setup_entities
from .modules import SWITCHES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter switches."""

    async_setup_entities(config_entry, SWITCHES, ARSwitch, async_add_entities)


class ARSwitch(ARToggleEntity, SwitchEntity):
    """AsusRouter switch."""

    entity_description: ARSwitchDescription
