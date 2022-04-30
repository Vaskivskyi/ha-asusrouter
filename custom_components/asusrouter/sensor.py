"""ASUS Router sensors"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from dataclasses import dataclass
from html import entities
from numbers import Real
from collections.abc import Callable, Mapping
from typing import Any, Final, cast
from xml.dom.minidom import Entity
from datetime import datetime


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DATA_GIGABYTES,
    DATA_RATE_MEGABITS_PER_SECOND,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, DeviceInfo, EntityDescription, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DATA_ASUSROUTER,
    DOMAIN,
)

from .router import KEY_COORDINATOR, KEY_SENSORS_CPU, KEY_SENSORS_MISC, KEY_SENSORS_RAM, KEY_SENSORS_NETWORK_STAT, KEY_SENSORS_DEVICES, AsusRouterObj


@dataclass
class AsusRouterEntityDescription(EntityDescription):
    """"""

    key_group: Callable[[dict], str] | None = None
    value: Callable[[Any], Any] = lambda val: val
    factor: int | None = None
    precision: int = 3
    extra_state_attributes: dict[str, AsusRouterAttributeDescription] | None = None


@dataclass
class AsusRouterSensorDescription(AsusRouterEntityDescription, SensorEntityDescription):
    """Describe AsusRouter sensor"""


@dataclass
class AsusRouterAttributeDescription(AsusRouterEntityDescription, SensorEntityDescription):
    """Describe AsusRouter attribute"""


DEFAULT_PREFIX = "AsusRouter"


SENSORS = {
    ("devices", "number"): AsusRouterSensorDescription(
        key = "number",
        key_group = KEY_SENSORS_DEVICES,
        name = "Connected Devices",
        icon = "mdi:router-network",
        state_class = SensorStateClass.MEASUREMENT,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = True,
    ),
    ("misc", "boottime"): AsusRouterSensorDescription(
        key = "boottime",
        key_group = KEY_SENSORS_MISC,
        name = "Boot Time",
        icon = "mdi:restart",
        device_class = SensorDeviceClass.TIMESTAMP,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
    ),
    ("cpu", "total"): AsusRouterSensorDescription(
        key = "total",
        key_group = KEY_SENSORS_CPU,
        name = "CPU",
        icon = "mdi:cpu-32-bit",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = PERCENTAGE,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "core_1": "Core 1",
            "core_2": "Core 2",
            "core_3": "Core 3",
            "core_4": "Core 4",
            "core_5": "Core 5",
            "core_6": "Core 6",
            "core_7": "Core 7",
            "core_8": "Core 8",
        },
    ),
    ("ram", "usage"): AsusRouterSensorDescription(
        key = "usage",
        key_group = KEY_SENSORS_RAM,
        name = "RAM",
        icon = "mdi:memory",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = PERCENTAGE,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
        precision = 2,
        extra_state_attributes = {
            "total": "Total",
            "free": "Free",
            "used": "Used",
        },
    ),
    ("network_stat", "WAN_rx"): AsusRouterSensorDescription(
        key = "{}_{}".format("WAN", "rx"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "WAN Download",
        icon = "mdi:download-outline",
        state_class = SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement = DATA_GIGABYTES,
        factor = 1073741824,
        entity_registry_enabled_default = True,
        extra_state_attributes = {
            "WAN_rx": "Bytes",
        }
    ),
    ("network_stat", "WAN_tx"): AsusRouterSensorDescription(
        key = "{}_{}".format("WAN", "tx"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "WAN Upload",
        icon = "mdi:upload-outline",
        state_class = SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement = DATA_GIGABYTES,
        factor = 1073741824,
        entity_registry_enabled_default = True,
        extra_state_attributes = {
            "WAN_tx": "Bytes",
        }
    ),
    ("network_stat", "WAN_rx_speed"): AsusRouterSensorDescription(
        key = "{}_{}".format("WAN", "rx_speed"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "WAN Download Speed",
        icon = "mdi:download-network-outline",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = DATA_RATE_MEGABITS_PER_SECOND,
        factor = 1048576,
        entity_registry_enabled_default = True,
        extra_state_attributes = {
            "WAN_rx_speed": "bits/s",
        }
    ),
    ("network_stat", "WAN_tx_speed"): AsusRouterSensorDescription(
        key = "{}_{}".format("WAN", "tx_speed"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "WAN Upload Speed",
        icon = "mdi:upload-network-outline",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = DATA_RATE_MEGABITS_PER_SECOND,
        factor = 1048576,
        entity_registry_enabled_default = True,
        extra_state_attributes = {
            "WAN_tx_speed": "bits/s",
        }
    ),
    ("network_stat", "USB_rx"): AsusRouterSensorDescription(
        key = "{}_{}".format("USB", "rx"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "USB Download",
        icon = "mdi:download-outline",
        state_class = SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement = DATA_GIGABYTES,
        factor = 1073741824,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "USB_rx": "Bytes",
        }
    ),
    ("network_stat", "USB_tx"): AsusRouterSensorDescription(
        key = "{}_{}".format("USB", "tx"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "USB Upload",
        icon = "mdi:upload-outline",
        state_class = SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement = DATA_GIGABYTES,
        factor = 1073741824,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "USB_tx": "Bytes",
        }
    ),
    ("network_stat", "USB_rx_speed"): AsusRouterSensorDescription(
        key = "{}_{}".format("USB", "rx_speed"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "USB Download Speed",
        icon = "mdi:download-network-outline",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = DATA_RATE_MEGABITS_PER_SECOND,
        factor = 1048576,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "USB_rx_speed": "bits/s",
        }
    ),
    ("network_stat", "USB_tx_speed"): AsusRouterSensorDescription(
        key = "{}_{}".format("USB", "tx_speed"),
        key_group = KEY_SENSORS_NETWORK_STAT,
        name = "USB Upload Speed",
        icon = "mdi:upload-network-outline",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = DATA_RATE_MEGABITS_PER_SECOND,
        factor = 1048576,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "USB_tx_speed": "bits/s",
        }
    ),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Setup sensors"""

    router: AsusRouterObj = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
    entities = []

    for sensor_data in router._sensors_coordinator.values():
        coordinator = sensor_data[KEY_COORDINATOR]
        for sensor_description in SENSORS:
            try:
                if sensor_description[0] in sensor_data:
                    if SENSORS[sensor_description].key in sensor_data[sensor_description[0]]:
                        entities.append(AsusRouterSensor(coordinator, router, SENSORS[sensor_description]))
            except Exception as ex:
                _LOGGER.warning(ex)

    async_add_entities(entities, True)


