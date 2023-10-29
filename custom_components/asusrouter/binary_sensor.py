"""AsusRouter binary sensor module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    AIMESH,
    ASUSROUTER,
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_HIDE_PASSWORDS,
    DOMAIN,
    MANUFACTURER,
    PASSWORD,
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
    if config_entry.options.get(CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS):
        hide.append(PASSWORD)

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, binary_sensors, ARBinarySensor, hide
    )

    router = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    tracked: set = set()

    @callback
    def update_router():
        """Update the values of the router."""

        add_entities(router, async_add_entities, tracked)

    router.async_on_close(
        async_dispatcher_connect(hass, router.signal_aimesh_new, update_router)
    )

    update_router()


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
        self._attr_unique_id = to_unique_id(f"{router.mac}_{AIMESH}_{node.mac}")
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
