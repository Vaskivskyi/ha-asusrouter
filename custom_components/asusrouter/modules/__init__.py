"""AsusRouter feature modules."""

from __future__ import annotations

from ..entity import (
    ARBinarySensorDescription,
    AREntityDescription,
    ARSensorDescription,
)
from . import aimesh, system_status, temperature

BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    *aimesh.BINARY_SENSORS,
)
SENSORS: tuple[ARSensorDescription, ...] = (
    *aimesh.SENSORS,
    *system_status.SENSORS,
    *temperature.SENSORS,
)

# Every entity description, defines the coordinators to set up
DESCRIPTIONS: tuple[AREntityDescription, ...] = (*BINARY_SENSORS, *SENSORS)
