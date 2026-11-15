"""AsusRouter feature modules."""

from __future__ import annotations

from ..entity import (
    ARBinarySensorDescription,
    ARButtonDescription,
    AREntityDescription,
    ARLightDescription,
    ARSensorDescription,
    ARSwitchDescription,
    ARTrackerDescription,
    ARUpdateDescription,
)
from . import (
    aimesh,
    aura,
    clients,
    clock,
    ddns,
    dsl,
    firmware,
    led,
    network,
    parental_control,
    port_forwarding,
    ports,
    service,
    sysinfo,
    system_status,
    temperature,
    vpn,
    wan,
    wifi,
)

BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    *aimesh.BINARY_SENSORS,
    *ddns.BINARY_SENSORS,
    *network.BINARY_SENSORS,
    *wan.BINARY_SENSORS,
)
BUTTONS: tuple[ARButtonDescription, ...] = (
    *clients.BUTTONS,
    *service.BUTTONS,
)
LIGHTS: tuple[ARLightDescription, ...] = (*aura.LIGHTS, *led.LIGHTS)
SENSORS: tuple[ARSensorDescription, ...] = (
    *aimesh.SENSORS,
    *clients.SENSORS,
    *clock.SENSORS,
    *dsl.SENSORS,
    *ports.SENSORS,
    *sysinfo.SENSORS,
    *system_status.SENSORS,
    *temperature.SENSORS,
    *vpn.SENSORS,
    *wan.SENSORS,
)
SWITCHES: tuple[ARSwitchDescription, ...] = (
    *aura.SWITCHES,
    *network.SWITCHES,
    *parental_control.SWITCHES,
    *port_forwarding.SWITCHES,
    *vpn.SWITCHES,
    *wifi.SWITCHES,
)
TRACKERS: tuple[ARTrackerDescription, ...] = (*clients.TRACKERS,)
UPDATES: tuple[ARUpdateDescription, ...] = (
    *aimesh.UPDATES,
    *firmware.UPDATES,
)

# Every entity description, defines the coordinators to set up
DESCRIPTIONS: tuple[AREntityDescription, ...] = (
    *BINARY_SENSORS,
    *BUTTONS,
    *LIGHTS,
    *SENSORS,
    *SWITCHES,
    *TRACKERS,
    *UPDATES,
)
