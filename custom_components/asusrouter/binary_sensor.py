"""AsusRouter binary sensor module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import ARClient
from .const import (
    AIMESH,
    ASUSROUTER,
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_HIDE_PASSWORDS,
    DNS,
    DOMAIN,
    IP,
    MAC,
    MANUFACTURER,
    PASSWORD,
    ROUTER,
    STATIC_BINARY_SENSORS,
)
from .dataclass import ARBinarySensorDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .helpers import to_unique_id
from .router import AiMeshNode, ARDevice


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter binary sensors."""

    binary_sensors = STATIC_BINARY_SENSORS.copy()

    hide = []
    if config_entry.options.get(
        CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS
    ):
        hide.append(PASSWORD)

    await async_setup_ar_entry(
        hass,
        config_entry,
        async_add_entities,
        binary_sensors,
        ARBinarySensor,
        hide,
    )

    router = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    tracked: set = set()
    client_tracked: set = set()

    @callback
    def update_router() -> None:
        """Update the values of the router."""

        add_entities(router, async_add_entities, tracked)

    @callback
    def update_clients() -> None:
        """Add static DHCP client sensors."""

        add_static_dhcp_entities(router, async_add_entities, client_tracked)

    router.async_on_close(
        async_dispatcher_connect(hass, router.signal_aimesh_new, update_router)
    )
    router.async_on_close(
        async_dispatcher_connect(
            hass, router.signal_device_new, update_clients
        )
    )

    update_router()
    update_clients()


class ARBinarySensor(ARBinaryEntity, BinarySensorEntity):
    """AsusRouter binary sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARBinarySensorDescription,
    ) -> None:
        """Initialize AsusRouter binary sensor."""

        super().__init__(coordinator, router, description)
        self.entity_description: ARBinarySensorDescription = description


@callback
def add_entities(
    router: ARDevice,
    async_add_entities: AddEntitiesCallback,
    tracked: set[str],
) -> None:
    """Add new tracker entities from the router."""

    new_tracked = []

    for mac, node in router.aimesh.items():
        if mac in tracked:
            continue

        new_tracked.append(AMBinarySensor(router, node))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


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
    """Add static DHCP reservation sensors for known client devices."""

    if router.mode != ROUTER:
        return

    new_tracked = []
    for mac, client in router.devices.items():
        if mac in tracked or not _client_entity_enabled(router, client):
            continue

        new_tracked.append(ClientStaticDHCPReservationSensor(router, client))
        tracked.add(mac)

    if new_tracked:
        async_add_entities(new_tracked)


class AMBinarySensor(BinarySensorEntity):
    """AsusRouter AiMesh sensor."""

    def __init__(
        self,
        router: ARDevice,
        node: AiMeshNode,
    ) -> None:
        """Initialize AsusRouter AiMesh sensor."""

        self._router = router
        self._node = node
        self._attr_unique_id = to_unique_id(
            f"{router.mac}_{AIMESH}_{node.mac}"
        )
        self._attr_name = f"AiMesh {node.native.model} ({node.native.mac})"

    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self._node.native.status

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Device class."""

        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        return dict(sorted(self._node.extra_state_attributes.items())) or {}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""

        device_info: DeviceInfo = DeviceInfo(
            identifiers={
                (DOMAIN, self._node.mac),
            },
            name=self._node.native.model,
            model=self._node.native.model,
            manufacturer=MANUFACTURER,
            sw_version=self._node.native.fw,
        )
        if self._router.mac != self._node.mac:
            device_info = DeviceInfo(
                identifiers={
                    (DOMAIN, self._node.mac),
                },
                name=self._node.native.model,
                model=self._node.native.model,
                manufacturer=MANUFACTURER,
                sw_version=self._node.native.fw,
                via_device=(DOMAIN, self._router.mac),
            )

        return device_info

    @callback
    def async_on_demand_update(self) -> None:
        """Update the state."""

        if self._node.mac in self._router.aimesh:
            self._node = self._router.aimesh[self._node.mac]
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register state update callback."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_aimesh_update,
                self.async_on_demand_update,
            )
        )


class ClientStaticDHCPReservationSensor(BinarySensorEntity):
    """Client static DHCP reservation sensor."""

    _attr_icon = "mdi:ip-network-outline"

    def __init__(
        self,
        router: ARDevice,
        client: ARClient,
    ) -> None:
        """Initialize static DHCP reservation sensor."""

        self._router = router
        self._client = client
        self._mac = dr.format_mac(client.mac_address)
        self._attr_unique_id = to_unique_id(
            f"{router.mac}_{self._mac}_dhcp_reservation"
        )
        self._attr_name = (
            f"{client.name or client.mac_address} DHCP Reservation"
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
    def is_on(self) -> bool:
        """Return whether the client has a static DHCP reservation."""

        return self._router.static_dhcp_reservation(self._mac) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return reservation details."""

        reservation = self._router.static_dhcp_reservation(self._mac)
        reserved_ip = reservation[IP] if reservation else None
        current_ip = self._client.ip_address

        return {
            MAC: self._mac,
            "reserved_ip": reserved_ip,
            "current_ip": current_ip,
            "hostname": reservation["hostname"] if reservation else None,
            DNS: reservation[DNS] if reservation else None,
            "matches_current_ip": (
                reserved_ip is not None and reserved_ip == current_ip
            ),
        }

    @callback
    def async_on_demand_update(self) -> None:
        """Update the client reservation sensor."""

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
