"""AsusRouter light module."""

from __future__ import annotations

from typing import Any

from asusrouter.modules.led import AsusLED
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import ASUSROUTER, DOMAIN, STATIC_LIGHTS
from .dataclass import ARLightDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    lights = STATIC_LIGHTS.copy()

    if not hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER].bridge.identity.led:
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

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on LED."""

        await self._set_state(AsusLED.ON)

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off LED."""

        await self._set_state(AsusLED.OFF)
