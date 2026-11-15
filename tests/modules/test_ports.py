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
        # A port the device reports without a label
        {ARPortProperty.LINK_RATE: ARPortSpeed.MBPS_1000},
    ],
)

DESCRIPTIONS: dict[str, ARSensorDescription] = {
    description.key: description for description in SENSORS
}
ETHERNET = DESCRIPTIONS["port"]
USB = DESCRIPTIONS["usb_port"]


@pytest.mark.parametrize(
    ("description", "translation_key", "keys"),
    [
        (ETHERNET, "port", {"W0", "L1", "L2"}),
        (USB, "usb_port", {"U1"}),
    ],
)
def test_keys(
    description: ARSensorDescription, translation_key: str, keys: set[str]
) -> None:
    """Test that every port on the device gets a sensor of its kind."""

    assert description.translation_key == translation_key
    assert description.keys_fn is not None
    assert set(description.keys_fn(DATA)) == keys
    assert description.keys_fn(ARPortsData(info={}, ports=[])) == {}


@pytest.mark.parametrize(
    ("description", "name", "value", "attributes"),
    [
        (
            ETHERNET,
            "W0",
            2500,
            {
                "capabilities": ["game", "wan"],
                "max_rate": 10000,
                "role": "wan",
            },
        ),
        # A port that is down
        (
            ETHERNET,
            "L1",
            0,
            {"capabilities": [], "max_rate": 1000, "role": "lan"},
        ),
        # Nothing known about the port
        (
            ETHERNET,
            "L2",
            None,
            {"capabilities": [], "max_rate": None, "role": None},
        ),
        (
            USB,
            "U1",
            5000,
            {"capabilities": [], "max_rate": 5000, "role": "usb"},
        ),
    ],
)
def test_port(
    description: ARSensorDescription,
    name: str,
    value: int | None,
    attributes: dict[str, Any],
) -> None:
    """Test that a port reports its link rate and its properties."""

    assert description.item_fn is not None
    assert description.unique_id_fn is not None
    assert description.placeholders_fn is not None
    port = description.item_fn(DATA, name)

    assert description.placeholders_fn(name) == {"port": name}
    assert description.unique_id_fn(name) == f"Port {name}"
    assert description.suggested_display_precision == 0
    assert description.value_fn(port) == value
    assert description.attributes_fn is not None
    assert description.attributes_fn(port) == attributes


@pytest.mark.parametrize(
    ("description", "name"), [(ETHERNET, "U1"), (USB, "W0"), (ETHERNET, "L3")]
)
def test_port_missing(description: ARSensorDescription, name: str) -> None:
    """Test that a port of the other kind or not on the device is not read."""

    assert description.item_fn is not None
    assert description.item_fn(DATA, name) is None


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_source(description: ARSensorDescription) -> None:
    """Test that the router reports the ports of the nodes it serves."""

    assert description.source is ARPortsSourceUniversal
    assert description.node_source is not None
    assert description.node_source(MAC) is ARPortsSourceUniversal
    # A node with its own entry reports its ports itself
    assert description.covers_mesh is False
    assert description.data_fn is None
    # A port missing from a read is not removed
    assert description.remove_missing is False
