"""AsusRouter button module."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import ARButtonDescription, AREntity, async_setup_entities
from .modules import BUTTONS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter buttons."""

    async_setup_entities(config_entry, BUTTONS, ARButton, async_add_entities)


class ARButton(AREntity, ButtonEntity):
    """AsusRouter button."""

    entity_description: ARButtonDescription

    async def async_press(self) -> None:
        """Run the action of the button."""

        # A restart leaves nothing to read back right away
        await self._async_run_action(
            self.entity_description.action_fn(), refresh=False
        )
