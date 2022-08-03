"""AsusRouter sensors."""

from __future__ import annotations

from numbers import Real

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DATA_RATE_MEGABITS_PER_SECOND, PERCENTAGE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .compilers import list_sensors_network
from .const import (
    CONF_INTERFACES,
    CONF_UNITS_SPEED,
    CONF_UNITS_TRAFFIC,
    SENSORS_TYPE_CPU,
    SENSORS_TYPE_DEVICES,
    SENSORS_TYPE_MISC,
    SENSORS_TYPE_PORTS,
    SENSORS_TYPE_RAM,
    SENSORS_TYPE_SYSINFO,
    SENSORS_TYPE_TEMPERATURE,
    SENSORS_TYPE_WAN,
)
from .dataclass import ARSensorDescription
from .entity import AREntity, async_setup_ar_entry
from .router import AsusRouterObj

SENSORS = {
    (SENSORS_TYPE_DEVICES, "number"): ARSensorDescription(
        key="number",
        key_group=SENSORS_TYPE_DEVICES,
        name="Connected Devices",
        icon="mdi:router-network",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        extra_state_attributes={
            "devices": "devices",
        },
    ),
    (SENSORS_TYPE_MISC, "boottime"): ARSensorDescription(
        key="boottime",
        key_group=SENSORS_TYPE_MISC,
        name="Boot Time",
        icon="mdi:restart",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_CPU, "total"): ARSensorDescription(
        key="total",
        key_group=SENSORS_TYPE_CPU,
        name="CPU",
        icon="mdi:cpu-32-bit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "core_1": "core_1",
            "core_2": "core_2",
            "core_3": "core_3",
            "core_4": "core_4",
            "core_5": "core_5",
            "core_6": "core_6",
            "core_7": "core_7",
            "core_8": "core_8",
        },
    ),
    (SENSORS_TYPE_RAM, "usage"): ARSensorDescription(
        key="usage",
        key_group=SENSORS_TYPE_RAM,
        name="RAM",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        precision=2,
        extra_state_attributes={
            "free": "free",
            "total": "total",
            "used": "used",
        },
    ),
    (SENSORS_TYPE_PORTS, "WAN_total"): ARSensorDescription(
        key="WAN_total",
        key_group=SENSORS_TYPE_PORTS,
        name="WAN Speed",
        icon="mdi:ethernet-cable",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_RATE_MEGABITS_PER_SECOND,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "WAN_0": "wan_0",
            "WAN_1": "wan_1",
            "WAN_2": "wan_2",
            "WAN_3": "wan_3",
        },
    ),
    (SENSORS_TYPE_PORTS, "LAN_total"): ARSensorDescription(
        key="LAN_total",
        key_group=SENSORS_TYPE_PORTS,
        name="LAN Speed",
        icon="mdi:ethernet-cable",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DATA_RATE_MEGABITS_PER_SECOND,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "LAN_1": "lan_1",
            "LAN_2": "lan_2",
            "LAN_3": "lan_3",
            "LAN_4": "lan_4",
            "LAN_5": "lan_5",
            "LAN_6": "lan_6",
            "LAN_7": "lan_7",
            "LAN_8": "lan_8",
        },
    ),
    (SENSORS_TYPE_WAN, "ip"): ARSensorDescription(
        key="ip",
        key_group=SENSORS_TYPE_WAN,
        name="WAN IP",
        icon="mdi:ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        extra_state_attributes={
            "dns": "dns",
            "gateway": "gateway",
            "ip_type": "ip_type",
            "mask": "mask",
            "private_subnet": "private_subnet",
        },
    ),
    (SENSORS_TYPE_TEMPERATURE, "cpu"): ARSensorDescription(
        key="cpu",
        key_group=SENSORS_TYPE_TEMPERATURE,
        name="Temperature CPU",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_TEMPERATURE, "2ghz"): ARSensorDescription(
        key="2ghz",
        key_group=SENSORS_TYPE_TEMPERATURE,
        name="Temperature 2.4 GHz",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_TEMPERATURE, "5ghz"): ARSensorDescription(
        key="5ghz",
        key_group=SENSORS_TYPE_TEMPERATURE,
        name="Temperature 5 GHz",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=TEMP_CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_SYSINFO, "load_avg_1"): ARSensorDescription(
        key="load_avg_1",
        key_group=SENSORS_TYPE_SYSINFO,
        name="Load Average (1 min)",
        icon="mdi:cpu-32-bit",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_SYSINFO, "load_avg_5"): ARSensorDescription(
        key="load_avg_5",
        key_group=SENSORS_TYPE_SYSINFO,
        name="Load Average (5 min)",
        icon="mdi:cpu-32-bit",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    (SENSORS_TYPE_SYSINFO, "load_avg_15"): ARSensorDescription(
        key="load_avg_15",
        key_group=SENSORS_TYPE_SYSINFO,
        name="Load Average (15 min)",
        icon="mdi:cpu-32-bit",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter sensors."""

    SENSORS.update(
        list_sensors_network(
            entry.options[CONF_INTERFACES],
            entry.options[CONF_UNITS_SPEED],
            entry.options[CONF_UNITS_TRAFFIC],
        )
    )

    await async_setup_ar_entry(hass, entry, async_add_entities, SENSORS, ARSensor)


class ARSensor(AREntity, SensorEntity):
    """AsusRouter sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: ARSensorDescription,
    ) -> None:
        """Initialize AsusRouter sensor."""

        super().__init__(coordinator, router, description)

    @property
    def native_value(
        self,
    ) -> float | str | None:
        """Return state."""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        if state is not None and description.factor and isinstance(state, Real):
            return round(state / description.factor, description.precision)
        return state
