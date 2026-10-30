"""AsusRouter ports module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.ports import (
    ARPortProperty,
    ARPortsData,
    ARPortSpeed,
    ARPortsSourceUniversal,
    ARPortType,
)
from asusrouter.modules.usb import ARUSBSpeed
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfDataRate

from ..entity import ARSensorDescription
from ..helpers import to_value

UPDATE_INTERVAL = timedelta(seconds=30)

# Port labels as the device reports them, only the present ones get a sensor
_ETHERNET_PORTS = (
    "AI",
    # A 10G port of the legacy firmware endpoint
    "SFP",
    *(f"W{index}" for index in range(4)),
    *(f"L{index}" for index in range(1, 17)),
)
_USB_PORTS = tuple(f"U{index}" for index in range(1, 5))


def _get_port(
    data: ARPortsData, name: str
) -> dict[ARPortProperty, Any] | None:
    """Get a port by its label."""

    return next(
        (
            port
            for port in data.ports
            if port.get(ARPortProperty.NATIVE_NAME) == name
        ),
        None,
    )


def _get_rate(
    port: dict[ARPortProperty, Any] | None, key: ARPortProperty
) -> int | None:
    """Get a rate of a port in Mbit/s."""

    rate = None if port is None else port.get(key)
    if not isinstance(rate, ARPortSpeed | ARUSBSpeed) or rate.value < 0:
        return None

    return rate.value


def _get_attributes(data: ARPortsData, name: str) -> dict[str, Any]:
    """Get the attributes of a port."""

    port = _get_port(data, name) or {}

    return {
        "capabilities": sorted(
            capability.name.lower()
            for capability in port.get(ARPortProperty.CAPABILITIES, [])
        ),
        "max_rate": _get_rate(port, ARPortProperty.MAX_RATE),
        "role": to_value(port.get(ARPortProperty.ROLE), ARPortType),
    }


def _get_port_sensor(name: str, translation_key: str) -> ARSensorDescription:
    """Get the description of the sensor of a port."""

    return ARSensorDescription(
        key=f"port_{name.lower()}",
        translation_key=translation_key,
        translation_placeholders={"port": name},
        source=ARPortsSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=f"Port {name}",
        # The router reports the ports of every node it serves
        node_source=lambda _: ARPortsSourceUniversal,
        # A port that is down reports 0
        value_fn=lambda data: _get_rate(
            _get_port(data, name), ARPortProperty.LINK_RATE
        ),
        attributes_fn=lambda data: _get_attributes(data, name),
        exists_fn=lambda data: _get_port(data, name) is not None,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    *(_get_port_sensor(name, "port") for name in _ETHERNET_PORTS),
    *(_get_port_sensor(name, "usb_port") for name in _USB_PORTS),
)
