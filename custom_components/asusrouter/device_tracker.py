"""AsusRouter device trackers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SOURCE_TYPE_ROUTER
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ASUSROUTER, DEFAULT_DEVICE_NAME, DOMAIN
from .router import AsusRouterDevInfo, AsusRouterObj


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for AsusRouter component."""

    router = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
    tracked: set = set()

    @callback
    def update_router():
        """Update the values of the router."""

        add_entities(router, async_add_entities, tracked)

    router.async_on_close(
        async_dispatcher_connect(hass, router.signal_device_new, update_router)
    )

    update_router()


@callback
def add_entities(
    router: AsusRouterObj,
    async_add_entities: AddEntitiesCallback,
    tracked: set[str],
) -> None:
    """Add new tracker entities from the router."""

    new_tracked = []

    for mac, device in router.devices.items():
        if mac in tracked:
            continue

        new_tracked.append(AsusRouterConnectedDevice(router, device))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


class AsusRouterConnectedDevice(ScannerEntity):
    """Connected device class."""

    _attr_should_poll = False

    def __init__(
        self,
        router: AsusRouterObj,
        device: AsusRouterDevInfo,
    ) -> None:
        """Initialize connected device."""

        self._router = router
        self._device = device
        self._attr_unique_id = device.mac
        self._attr_name = device.name or DEFAULT_DEVICE_NAME

    @property
    def source_type(self) -> str:
        """Source type."""

        return SOURCE_TYPE_ROUTER

    @property
    def is_connected(self) -> bool:
        """Device status."""

        return self._device.is_connected

    @property
    def ip_address(self) -> str:
        """Device IP address."""

        return self._device.ip

    @property
    def mac_address(self) -> str:
        """Device MAC address."""

        return self._device.mac

    @property
    def hostname(self) -> str:
        """Device hostname."""

        return self._device.name

    @property
    def icon(self) -> str:
        """Device icon."""

        return "mdi:lan-connect" if self._device.is_connected else "mdi:lan-disconnect"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        _attributes = self._device.extra_state_attributes
        if not _attributes:
            return {}

        attributes = {}

        for attr in _attributes:
            attributes[attr] = _attributes[attr]

        return attributes

    @callback
    def async_on_demand_update(self) -> None:
        """Update the state."""

        self._device = self._router.devices[self._device.mac]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register state update callback."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_device_update,
                self.async_on_demand_update,
            )
        )
