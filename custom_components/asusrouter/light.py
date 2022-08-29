"""AsusRouter lights."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_ENABLE_CONTROL, DATA_ASUSROUTER, DOMAIN, SENSORS_TYPE_LIGHT
from .dataclass import ARLightDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import AsusRouterObj

LIGHTS = {
    (SENSORS_TYPE_LIGHT, "led"): ARLightDescription(
        key="led",
        key_group=SENSORS_TYPE_LIGHT,
        name="LED",
        icon="mdi:led-outline",
        icon_on="mdi:led-on",
        icon_off="mdi:led-off",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter lights."""

    if (
        not entry.options[CONF_ENABLE_CONTROL]
        or not hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER].api._identity.led
    ):
        return

    await async_setup_ar_entry(hass, entry, async_add_entities, LIGHTS, ARLightLED)


class ARLightLED(ARBinaryEntity, LightEntity):
    """AsusRouter LED light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: ARLightDescription,
    ) -> None:
        """Initialize AsusRouter LED light."""

        super().__init__(coordinator, router, description)

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on LED."""

        try:
            result = await self.api.async_service_led_set("on")
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:
            _LOGGER.error(f"LED control has returned an exception: {ex}")

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off LED."""

        try:
            result = await self.api.async_service_led_set("off")
            await self.coordinator.async_request_refresh()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:
            _LOGGER.error(f"LED control has returned an exception: {ex}")

    async def async_update(self) -> None:
        """Update state from the device."""

        self._state = await self.api.async_service_led_get()
