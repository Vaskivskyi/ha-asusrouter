"""AsusRouter sensors."""

from __future__ import annotations

import logging
from numbers import Real

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .compilers import list_sensors_network
from .const import (
    CONF_INTERFACES,
    CONF_UNITS_SPEED,
    CONF_UNITS_TRAFFIC,
    STATIC_SENSORS as SENSORS,
)
from .dataclass import ARSensorDescription
from .entity import AREntity, async_setup_ar_entry
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter sensors."""

    interfaces = entry.options[CONF_INTERFACES]
    if len(interfaces) > 0:
        _LOGGER.debug(f"Interfaces selected: {interfaces}. Initializing sensors")
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
        router: ARDevice,
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
