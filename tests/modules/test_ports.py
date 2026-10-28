"""Tests for the ports module."""

from __future__ import annotations

from typing import Any

from asusrouter.modules.ports import (
    ARPortCapability,
    ARPortProperty,
    ARPortsData,
    ARPortSpeed,
    ARPortsSourceUniversal,
    ARPortType,
)
from asusrouter.modules.usb import ARUSBSpeed
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules.ports import SENSORS

MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")


def _get_port(
    name: str, properties: dict[ARPortProperty, Any]
) -> dict[ARPortProperty, Any]:
    """Create a port as the library reports it."""

    return {ARPortProperty.NATIVE_NAME: name, **properties}


DATA = ARPortsData(
    info={},
    ports=[
        _get_port(
            "W0",
            {
                ARPortProperty.LINK_RATE: ARPortSpeed.MBPS_2500,
                ARPortProperty.MAX_RATE: ARPortSpeed.MBPS_10000,
                ARPortProperty.ROLE: ARPortType.WAN,
                ARPortProperty.CAPABILITIES: [
                    ARPortCapability.WAN,
                    ARPortCapability.GAME,
                ],
            },
        ),
        _get_port(
            "L1",
            {
                ARPortProperty.LINK_RATE: ARPortSpeed.DOWN,
                ARPortProperty.MAX_RATE: ARPortSpeed.MBPS_1000,
                ARPortProperty.ROLE: ARPortType.LAN,
            },
        ),
        _get_port(
            "L2",
            {
                ARPortProperty.LINK_RATE: ARPortSpeed.UNKNOWN,
                ARPortProperty.ROLE: ARPortType.UNKNOWN,
            },
        ),
        _get_port(
            "U1",
            {
                ARPortProperty.LINK_RATE: ARUSBSpeed.USB3,
                ARPortProperty.MAX_RATE: ARUSBSpeed.USB3,
                ARPortProperty.ROLE: ARPortType.USB,
            },
        ),
    ],
)

DESCRIPTIONS: dict[str, ARSensorDescription] = {
    description.key: description for description in SENSORS
}


@pytest.mark.parametrize(
    ("name", "translation_key", "value", "attributes"),
    [
        (
            "W0",
            "port",
            2500,
            {
                "capabilities": ["game", "wan"],
                "max_rate": 10000,
                "role": "wan",
            },
        ),
        # A port that is down
        (
            "L1",
            "port",
            0,
            {"capabilities": [], "max_rate": 1000, "role": "lan"},
        ),
        # Nothing known about the port
        (
            "L2",
            "port",
            None,
            {"capabilities": [], "max_rate": None, "role": None},
        ),
        (
            "U1",
            "usb_port",
            5000,
            {"capabilities": [], "max_rate": 5000, "role": "usb"},
        ),
    ],
)
def test_port(
    name: str,
    translation_key: str,
    value: int | None,
    attributes: dict[str, Any],
) -> None:
    """Test that a port reports its link rate and its properties."""

    description = DESCRIPTIONS[f"port_{name.lower()}"]

    assert description.translation_key == translation_key
    assert description.translation_placeholders == {"port": name}
    assert description.unique_id_name == f"Port {name}"
    assert description.suggested_display_precision == 0
    assert description.value_fn(DATA) == value
    assert description.attributes_fn is not None
    assert description.attributes_fn(DATA) == attributes
    assert description.exists_fn is not None
    assert description.exists_fn(DATA) is True


@pytest.mark.parametrize("name", ["ai", "l3", "sfp", "u2", "w1"])
def test_port_missing(name: str) -> None:
    """Test that a port not on the device gets no sensor."""

    description = DESCRIPTIONS[f"port_{name}"]

    assert description.exists_fn is not None
    assert description.exists_fn(DATA) is False
    assert description.value_fn(DATA) is None


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_source(description: ARSensorDescription) -> None:
    """Test that the router reports the ports of the nodes it serves."""

    assert description.source is ARPortsSourceUniversal
    assert description.node_source is not None
    assert description.node_source(MAC) is ARPortsSourceUniversal
    # A node with its own entry reports its ports itself
    assert description.covers_mesh is False
    assert description.data_fn is None
