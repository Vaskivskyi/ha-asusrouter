"""AsusRouter device tracker module."""

from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .entity import AREntity, ARTrackerDescription, async_setup_entities
from .modules import TRACKERS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter device trackers."""

    async_setup_entities(config_entry, TRACKERS, ARTracker, async_add_entities)


class ARTracker(AREntity, ScannerEntity):
    """AsusRouter tracker of a client."""

    # Named after the device of the client
    _attr_name = None

    entity_description: ARTrackerDescription

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id built for the entity."""

        return self._attr_unique_id

    @property
    def available(self) -> bool:
        """Return whether the clients are read, a missing one is away."""

        return self.coordinator.last_update_success

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected."""

        data = self._device_data
        return data is not None and bool(
            self.entity_description.value_fn(data)
        )

    @property
    def ip_address(self) -> str | None:
        """Return the IP address of the client."""

        data = self._device_data
        return None if data is None else self.entity_description.ip_fn(data)

    @property
    def mac_address(self) -> str:
        """Return the MAC address of the client."""

        return format_mac(str(self._key))

    @property
    def hostname(self) -> str | None:
        """Return the hostname of the client."""

        data = self._device_data
        return (
            None if data is None else self.entity_description.hostname_fn(data)
        )
