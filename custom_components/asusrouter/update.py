"""AsusRouter update module."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import STATIC_UPDATES
from .dataclass import ARUpdateDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice


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

        self._attr_installed_version = self.extra_state_attributes["current"]
        self._attr_latest_version = self.extra_state_attributes["available"]
