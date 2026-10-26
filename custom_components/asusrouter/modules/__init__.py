"""AsusRouter feature modules."""

from __future__ import annotations

from ..entity import AREntityDescription, ARSensorDescription
from . import system_status

SENSORS: tuple[ARSensorDescription, ...] = (*system_status.SENSORS,)

# Every entity description, defines the coordinators to set up
DESCRIPTIONS: tuple[AREntityDescription, ...] = (*SENSORS,)
