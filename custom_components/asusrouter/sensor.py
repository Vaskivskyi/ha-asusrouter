"""AsusRouter sensor module."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .compilers import list_sensors_network
from .const import CONF_INTERFACES, STATIC_SENSORS
from .dataclass import ARSensorDescription
from .entity import AREntity, async_setup_ar_entry
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter sensors."""

    sensors = STATIC_SENSORS.copy()

    interfaces = config_entry.options.get(CONF_INTERFACES, [])
    if len(interfaces) > 0:
        _LOGGER.debug("Interfaces selected: %s. Initializing sensors", interfaces)
        sensors.extend(
            list_sensors_network(
                config_entry.options[CONF_INTERFACES],
            )
        )

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, sensors, ARSensor
    )


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
        self.entity_description: ARSensorDescription = description

    @property
    def native_value(
        self,
    ) -> float | str | None:
        """Return state."""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        return state
