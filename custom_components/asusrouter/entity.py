"""AsusRouter entity module."""

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

from .const import ASUSROUTER, COORDINATOR, DOMAIN
from .dataclass import ARBinaryDescription, AREntityDescription, ARSwitchDescription
from .helpers import to_unique_id
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_ar_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    sensors: list[AREntityDescription],
    sensor_class: type[AREntity],
    hide: list[str] | None = None,
) -> None:
    """Set up AsusRouter entities."""

    router: ARDevice = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    entities = []

    if not hide:
        hide = []

    for sensor_data in router.sensor_coordinator.values():
        coordinator = sensor_data[COORDINATOR]
        for sensor_description in sensors:
            try:
                sensor_type = sensor_description.key_group

                # Make sure extra state attributes are dict
                if not sensor_description.extra_state_attributes:
                    sensor_description.extra_state_attributes = {}

                if sensor_type in sensor_data:
                    if sensor_description.key in sensor_data[sensor_type]:
                        # Hide protected values
                        sensor_description.extra_state_attributes = {
                            key: value
                            for key, value in sensor_description.extra_state_attributes.items()
                            if value not in hide
                        }

                        entities.append(
                            sensor_class(coordinator, router, sensor_description)
                        )
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.warning(ex)

    async_add_entities(entities)


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
        self.router = router
        self.api = router.bridge.api
        self.coordinator = coordinator

        self._attr_name = f"{router._conf_name} {description.name}"
        self._attr_unique_id = to_unique_id(f"{router.mac}_{description.name}")
        self._attr_device_info = router.device_info
        self._attr_capability_attributes = description.capabilities

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        # Check if description is of the needed class
        if not isinstance(self.entity_description, AREntityDescription):
            return {}

        description = self.entity_description
        _attributes = description.extra_state_attributes
        if not _attributes:
            return {}

        attributes = {}

        for attr in _attributes:
            if attr in self.coordinator.data:
                attributes[_attributes[attr]] = self.coordinator.data[attr]

        return dict(sorted(attributes.items())) or {}


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
        if isinstance(description, (ARBinaryDescription, ARSwitchDescription)):
            self._icon_onoff = bool(description.icon_on and description.icon_off)

    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self.coordinator.data.get(self.entity_description.key)

    @property
    def icon(self) -> str | None:
        """Get the icon."""

        if (
            isinstance(
                self.entity_description, (ARBinaryDescription, ARSwitchDescription)
            )
            and self._icon_onoff
        ):
            if self.is_on:
                return self.entity_description.icon_on
            return self.entity_description.icon_off
        if self.entity_description.icon:
            return self.entity_description.icon
        return None
