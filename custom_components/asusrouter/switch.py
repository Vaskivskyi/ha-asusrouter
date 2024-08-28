"""AsusRouter switch module."""

from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from asusrouter.modules.parental_control import ParentalControlRule, PCRuleType

from .const import (
    ASUSROUTER,
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_HIDE_PASSWORDS,
    DOMAIN,
    ICON_INTERNET_ACCESS_OFF,
    ICON_INTERNET_ACCESS_ON,
    STATIC_SWITCHES,
)
from .dataclass import ARSwitchDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .helpers import to_unique_id
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
    if config_entry.options.get(
        CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS
    ):
        hide.extend(["password", "private_key", "psk"])

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, switches, ARSwitch, hide
    )

    router = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    tracked: set = set()

    @callback
    def update_router():
        """Update the values of the router."""

        add_entities(router, async_add_entities, tracked)

    router.async_on_close(
        async_dispatcher_connect(
            hass, router.signal_pc_rules_new, update_router
        )
    )

    update_router()


@callback
def add_entities(
    router: ARDevice,
    async_add_entities: AddEntitiesCallback,
    tracked: set[str],
) -> None:
    """Add new tracker entities from the router."""

    new_tracked = []

    for mac, rule in router.pc_rules.items():
        if mac in tracked:
            continue

        new_tracked.append(ClientInternetSwitch(router, rule))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


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

        kwargs = (
            self._state_off_args if self._state_off_args is not None else {}
        )

        await self._set_state(
            state=self._state_off,
            expect_modify=self._state_expect_modify,
            **kwargs,
        )


class ClientInternetSwitch(SwitchEntity):
    """Client internet switch."""

    def __init__(
        self,
        router: ARDevice,
        rule: ParentalControlRule,
    ):
        """Initialize client switch."""

        self._router = router
        self._rule = rule
        self._mac = dr.format_mac(rule.mac)
        self._attr_unique_id = to_unique_id(
            f"{router.mac}_{self._mac}_block_internet"
        )
        self._attr_name = f"{rule.name} Block Internet"

        # Assign device info if set up
        if router.create_devices is True:
            self._attr_device_info = self._compile_device_info()

    def _compile_device_info(self) -> DeviceInfo:
        """Compile device info."""

        return DeviceInfo(
            connections={(dr.CONNECTION_NETWORK_MAC, self._mac)},
            default_name=self._rule.name,
            via_device=(DOMAIN, self._router.mac),
        )

    @property
    def is_on(self) -> Optional[bool]:
        """Get the state."""

        match self._rule.type:
            case PCRuleType.BLOCK:
                return True
            case PCRuleType.DISABLE:
                return False
            case _:
                return None

    @property
    def icon(self) -> Optional[str]:
        """Get the icon."""

        if self.is_on:
            return ICON_INTERNET_ACCESS_OFF
        return ICON_INTERNET_ACCESS_ON

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        return {
            "mac": self._mac,
        }

    async def _set_state(
        self,
        state: ParentalControlRule,
        **kwargs: Any,
    ) -> None:
        """Set state."""

        try:
            _LOGGER.debug("Changing PC rule to %s", state)
            result = await self._router.bridge.api.async_set_state(
                state=state, **kwargs
            )
            self._rule = state
            if not result:
                _LOGGER.debug("State was not set!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Unable to set state with an exception: %s", ex)

    async def async_turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn on block."""

        await self._set_state(
            state=ParentalControlRule(
                mac=self._rule.mac,
                name=self._rule.name,
                type=PCRuleType.BLOCK,
            ),
            **kwargs,
        )

    async def async_turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn off block."""

        await self._set_state(
            state=ParentalControlRule(
                mac=self._rule.mac,
                name=self._rule.name,
                type=PCRuleType.DISABLE,
            ),
            **kwargs,
        )

    @callback
    def async_on_demand_update(self) -> None:
        """Update the state."""

        if self._rule.mac in self._router.pc_rules:
            self._rule = self._router.pc_rules[self._rule.mac]
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register state update callback."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_pc_rules_update,
                self.async_on_demand_update,
            )
        )