class AsusRouterSensor(CoordinatorEntity, SensorEntity):
    """AsusRouter sensor"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: AsusRouterSensorDescription,
    ) -> None:
        """Initialize AsusRouter sensor"""

        super().__init__(coordinator)
        self.entity_description: AsusRouterSensorDescription = description
        self.router = router
        self.coordinator = coordinator

        self._attr_name = "{} {}".format(router._name, description.name)
        self._attr_unique_id = "{} {}".format(DOMAIN, self.name)
        self._attr_device_info = router.device_info
        self._attr_extra_state_attributes = description.extra_state_attributes


    @property
    def native_value(self) -> float | str | None:
        """Return current state"""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        if (
            state is not None
            and description.factor
            and isinstance(state, Real)
        ):
            return round(state / description.factor, description.precision)
        return state


    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """"""

        description = self.entity_description
        _extra_state_attributes = description.extra_state_attributes
        if _extra_state_attributes is None:
            return {}

        attrs = {}

        for attr in _extra_state_attributes:
            if attr in self.coordinator.data:
                attrs[_extra_state_attributes[attr]] = self.coordinator.data[attr]

        return attrs


class AsusRouterAttribute(CoordinatorEntity, SensorEntity):
    """AsusRouter attribute"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: AsusRouterAttributeDescription,
    ) -> None:
        """Initialize AsusRouter attribute"""

        super().__init__(coordinator)
        self.entity_description: AsusRouterSensorDescription = description
        _LOGGER.debug(self.entity_description)

        self._attr_name = "{}".format(self.entity_description.name)
        self._attr_unique_id = "{} {}".format(DOMAIN, self.name)


    @property
    def native_value(self) -> float | str | None:
        """Return current state"""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        if (
            state is not None
            and description.factor
            and isinstance(state, Real)
        ):
            return round(state / description.factor, description.precision)
        return state


