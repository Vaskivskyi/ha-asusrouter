"""AsusRouter feature modules."""

from __future__ import annotations

from ..entity import (
    ARBinarySensorDescription,
    ARButtonDescription,
    AREntityDescription,
    ARLightDescription,
    ARSensorDescription,
)
from . import aimesh, clock, led, service, sysinfo, system_status, temperature

BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    *aimesh.BINARY_SENSORS,
)
BUTTONS: tuple[ARButtonDescription, ...] = (*service.BUTTONS,)
LIGHTS: tuple[ARLightDescription, ...] = (*led.LIGHTS,)
SENSORS: tuple[ARSensorDescription, ...] = (
    *aimesh.SENSORS,
    *clock.SENSORS,
    *sysinfo.SENSORS,
    *system_status.SENSORS,
    *temperature.SENSORS,
)

# Every entity description, defines the coordinators to set up
DESCRIPTIONS: tuple[AREntityDescription, ...] = (
    *BINARY_SENSORS,
    *BUTTONS,
    *LIGHTS,
    *SENSORS,
)
