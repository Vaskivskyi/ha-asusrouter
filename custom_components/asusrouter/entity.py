"""AsusRouter entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import ASUSROUTER, DOMAIN, KEY_COORDINATOR
from .dataclass import AREntityDescription
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_ar_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    sensors: dict[Any, Any],
    sensor_class: AREntity,
) -> None:
    """Setup AsusRouter entities."""

    router: ARDevice = hass.data[DOMAIN][entry.entry_id][ASUSROUTER]
    entities = []

    for sensor_data in router._sensor_coordinator.values():
        coordinator = sensor_data[KEY_COORDINATOR]
        for sensor_description in sensors:
            try:
                if sensor_description[0] in sensor_data:
                    if (
                        sensors[sensor_description].key
                        in sensor_data[sensor_description[0]]
                    ):
                        entities.append(
                            sensor_class(
                                coordinator, router, sensors[sensor_description]
                            )
                        )
            except Exception as ex:
                _LOGGER.warning(ex)

    async_add_entities(entities, True)


class AREntity(CoordinatorEntity):
    """AsusRouter entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: AREntityDescription,
    ) -> None:
        """Initialize AsusRouter entity."""

        super().__init__(coordinator)
        self.entity_description: AREntityDescription = description
        self.router = router
        self.api = router.bridge.api
        self.coordinator = coordinator

        self._attr_name = f"{router._conf_name} {description.name}"
        self._attr_unique_id = f"{DOMAIN} {self.name}"
        self._attr_device_info = router.device_info
        self._attr_capability_attributes = description.capabilities

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        description = self.entity_description
        _attributes = description.extra_state_attributes
        if not _attributes:
            return {}

        attributes = {}

        for attr in _attributes:
            if attr in self.coordinator.data:
                attributes[_attributes[attr]] = self.coordinator.data[attr]

        return attributes


class ARBinaryEntity(AREntity):
    """AsusRouter binary entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: AREntityDescription,
    ) -> None:
        """Initialize AsusRouter binary entity."""

        super().__init__(coordinator, router, description)
        self._icon_onoff = (
            True if description.icon_on and description.icon_off else False
        )

    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self.coordinator.data.get(self.entity_description.key)

    @property
    def icon(self) -> str | None:
        """Get the icon."""

        if self._icon_onoff:
            if self.is_on:
                return self.entity_description.icon_on
            else:
                return self.entity_description.icon_off
        elif self.entity_description.icon:
            return self.entity_description.icon


class ARButtonEntity:
    """AsusRouter button entity."""

    def __init__(
        self,
        router: ARDevice,
        description: AREntityDescription,
    ) -> None:
        """Initialize AsusRouter button entity."""

        self.entity_description: AREntityDescription = description
        self.router = router
        self.api = router.bridge.api

        self._attr_name = f"{router._conf_name} {description.name}"
        self._attr_unique_id = f"{DOMAIN} {self.name}"
        self._attr_device_info = router.device_info
        self._attr_capability_attributes = description.capabilities
