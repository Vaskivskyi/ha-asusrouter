"""AsusRouter button module."""

from __future__ import annotations

import logging
from typing import Any

from asusrouter.modules.state import AsusState
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import ARClient
from .const import (
    ASUSROUTER,
    CONF_MODE,
    DOMAIN,
    ICON_IP,
    IP,
    MAC,
    ROUTER,
    STATIC_BUTTONS,
    STATIC_BUTTONS_OPTIONAL,
)
from .dataclass import ARButtonDescription
from .helpers import to_unique_id
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter buttons."""

    buttons = STATIC_BUTTONS.copy()

    router: ARDevice = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    entities = []

    if config_entry.options.get(CONF_MODE) == ROUTER:
        buttons.extend(STATIC_BUTTONS_OPTIONAL)

    for button in buttons:
        try:
            entities.append(ARButton(router, button))
        except Exception as ex:  # noqa: BLE001
            _LOGGER.warning(ex)

    async_add_entities(entities)

    tracked: set = set()

    @callback
    def update_router() -> None:
        """Add static DHCP client buttons."""

        add_static_dhcp_entities(router, async_add_entities, tracked)

    router.async_on_close(
        async_dispatcher_connect(hass, router.signal_device_new, update_router)
    )

    update_router()


def _client_entity_enabled(router: ARDevice, client: ARClient) -> bool:
    """Return whether client-scoped entities should be created."""

    return router.create_devices is True or (
        router.client_device is True and client.device is True
    )


@callback
def add_static_dhcp_entities(
    router: ARDevice,
    async_add_entities: AddEntitiesCallback,
    tracked: set[str],
) -> None:
    """Add static DHCP buttons for known client devices."""

    if router.mode != ROUTER:
        return

    new_tracked = []
    for mac, client in router.devices.items():
        if mac in tracked or not _client_entity_enabled(router, client):
            continue

        new_tracked.append(ClientStaticDHCPReserveButton(router, client))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


class ARButton(ButtonEntity):
    """AsusRouter button."""

    def __init__(
        self,
        router: ARDevice,
        description: ARButtonDescription,
    ) -> None:
        """Initialize AsusRouter button."""

        self.router = router
        self.api = router.bridge.api

        self._attr_device_info = router.device_info
        self._attr_name = f"{router._conf_name} {description.name}"
        self._attr_unique_id = to_unique_id(f"{router.mac}_{description.name}")
        self._attr_capability_attributes = description.capabilities

        self._state = description.state
        self._state_args = description.state_args
        self._state_expect_modify = description.state_expect_modify

        if description.icon:
            self._attr_icon = description.icon

    async def async_press(
        self,
        **kwargs: Any,
    ) -> None:
        """Press button."""

        kwargs = self._state_args if self._state_args is not None else {}

        await self._set_state(
            state=self._state,
            expect_modify=self._state_expect_modify,
            **kwargs,
        )

    async def _set_state(
        self,
        state: AsusState,
        expect_modify: bool = False,
        **kwargs: Any,
    ) -> None:
        """Set switch state."""

        try:
            _LOGGER.debug("Pressing %s", state)
            result = await self.api.async_set_state(
                state=state, expect_modify=expect_modify, **kwargs
            )
            if not result:
                _LOGGER.debug("Didn't manage to press %s", state)
        except Exception as ex:  # noqa: BLE001
            _LOGGER.error("Pressing %s caused an exception: %s", state, ex)


class ClientStaticDHCPReserveButton(ButtonEntity):
    """Button to reserve a client's current IP address."""

    _attr_icon = ICON_IP

    def __init__(
        self,
        router: ARDevice,
        client: ARClient,
    ) -> None:
        """Initialize the reserve current IP button."""

        self._router = router
        self._client = client
        self._mac = dr.format_mac(client.mac_address)
        self._attr_unique_id = to_unique_id(
            f"{router.mac}_{self._mac}_reserve_current_ip"
        )
        self._attr_name = (
            f"{client.name or client.mac_address} Reserve Current IP"
        )
        self._attr_device_info = self._compile_device_info()

    def _compile_device_info(self) -> DeviceInfo:
        """Compile client device info."""

        return DeviceInfo(
            connections={(dr.CONNECTION_NETWORK_MAC, self._mac)},
            default_name=self._client.name or self._mac,
            via_device=(DOMAIN, self._router.mac),
        )

    @property
    def available(self) -> bool:
        """Return if the button can safely reserve the current IP."""

        current_ip = self._client.ip_address
        if current_ip is None:
            return False

        if self._router.static_dhcp_ip_conflict(self._mac, current_ip):
            return False

        reservation = self._router.static_dhcp_reservation(self._mac)
        return reservation is None or reservation[IP] == current_ip

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return button attributes."""

        reservation = self._router.static_dhcp_reservation(self._mac)
        return {
            MAC: self._mac,
            "current_ip": self._client.ip_address,
            "reserved_ip": reservation[IP] if reservation else None,
        }

    async def async_press(
        self,
        **kwargs: Any,
    ) -> None:
        """Reserve the current IP address."""

        if self._client.ip_address is None:
            return

        await self._router.async_reserve_current_ip(
            mac=self._mac,
            ip=self._client.ip_address,
            hostname=self._client.name,
        )
        self.async_write_ha_state()

    @callback
    def async_on_demand_update(self) -> None:
        """Update the client button."""

        if self._mac in self._router.devices:
            self._client = self._router.devices[self._mac]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register state update callbacks."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_device_update,
                self.async_on_demand_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_static_dhcp_update,
                self.async_on_demand_update,
            )
        )
