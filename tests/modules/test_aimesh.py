"""Tests for the AiMesh module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.aimesh import (
    ARAiMeshBackhaul,
    ARAiMeshMedium,
    ARAiMeshNode,
    ARAiMeshSourceUniversal,
    ARAiMeshTopology,
)
from asusrouter.modules.ports import ARPortSpeed
from asusrouter.modules.wifi import ARWiFiBand
from asusrouter.tools.identifiers import IpAddress, MacAddress
import pytest

from custom_components.asusrouter.modules.aimesh import (
    BINARY_SENSORS,
    SENSORS,
    _get_aimesh_attributes,
    _get_backhaul,
    _get_backhaul_attributes,
    _get_ip,
    _get_link_rate,
    _get_link_rate_attributes,
    _get_online,
    _get_rssi,
    _has_link_rate,
    _has_rssi,
    _is_online,
    _serves_mesh,
)

ROUTER_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
RSSI = -58

BACKHAUL = ARAiMeshBackhaul(
    medium=ARAiMeshMedium.WIRELESS,
    mac_parent=ROUTER_MAC,
    band=ARWiFiBand.BAND_5G1,
    rssi=RSSI,
)
NODE = ARAiMeshNode(
    mac=NODE_MAC,
    ip=IpAddress.from_value("192.168.1.2"),
    online=True,
    backhaul=BACKHAUL,
)
# The router has no backhaul, as an offline node
ROUTER = ARAiMeshNode(mac=ROUTER_MAC)
WIRED = ARAiMeshNode(
    mac=NODE_MAC,
    online=True,
    backhaul=ARAiMeshBackhaul(
        medium=ARAiMeshMedium.WIRED,
        mac_parent=ROUTER_MAC,
        port=2,
        link_rate=ARPortSpeed.MBPS_2500,
    ),
)

DESCRIPTIONS = {
    description.key: description for description in (*BINARY_SENSORS, *SENSORS)
}


def _get_backhaul_node(
    medium: ARAiMeshMedium, band: ARWiFiBand | None = None
) -> ARAiMeshNode:
    """Create an online node with the given backhaul."""

    return ARAiMeshNode(
        mac=NODE_MAC,
        online=True,
        backhaul=ARAiMeshBackhaul(medium=medium, band=band),
    )


@pytest.mark.parametrize("serves_mesh", [True, False])
def test_serves_mesh(serves_mesh: bool) -> None:
    """Test that the AiMesh entities follow the bridge."""

    assert _serves_mesh(Mock(serves_mesh=serves_mesh)) is serves_mesh


def test_get_aimesh_attributes() -> None:
    """Test that every device of the AiMesh is counted, offline included."""

    topology = ARAiMeshTopology(nodes={ROUTER_MAC: ROUTER, NODE_MAC: NODE})

    assert _get_aimesh_attributes(topology) == {"total": 2}


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (NODE, "wireless_5g1"),
        (
            _get_backhaul_node(ARAiMeshMedium.WIRELESS, ARWiFiBand.BAND_5G2),
            "wireless_5g2",
        ),
        (WIRED, "wired"),
        (_get_backhaul_node(ARAiMeshMedium.MLO), "mlo"),
        (ROUTER, None),
        # Not a known option
        (_get_backhaul_node(ARAiMeshMedium.UNKNOWN), None),
        (_get_backhaul_node(ARAiMeshMedium.WIRELESS), None),
        (
            _get_backhaul_node(ARAiMeshMedium.WIRELESS, ARWiFiBand.UNKNOWN),
            None,
        ),
    ],
)
def test_get_backhaul(node: ARAiMeshNode, expected: str | None) -> None:
    """Test that a wireless backhaul is reported with its band."""

    assert _get_backhaul(node) == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (NODE, {"parent": "aa:bb:cc:dd:ee:01"}),
        (WIRED, {"parent": "aa:bb:cc:dd:ee:01"}),
        (ROUTER, {"parent": None}),
        (
            ARAiMeshNode(
                mac=NODE_MAC,
                backhaul=ARAiMeshBackhaul(medium=ARAiMeshMedium.WIRED),
            ),
            {"parent": None},
        ),
    ],
)
def test_get_backhaul_attributes(
    node: ARAiMeshNode, expected: dict[str, Any]
) -> None:
    """Test that the parent of the backhaul is reported."""

    assert _get_backhaul_attributes(node) == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [(NODE, "192.168.1.2"), (ROUTER, None)],
)
def test_get_ip(node: ARAiMeshNode, expected: str | None) -> None:
    """Test that the IP address is read as text."""

    assert _get_ip(node) == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (WIRED, 2500),
        # Unknown on a wireless backhaul
        (NODE, None),
        (ROUTER, None),
        (
            ARAiMeshNode(
                mac=NODE_MAC,
                backhaul=ARAiMeshBackhaul(
                    medium=ARAiMeshMedium.WIRED, link_rate=ARPortSpeed.DOWN
                ),
            ),
            0,
        ),
    ],
)
def test_get_link_rate(node: ARAiMeshNode, expected: int | None) -> None:
    """Test that the backhaul link rate is read in Mbit/s."""

    assert _get_link_rate(node) == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [(WIRED, {"port": 2}), (NODE, {"port": None}), (ROUTER, {"port": None})],
)
def test_get_link_rate_attributes(
    node: ARAiMeshNode, expected: dict[str, Any]
) -> None:
    """Test that the wired backhaul port is reported."""

    assert _get_link_rate_attributes(node) == expected


@pytest.mark.parametrize(
    ("nodes", "expected"),
    [
        ([ROUTER, NODE], 1),
        ([NODE, ARAiMeshNode(mac=ROUTER_MAC, online=True)], 2),
        ([], 0),
    ],
)
def test_get_online(nodes: list[ARAiMeshNode], expected: int) -> None:
    """Test that only the online devices are counted."""

    topology = ARAiMeshTopology(nodes={node.mac: node for node in nodes})

    assert _get_online(topology) == expected


@pytest.mark.parametrize(("node", "expected"), [(NODE, RSSI), (ROUTER, None)])
def test_get_rssi(node: ARAiMeshNode, expected: int | None) -> None:
    """Test that the backhaul signal strength is read."""

    assert _get_rssi(node) == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (WIRED, True),
        (NODE, False),
        # Offline
        (ROUTER, False),
        (ARAiMeshNode(mac=NODE_MAC, backhaul=WIRED.backhaul), False),
        # Online, without a backhaul
        (ARAiMeshNode(mac=NODE_MAC, online=True), False),
    ],
)
def test_has_link_rate(node: ARAiMeshNode, expected: bool) -> None:
    """Test that only an online backhaul with a known link rate has one."""

    assert _has_link_rate(node) is expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (NODE, True),
        (WIRED, False),
        # Offline
        (ROUTER, False),
        (ARAiMeshNode(mac=NODE_MAC, backhaul=BACKHAUL), False),
        # Online, without a backhaul
        (ARAiMeshNode(mac=NODE_MAC, online=True), False),
    ],
)
def test_has_rssi(node: ARAiMeshNode, expected: bool) -> None:
    """Test that only an online wireless backhaul has a signal."""

    assert _has_rssi(node) is expected


@pytest.mark.parametrize(("node", "expected"), [(NODE, True), (ROUTER, False)])
def test_is_online(node: ARAiMeshNode, expected: bool) -> None:
    """Test that the node is online as reported."""

    assert _is_online(node) is expected


def test_aimesh_sensor() -> None:
    """Test that the AiMesh sensor keeps its unique_id and counts the mesh."""

    description = DESCRIPTIONS["aimesh"]
    topology = ARAiMeshTopology(nodes={NODE_MAC: NODE})

    assert description.unique_id_name == "AiMesh"
    assert description.data_fn is not None
    assert description.data_fn(topology) is topology
    assert description.attributes_fn is _get_aimesh_attributes
    # Only the router counts its mesh
    assert description.on_device is True
    assert description.node_source is None


def test_backhaul_link_rate_precision() -> None:
    """Test that the link rate is shown in whole Mbit/s."""

    description = next(
        description
        for description in SENSORS
        if description.key == "backhaul_link_rate"
    )

    assert description.suggested_display_precision == 0


def test_backhaul_options() -> None:
    """Test that every known medium and wireless band is an option."""

    description = next(item for item in SENSORS if item.key == "backhaul")

    assert description.options == [
        "mlo",
        "moca",
        "plc",
        "wired",
        "wireless_2g1",
        "wireless_2g2",
        "wireless_5g1",
        "wireless_5g2",
        "wireless_6g1",
        "wireless_6g2",
    ]


@pytest.mark.parametrize(
    ("key", "value", "on_device", "available_fn"),
    [
        # The router is online whenever its topology is read
        ("connected", True, False, None),
        ("backhaul", "wireless_5g1", False, _is_online),
        ("backhaul_rssi", RSSI, False, _has_rssi),
        ("backhaul_link_rate", None, False, _has_link_rate),
        # Kept for an offline node, as set in the AiMesh
        ("ip_address", "192.168.1.2", True, None),
    ],
)
def test_node_entities(
    key: str, value: Any, on_device: bool, available_fn: Any
) -> None:
    """Test that each node entity reads its node from the topology."""

    description = DESCRIPTIONS[key]

    assert description.value_fn(NODE) == value
    assert description.on_device is on_device
    assert description.available_fn is available_fn
    assert description.source is ARAiMeshSourceUniversal
    assert description.node_source is not None
    assert description.node_source(NODE_MAC) is ARAiMeshSourceUniversal
    # The router reports the nodes other entries serve as well
    assert description.covers_mesh is True
    assert description.supported_fn is _serves_mesh
