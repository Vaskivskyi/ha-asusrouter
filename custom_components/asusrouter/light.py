"""AsusRouter light module."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import ASUSROUTER, CONF_ENABLE_CONTROL, DOMAIN, STATIC_LIGHTS
from .dataclass import ARLightDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    lights = STATIC_LIGHTS.copy()

    if (
        not config_entry.options[CONF_ENABLE_CONTROL]
        or not hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER].bridge.identity.led
    ):
        return

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, lights, ARLightLED
    )


class ARLightLED(ARBinaryEntity, LightEntity):
    """AsusRouter LED light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARLightDescription,
    ) -> None:
        """Initialize AsusRouter LED light."""

        super().__init__(coordinator, router, description)
        self.entity_description: ARLightDescription = description
        self._state: bool

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on LED."""

        try:
            result = await self.api.async_set_led(True)
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("LED control has returned an exception: %s", ex)

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off LED."""

        try:
            result = await self.api.async_set_led(False)
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("LED control has returned an exception: %s", ex)

    async def async_update(self) -> None:
        """Update state from the device."""

        try:
            self._state = await self.api.async_get_led(use_cache=False)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("LED control has returned an exception: %s", ex)
