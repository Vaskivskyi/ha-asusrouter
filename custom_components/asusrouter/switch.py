"""AsusRouter switch module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_DEFAULT_HIDE_PASSWORDS, CONF_HIDE_PASSWORDS, STATIC_SWITCHES
from .dataclass import ARSwitchDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter switches."""

    switches = STATIC_SWITCHES.copy()

    hide = []
    if config_entry.options.get(CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS):
        hide.extend(["password", "private_key", "psk"])

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

        # State on
        self._state_on = description.state_on
        self._state_on_args = description.state_on_args
        # State off
        self._state_off = description.state_off
        self._state_off_args = description.state_off_args
        # Expect modify
        self._state_expect_modify = description.state_expect_modify

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on switch."""

        kwargs = self._state_on_args if self._state_on_args is not None else {}

        await self._set_state(
            state=self._state_on,
            expect_modify=self._state_expect_modify,
            **kwargs,
        )

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off switch."""

        kwargs = self._state_off_args if self._state_off_args is not None else {}

        await self._set_state(
            state=self._state_off,
            expect_modify=self._state_expect_modify,
            **kwargs,
        )
