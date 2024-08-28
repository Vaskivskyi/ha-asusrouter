"""AsusRouter entity module."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from asusrouter.modules.homeassistant import convert_to_ha_state_bool
from asusrouter.modules.state import AsusState

from .const import ASUSROUTER, COORDINATOR, DOMAIN
from .dataclass import (
    ARBinaryDescription,
    AREntityDescription,
    ARSwitchDescription,
)
from .helpers import to_unique_id
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_ar_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    sensors: list[AREntityDescription],
    sensor_class: type[AREntity],
    hide: Optional[list[str]] = None,
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
                            sensor_class(
                                coordinator, router, sensor_description
                            )
                        )
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.warning(
                    "Got an exception when creating entities: %s. Please, report this."
                    + "Sensor description: %s",
                    ex,
                    sensor_description,
                )

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

        # Mask attributes
        attrs_to_mask = self.router.sensor_filters.get(
            (description.key_group, description.key),
            [],
        )
        for attr in attrs_to_mask:
            if attr in _attributes:
                _attributes.pop(attr, None)

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
            self._icon_onoff = bool(
                description.icon_on and description.icon_off
            )

    @property
    def is_on(self) -> Optional[bool]:
        """Get the state."""

        return convert_to_ha_state_bool(
            self.coordinator.data.get(self.entity_description.key)
        )

    @property
    def icon(self) -> Optional[str]:
        """Get the icon."""

        if (
            isinstance(
                self.entity_description,
                (ARBinaryDescription, ARSwitchDescription),
            )
            and self._icon_onoff
        ):
            if self.is_on:
                return self.entity_description.icon_on
            return self.entity_description.icon_off
        if self.entity_description.icon:
            return self.entity_description.icon
        return None

    async def _set_state(
        self,
        state: AsusState,
        expect_modify: bool = False,
        **kwargs: Any,
    ) -> None:
        """Set switch state."""
        try:
            _LOGGER.debug("Setting state to %s", state)
            result = await self.api.async_set_state(
                state=state, expect_modify=expect_modify, **kwargs
            )
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("State was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Unable to set state with an exception: %s", ex)
