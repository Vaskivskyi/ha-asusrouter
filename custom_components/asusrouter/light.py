"""AsusRouter light module."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from asusrouter.modules.aura import AsusAura
from asusrouter.modules.color import ColorRGB, scale_value_int
from asusrouter.modules.led import AsusLED

from .const import ASUSROUTER, DOMAIN, STATIC_AURA, STATIC_LIGHTS
from .dataclass import ARLightDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .modules.aura import AURA_EFFECTS, AURA_NO_EFFECT, per_zone_light
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)

EFFECT = "effect"
RGB_COLOR = "rgb_color"
BRIGHTNESS = "brightness"
COLOR_MODE = "color_mode"
ZONE_ID = "zone_id"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    leds = STATIC_LIGHTS.copy()
    if (
        hass.data[DOMAIN][config_entry.entry_id][
            ASUSROUTER
        ].bridge.identity.led
        is True
    ):
        await async_setup_ar_entry(
            hass, config_entry, async_add_entities, leds, ARLightLED
        )

    auras = STATIC_AURA.copy()
    if (
        hass.data[DOMAIN][config_entry.entry_id][
            ASUSROUTER
        ].bridge.identity.aura
        is True
    ):
        # Create per-zone lights
        auras.extend(
            per_zone_light(
                hass.data[DOMAIN][config_entry.entry_id][
                    ASUSROUTER
                ].bridge.identity.aura_zone
            )
        )

        await async_setup_ar_entry(
            hass, config_entry, async_add_entities, auras, ARLightAura
        )


class ARLightLED(ARBinaryEntity, LightEntity):
    """AsusRouter LED light."""

    _attr_color_mode = ColorMode.ONOFF
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


class ARLightAura(ARBinaryEntity, LightEntity):
    """AsusRouter Aura light."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARLightDescription,
    ) -> None:
        """Initialize AsusRouter Aura light."""

        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_effect_list = AURA_EFFECTS

        super().__init__(coordinator, router, description)
        self.entity_description: ARLightDescription = description

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on Aura."""

        effect = AsusAura.ON
        if "effect" in kwargs:
            effect = AsusAura.__members__.get(
                kwargs["effect"].upper(), AsusAura.ON
            )

        color = None
        if "rgb_color" in kwargs:
            rgb = kwargs["rgb_color"]
            color = ColorRGB(rgb[0], rgb[1], rgb[2], scale=255)

        brightness = None
        if "brightness" in kwargs:
            brightness = scale_value_int(kwargs["brightness"], 128, 255)

        zone_id = (
            self.entity_description.capabilities.get("zone_id", None)
            if self.entity_description.capabilities
            else None
        )

        await self._set_state(
            effect,
            color=color,
            brightness=brightness,
            zone=zone_id,
        )

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off Aura."""

        await self._set_state(AsusAura.OFF)

    @property
    def effect(self) -> str | None:
        """Return the current effect."""

        return self.coordinator.data.get("effect", AURA_NO_EFFECT)

    @property
    def supported_color_modes(self) -> set[str] | None:
        """Return the supported color modes."""

        # This is a workaround to avoid a bug in HA
        # which does not hide the color picker and brightness slider
        # even when the current color mode is set to ONOFF only
        _supported_color_modes = self.coordinator.data.get(
            "color_mode", ColorMode.RGB
        )
        return {_supported_color_modes}

    @property
    def color_mode(self) -> ColorMode | str | None:
        """Return the color mode."""

        return self.coordinator.data.get("color_mode", ColorMode.RGB)
