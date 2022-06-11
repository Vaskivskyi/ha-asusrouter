"""AsusRouter switches."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .compilers import list_switches_vpn_clients
from .const import (
    CONF_ENABLE_CONTROL,
    DATA_ASUSROUTER,
    DOMAIN,
    KEY_COORDINATOR,
)
from .dataclass import ARSwitchDescription
from .router import AsusRouterObj

SWITCHES = {}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter switches."""

    router: AsusRouterObj = hass.data[DOMAIN][config_entry.entry_id][DATA_ASUSROUTER]
    entities = []

    if config_entry.options[CONF_ENABLE_CONTROL]:
        SWITCHES.update(list_switches_vpn_clients(5))

    for sensor_data in router._sensors_coordinator.values():
        coordinator = sensor_data[KEY_COORDINATOR]
        for sensor_description in SWITCHES:
            try:
                if sensor_description[0] in sensor_data:
                    if (
                        SWITCHES[sensor_description].key
                        in sensor_data[sensor_description[0]]
                    ):
                        entities.append(
                            ARSwitch(coordinator, router, SWITCHES[sensor_description])
                        )
            except Exception as ex:
                _LOGGER.warning(ex)

    async_add_entities(entities, True)


class ARSwitch(CoordinatorEntity, SwitchEntity):
    """AsusRouter switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: ARSwitchDescription,
    ) -> None:
        """Initialize AsusRouter switch."""

        super().__init__(coordinator)
        self.entity_description: ARSwitchDescription = description
        self.router = router
        self.api = router.api._api

        self._attr_name = f"{router._name} {description.name}"
        self._attr_unique_id = f"{DOMAIN} {self.name}"
        self._attr_device_info = router.device_info
        self._icon_onoff = (
            True if description.icon_on and description.icon_off else False
        )
        self._service_on = description.service_on
        self._service_off = description.service_off

        self.full_state: dict[str, Any] = dict()

    @property
    def is_on(self) -> bool:
        """Get switch state."""

        return self.coordinator.data.get(self.entity_description.key)

    @property
    def icon(self) -> str | None:
        """Get switch icon."""

        if self._icon_onoff:
            if self.coordinator.data.get(self.entity_description.key):
                return self.entity_description.icon_on
            else:
                return self.entity_description.icon_off
        else:
            return self.entity_description.icon

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on switch."""

        try:
            result = await self.api.async_service_run(
                self._service_on, expect_modify=False
            )
            if not result:
                _LOGGER.debug("Switch state was not set!")
        except Exception as ex:
            _LOGGER.error(f"Switch control has returned an exception: {ex}")

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off switch."""

        try:
            result = await self.api.async_service_run(
                self._service_off, expect_modify=False
            )
            if not result:
                _LOGGER.debug("Switch state was not set!")
        except Exception as ex:
            _LOGGER.error(f"Switch control has returned an exception: {ex}")

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
