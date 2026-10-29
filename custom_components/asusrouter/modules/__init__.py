"""AsusRouter feature modules."""

from __future__ import annotations

from ..entity import (
    ARBinarySensorDescription,
    ARButtonDescription,
    AREntityDescription,
    ARLightDescription,
    ARSensorDescription,
    ARSwitchDescription,
)
from . import (
    aimesh,
    clock,
    ddns,
    led,
    network,
    ports,
    service,
    sysinfo,
    system_status,
    temperature,
    wan,
    wifi,
)

BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    *aimesh.BINARY_SENSORS,
    *ddns.BINARY_SENSORS,
    *network.BINARY_SENSORS,
    *wan.BINARY_SENSORS,
)
BUTTONS: tuple[ARButtonDescription, ...] = (*service.BUTTONS,)
LIGHTS: tuple[ARLightDescription, ...] = (*led.LIGHTS,)
SENSORS: tuple[ARSensorDescription, ...] = (
    *aimesh.SENSORS,
    *clock.SENSORS,
    *ports.SENSORS,
    *sysinfo.SENSORS,
    *system_status.SENSORS,
    *temperature.SENSORS,
    *wan.SENSORS,
)
SWITCHES: tuple[ARSwitchDescription, ...] = (
    *network.SWITCHES,
    *wifi.SWITCHES,
)

# Every entity description, defines the coordinators to set up
DESCRIPTIONS: tuple[AREntityDescription, ...] = (
    *BINARY_SENSORS,
    *BUTTONS,
    *LIGHTS,
    *SENSORS,
    *SWITCHES,
)
