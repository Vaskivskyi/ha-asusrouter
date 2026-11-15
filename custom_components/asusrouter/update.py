"""AsusRouter update module."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import AREntity, ARUpdateDescription, async_setup_entities
from .modules import UPDATES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter updates."""

    async_setup_entities(config_entry, UPDATES, ARUpdate, async_add_entities)


class ARUpdate(AREntity, UpdateEntity):
    """AsusRouter update."""

    entity_description: ARUpdateDescription

    @property
    def installed_version(self) -> str | None:
        """Return the installed version."""

        version: str | None = self.entity_description.value_fn(
            self._device_data
        )
        return version

    @property
    def latest_version(self) -> str | None:
        """Return the latest version."""

        return self.entity_description.latest_fn(self._device_data)

    @property
    def supported_features(self) -> UpdateEntityFeature:
        """Return the features the update supports."""

        return (
            UpdateEntityFeature(0)
            if self.entity_description.release_notes_fn is None
            else UpdateEntityFeature.RELEASE_NOTES
        )

    async def async_release_notes(self) -> str | None:
        """Return the release notes."""

        release_notes_fn = self.entity_description.release_notes_fn
        return (
            None
            if release_notes_fn is None
            else release_notes_fn(self._device_data)
        )
