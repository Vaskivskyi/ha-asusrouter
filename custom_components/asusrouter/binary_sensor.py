"""AsusRouter binary sensors."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .compilers import list_sensors_vpn_clients
from .const import (
    CONF_ENABLE_CONTROL,
    DATA_ASUSROUTER,
    DOMAIN,
    KEY_COORDINATOR,
    SENSORS_TYPE_WAN,
)
from .dataclass import ARBinarySensorDescription
from .entity import AREntity
from .router import AsusRouterObj

BINARY_SENSORS = {
    (SENSORS_TYPE_WAN, "status"): ARBinarySensorDescription(
        key="status",
        key_group=SENSORS_TYPE_WAN,
        name="WAN",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "dns": "dns",
            "gateway": "gateway",
            "ip": "ip",
            "ip_type": "ip_type",
            "mask": "mask",
            "private_subnet": "private_subnet",
        },
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter binary sensors."""

    router: AsusRouterObj = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
    entities = []

    if not entry.options[CONF_ENABLE_CONTROL]:
        BINARY_SENSORS.update(list_sensors_vpn_clients(5))

    for sensor_data in router._sensors_coordinator.values():
        coordinator = sensor_data[KEY_COORDINATOR]
        for sensor_description in BINARY_SENSORS:
            try:
                if sensor_description[0] in sensor_data:
                    if (
                        BINARY_SENSORS[sensor_description].key
                        in sensor_data[sensor_description[0]]
                    ):
                        entities.append(
                            ARBinarySensor(
                                coordinator, router, BINARY_SENSORS[sensor_description]
                            )
                        )
            except Exception as ex:
                _LOGGER.warning(ex)

    async_add_entities(entities, True)


class ARBinarySensor(AREntity, BinarySensorEntity):
    """AsusRouter binary sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: ARBinarySensorDescription,
    ) -> None:
        """Initialize AsusRouter binary sensor."""

        super().__init__(coordinator, router, description)

    @property
    def is_on(self) -> bool:
        """Return state."""

        return self.coordinator.data.get(self.entity_description.key)
