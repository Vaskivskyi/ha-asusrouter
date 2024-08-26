"""AsusRouter update module."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from asusrouter.modules.system import AsusSystem

from .const import STATIC_UPDATES
from .dataclass import ARUpdateDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter updates."""

    updates = STATIC_UPDATES.copy()

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, updates, ARUpdate
    )


class ARUpdate(ARBinaryEntity, UpdateEntity):
    """AsusRouter update."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARUpdateDescription,
    ) -> None:
        """Initialize AsusRouter update."""

        super().__init__(coordinator, router, description)
        self.entity_description: ARUpdateDescription = description

        self._attr_installed_version = self.extra_state_attributes.get(
            "current"
        )
        self._attr_latest_version = self.extra_state_attributes.get("latest")
        self._attr_release_summary = self.extra_state_attributes.get(
            "release_note"
        )
        self._attr_in_progress = False

        self._attr_supported_features = (
            UpdateEntityFeature.RELEASE_NOTES
            | UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
        )

    def release_notes(self) -> str | None:
        """Return the release notes."""

        return self.extra_state_attributes.get("release_note")

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install the update."""
        try:
            _LOGGER.debug(
                "Trying to install Firmware update. This might take several minutes."
            )
            result = await self.api.async_set_state(
                state=AsusSystem.FIRMWARE_UPGRADE,
            )
            if not result:
                _LOGGER.debug(
                    "Something went wrong while trying to install the update."
                )
            else:
                self._attr_in_progress = True
                await asyncio.sleep(120)
                self._attr_in_progress = False

        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error(
                "An exception occurred while trying to install the update: %s",
                ex,
            )
