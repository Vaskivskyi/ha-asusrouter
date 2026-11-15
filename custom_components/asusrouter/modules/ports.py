"""AsusRouter ports module."""

from __future__ import annotations

from datetime import timedelta
import re
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

# Labels of the USB ports as the device reports them, U1 and up
_USB_LABEL = re.compile(r"U\d+")


def _get_ports(
    data: ARPortsData, *, usb: bool
) -> dict[str, dict[ARPortProperty, Any]]:
    """Get the Ethernet or the USB ports by their label."""

    ports: dict[str, dict[ARPortProperty, Any]] = {}
    for port in data.ports:
        name = port.get(ARPortProperty.NATIVE_NAME)
        if isinstance(name, str) and bool(_USB_LABEL.fullmatch(name)) is usb:
            ports[name] = port
    return ports


def _get_rate(
    port: dict[ARPortProperty, Any] | None, key: ARPortProperty
) -> int | None:
    """Get a rate of a port in Mbit/s."""

    rate = None if port is None else port.get(key)
    if not isinstance(rate, ARPortSpeed | ARUSBSpeed) or rate.value < 0:
        return None

    return rate.value


def _get_attributes(port: dict[ARPortProperty, Any]) -> dict[str, Any]:
    """Get the attributes of a port."""

    return {
        "capabilities": sorted(
            capability.name.lower()
            for capability in port.get(ARPortProperty.CAPABILITIES, [])
        ),
        "max_rate": _get_rate(port, ARPortProperty.MAX_RATE),
        "role": to_value(port.get(ARPortProperty.ROLE), ARPortType),
    }


def _get_port_sensor(*, usb: bool) -> ARSensorDescription:
    """Get the description of the sensors of the Ethernet or USB ports."""

    return ARSensorDescription(
        key="usb_port" if usb else "port",
        translation_key="usb_port" if usb else "port",
        source=ARPortsSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        # The router reports the ports of every node it serves
        node_source=lambda _: ARPortsSourceUniversal,
        keys_fn=lambda data: _get_ports(data, usb=usb),
        item_fn=lambda data, name: _get_ports(data, usb=usb).get(name),
        unique_id_fn=lambda name: f"Port {name}",
        placeholders_fn=lambda name: {"port": name},
        # A port that is down reports 0
        value_fn=lambda port: _get_rate(port, ARPortProperty.LINK_RATE),
        attributes_fn=_get_attributes,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    _get_port_sensor(usb=False),
    _get_port_sensor(usb=True),
)
