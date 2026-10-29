"""AsusRouter light module."""

from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import ARLightDescription, ARToggleEntity, async_setup_entities
from .modules import LIGHTS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    async_setup_entities(config_entry, LIGHTS, ARLight, async_add_entities)


class ARLight(ARToggleEntity, LightEntity):
    """AsusRouter light."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    entity_description: ARLightDescription
