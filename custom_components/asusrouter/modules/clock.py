"""AsusRouter clock module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.clock import ARClockField, ARClockSourceUniversal
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTime

from ..entity import ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)

# The device reports its clock, not keyed by its MAC
_CLOCK: dict[str, Any] = {
    "source": ARClockSourceUniversal,
    "update_interval": UPDATE_INTERVAL,
    "data_fn": lambda data: data,
    "entity_category": EntityCategory.DIAGNOSTIC,
    "entity_registry_enabled_default": False,
}

SENSORS: tuple[ARSensorDescription, ...] = (
    ARSensorDescription(
        key="boot_time",
        translation_key="boot_time",
        unique_id_name="Boot Time",
        value_fn=lambda data: data.get(ARClockField.BOOTTIME),
        device_class=SensorDeviceClass.TIMESTAMP,
        **_CLOCK,
    ),
    ARSensorDescription(
        key="uptime",
        translation_key="uptime",
        unique_id_name="Uptime",
        value_fn=lambda data: data.get(ARClockField.UPTIME),
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        **_CLOCK,
    ),
)
