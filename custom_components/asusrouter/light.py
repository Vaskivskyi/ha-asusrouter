"""AsusRouter light module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import AREntity, ARLightDescription, async_setup_entities
from .modules import LIGHTS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    async_setup_entities(config_entry, LIGHTS, ARLight, async_add_entities)


class ARLight(AREntity, LightEntity):
    """AsusRouter light."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    entity_description: ARLightDescription

    @property
    def is_on(self) -> bool | None:
        """Return the light state."""

        value: bool | None = self.entity_description.value_fn(
            self._device_data
        )
        return value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""

        await self._async_run_action(self.entity_description.action_fn(True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""

        await self._async_run_action(self.entity_description.action_fn(False))
