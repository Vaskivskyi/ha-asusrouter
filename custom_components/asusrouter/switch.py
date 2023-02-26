"""AsusRouter switch module."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_ENABLE_CONTROL,
    CONF_HIDE_PASSWORDS,
    PASSWORD,
    STATIC_SWITCHES,
    STATIC_SWITCHES_OPTIONAL,
)
from .dataclass import ARSwitchDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter switches."""

    switches = STATIC_SWITCHES.copy()

    hide = []
    if config_entry.options.get(CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS):
        hide.append(PASSWORD)

    if config_entry.options[CONF_ENABLE_CONTROL]:
        switches.extend(STATIC_SWITCHES_OPTIONAL)

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, switches, ARSwitch, hide
    )


class ARSwitch(ARBinaryEntity, SwitchEntity):
    """AsusRouter switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARSwitchDescription,
    ) -> None:
        """Initialize AsusRouter switch."""

        super().__init__(coordinator, router, description)
        self.entity_description: ARSwitchDescription = description

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
            result = await self.api.async_service_generic_apply(
                self._service_on,
                arguments=self._service_on_args,
                expect_modify=self._service_expect_modify,
            )
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("Switch state was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Switch control has returned an exception: %s", ex)

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off switch."""

        try:
            result = await self.api.async_service_generic_apply(
                self._service_off,
                arguments=self._service_off_args,
                expect_modify=self._service_expect_modify,
            )
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("Switch state was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Switch control has returned an exception: %s", ex)
