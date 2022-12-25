"""AsusRouter binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ENABLE_CONTROL,
    CONF_HIDE_PASSWORDS,
    DEFAULT_HIDE_PASSWORDS,
    PASSWORD,
    STATIC_BINARY_SENSORS as BINARY_SENSORS,
    STATIC_BINARY_SENSORS_OPTIONAL,
)
from .dataclass import ARBinarySensorDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .router import ARDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter binary sensors."""

    hide = list()
    if entry.options.get(CONF_HIDE_PASSWORDS, DEFAULT_HIDE_PASSWORDS):
        hide.append(PASSWORD)

    if not entry.options[CONF_ENABLE_CONTROL]:
        BINARY_SENSORS.update(STATIC_BINARY_SENSORS_OPTIONAL)

    await async_setup_ar_entry(
        hass, entry, async_add_entities, BINARY_SENSORS, ARBinarySensor, hide
    )


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
