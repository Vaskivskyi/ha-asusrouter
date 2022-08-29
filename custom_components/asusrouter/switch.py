"""AsusRouter switches."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .compilers import list_switches_vpn_clients, list_switches_wlan
from .const import CONF_ENABLE_CONTROL
from .dataclass import ARSwitchDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import AsusRouterObj

SWITCHES = {}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter switches."""

    if entry.options[CONF_ENABLE_CONTROL]:
        SWITCHES.update(list_switches_vpn_clients(5))
        SWITCHES.update(list_switches_wlan(3))

    await async_setup_ar_entry(hass, entry, async_add_entities, SWITCHES, ARSwitch)


class ARSwitch(ARBinaryEntity, SwitchEntity):
    """AsusRouter switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: ARSwitchDescription,
    ) -> None:
        """Initialize AsusRouter switch."""

        super().__init__(coordinator, router, description)
        self._service_on = description.service_on
        self._service_on_args = description.service_on_args
        self._service_off = description.service_off
        self._service_off_args = description.service_off_args
        self._service_expect_modify = description.service_expect_modify

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on switch."""

        try:
            result = await self.api.async_service_run(
                self._service_on,
                arguments=self._service_on_args,
                expect_modify=self._service_expect_modify,
            )
            await self.coordinator.async_request_refresh()
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
                self._service_off,
                arguments=self._service_off_args,
                expect_modify=self._service_expect_modify,
            )
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("Switch state was not set!")
        except Exception as ex:
            _LOGGER.error(f"Switch control has returned an exception: {ex}")
