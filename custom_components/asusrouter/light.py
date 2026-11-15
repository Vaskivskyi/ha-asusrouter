"""AsusRouter light module."""

from __future__ import annotations

from typing import Any

from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from . import ARConfigEntry
from .coordinator import ARCoordinator
from .entity import ARLightDescription, ARToggleEntity, async_setup_entities
from .modules import LIGHTS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AsusRouter lights."""

    async_setup_entities(config_entry, LIGHTS, ARLight, async_add_entities)


class ARLight(ARToggleEntity, LightEntity):
    """AsusRouter light."""

    entity_description: ARLightDescription

    def __init__(
        self,
        coordinator: ARCoordinator[Any],
        description: ARLightDescription,
        mac: MacAddress,
    ) -> None:
        """Initialize the light with the color mode it supports."""

        super().__init__(coordinator, description, mac)

        mode = ColorMode.ONOFF if description.rgb_fn is None else ColorMode.RGB
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}
        if description.effects:
            self._attr_effect_list = list(description.effects)
            self._attr_supported_features = LightEntityFeature.EFFECT

    @property
    def brightness(self) -> int | None:
        """Return the brightness."""

        brightness_fn = self.entity_description.brightness_fn
        return (
            None if brightness_fn is None else brightness_fn(self._device_data)
        )

    @property
    def effect(self) -> str | None:
        """Return the effect shown."""

        effect_fn = self.entity_description.effect_fn
        return None if effect_fn is None else effect_fn(self._device_data)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color."""

        rgb_fn = self.entity_description.rgb_fn
        return None if rgb_fn is None else rgb_fn(self._device_data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on with the requested settings."""

        turn_on_fn = self.entity_description.turn_on_fn
        if turn_on_fn is None:
            await super().async_turn_on(**kwargs)
            return

        await self._async_run_action(turn_on_fn(kwargs, self._device_data))
