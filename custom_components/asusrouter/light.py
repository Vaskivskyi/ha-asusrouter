"""AsusRouter lights"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import (
    CONF_ENABLE_CONTROL,
    DATA_ASUSROUTER,
    DOMAIN,
)
from .dataclass import ARLightDescription
from .router import AsusRouterObj


LED_DESCRIPTION = ARLightDescription(
    key = "LED",
    name = "LED",
    icon = "mdi:led-outline",
    icon_on = "mdi:led-on",
    icon_off = "mdi:led-off",
    entity_category = EntityCategory.CONFIG,
    entity_registry_enabled_default = True,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter lights"""

    router : AsusRouterObj = hass.data[DOMAIN][config_entry.entry_id][DATA_ASUSROUTER]
    entities = []

    if config_entry.options[CONF_ENABLE_CONTROL]:
        if router.api._identity.led:
            entities.append(ARLightLED(router, LED_DESCRIPTION))

    async_add_entities(entities)


class ARLightLED(LightEntity):
    """AsusRouter LED light"""

    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self,
        router: AsusRouterObj,
        description: ARLightDescription,
    ) -> None:
        """Initialize AsusRouter LED light"""

        super().__init__()
        self.entity_description: ARLightDescription = description
        self.router = router
        self.api = router.api._api

        self._attr_name = "{} {}".format(router._name, description.name)
        self._attr_unique_id = "{} {}".format(DOMAIN, self.name)
        self._attr_device_info = router.device_info
        self._icon_on = description.icon_on
        self._icon_off = description.icon_off

        self._state : bool = self.api.led
        self.update_icon()


    @property
    def is_on(self) -> bool:
        """Get LED state"""

        return self._state


    def update_icon(self) -> None:
        """Update icon"""

        if self._state:
            if self._icon_on:
                self.entity_description.icon = self._icon_on
        else:
            if self._icon_off:
                self.entity_description.icon = self._icon_off


    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on LED"""

        try:
            result = await self.api.async_service_led_set("on")
            self.update_icon()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:
            _LOGGER.error("LED control has returned an exception: {}".format(ex))


    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off LED"""

        try:
            result = await self.api.async_service_led_set("off")
            self.update_icon()
            if not result:
                _LOGGER.debug("LED state was not set!")
        except Exception as ex:
            _LOGGER.error("LED control has returned an exception: {}".format(ex))


    async def async_update(self) -> None:
        """Update state from the device"""

        self._state = await self.api.async_service_led_get()
        self.update_icon()


