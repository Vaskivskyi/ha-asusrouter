"""Tests for the topology module."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock, patch

from asusrouter.modules.aimesh import ARAiMeshNode, ARAiMeshTopology
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import topology
from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.topology import (
    async_register_devices,
    async_remove_stale_devices,
    async_sync_topology,
    can_remove_device,
)

pytestmark = pytest.mark.asyncio

ENTRY_ID = "entry"

NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
OWNED_NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
NODE_IDENTIFIER = (DOMAIN, str(NODE_MAC))

DEVICE_INFO = {"identifiers": {(DOMAIN, "device")}, "name": "Model"}
NODE_DEVICE_INFO = {"identifiers": {NODE_IDENTIFIER}, "name": "Node"}


@pytest.fixture
def registry() -> Iterator[Mock]:
    """Mock the device registry module."""

    with patch.object(topology, "dr") as dr:
        yield dr


def _get_node(mac: MacAddress = NODE_MAC) -> ARAiMeshNode:
    """Create an AiMesh node as the library reports it."""

    return ARAiMeshNode(mac=mac)


def _get_entry(mesh: Any = ()) -> Mock:
    """Create a config entry with the given AiMesh nodes."""

    entry = Mock(entry_id=ENTRY_ID)
    entry.runtime_data.mesh = frozenset(mesh)
    bridge = entry.runtime_data.bridge
    bridge.get_nodes = Mock(
        side_effect=lambda found: list(found.nodes.values())
    )
    bridge.get_node_device_info = Mock(return_value=NODE_DEVICE_INFO)
    bridge.get_node_naming = Mock(return_value=("Model", "Name"))

    return entry


def _get_coordinator(*macs: MacAddress, success: bool = True) -> Mock:
    """Create a topology coordinator with the given nodes."""

    return Mock(
        data=ARAiMeshTopology(nodes={mac: _get_node(mac) for mac in macs}),
        last_update_success=success,
    )


# ---------------------------
# DEVICES -->
# ---------------------------


async def test_register_devices(registry: Mock) -> None:
    """Test that the device and the nodes no other entry owns are created."""

    hass = Mock()
    entry = _get_entry()
    nodes = [_get_node(), _get_node(OWNED_NODE_MAC)]
    owned = {OWNED_NODE_MAC: Mock(id="owned")}
    devices = registry.async_get.return_value

    with patch.object(
        topology, "get_device_info", Mock(return_value=DEVICE_INFO)
    ) as device_info:
        device = async_register_devices(hass, entry, nodes, owned)

    bridge = entry.runtime_data.bridge
    assert device is devices.async_get_or_create.return_value
    device_info.assert_called_once_with(hass, entry, bridge)
    devices.async_get_or_create.assert_any_call(
        config_entry_id=ENTRY_ID, **DEVICE_INFO
    )
    bridge.get_node_device_info.assert_called_once_with(nodes[0], device.id)
    devices.async_get_or_create.assert_called_with(
        config_entry_id=ENTRY_ID, **NODE_DEVICE_INFO
    )
    # The entry of the node cannot name it, so its router does
    bridge.get_node_naming.assert_called_once_with(nodes[1])
    devices.async_update_device.assert_called_once_with(
        "owned", model="Model", name="Name"
    )


async def test_remove_stale_devices(registry: Mock) -> None:
    """Test that only the nodes that left the AiMesh are removed."""

    device = Mock(id="device")
    registry.async_entries_for_config_entry.return_value = [
        device,
        Mock(id="node", via_device_id="device", identifiers={NODE_IDENTIFIER}),
        Mock(id="left", via_device_id="device", identifiers={(DOMAIN, "x")}),
        # Linked to a device of another integration
        Mock(id="other", via_device_id="other", identifiers={(DOMAIN, "y")}),
    ]

    async_remove_stale_devices(Mock(), _get_entry(), device, [_get_node()])

    registry.async_entries_for_config_entry.assert_called_once_with(
        registry.async_get.return_value, ENTRY_ID
    )
    registry.async_get.return_value.async_remove_device.assert_called_once_with(
        "left"
    )


# ---------------------------
# <-- DEVICES
# ---------------------------

# ---------------------------
# SYNC -->
# ---------------------------


@pytest.mark.parametrize(
    "coordinator",
    [
        # Listeners are called on failures too
        _get_coordinator(NODE_MAC, success=False),
        # Nothing was ever read
        _get_coordinator(),
    ],
)
async def test_sync_topology_nothing_new(coordinator: Mock) -> None:
    """Test that a failed read changes nothing."""

    hass = Mock()

    with patch.object(topology, "async_register_devices") as register:
        async_sync_topology(
            hass, _get_entry(mesh=[OWNED_NODE_MAC]), coordinator
        )

    hass.config_entries.async_schedule_reload.assert_not_called()
    register.assert_not_called()


@pytest.mark.parametrize(
    "macs",
    [
        # A node joined
        [NODE_MAC, OWNED_NODE_MAC],
        # A node left
        [OWNED_NODE_MAC],
    ],
)
async def test_sync_topology_mesh_changed(macs: list[MacAddress]) -> None:
    """Test that a changed mesh sets every node up again."""

    hass = Mock()

    with patch.object(topology, "async_register_devices") as register:
        async_sync_topology(
            hass, _get_entry(mesh=[NODE_MAC]), _get_coordinator(*macs)
        )

    hass.config_entries.async_schedule_reload.assert_called_once_with(ENTRY_ID)
    register.assert_not_called()


async def test_sync_topology_updates_devices() -> None:
    """Test that a known mesh only refreshes the node devices."""

    hass = Mock()
    entry = _get_entry(mesh=[NODE_MAC])
    coordinator = _get_coordinator(NODE_MAC)

    with (
        patch.object(topology, "async_register_devices") as register,
        patch.object(topology, "get_owned_devices") as owned,
    ):
        async_sync_topology(hass, entry, coordinator)

    hass.config_entries.async_schedule_reload.assert_not_called()
    owned.assert_called_once_with(hass, entry, frozenset({NODE_MAC}))
    register.assert_called_once_with(
        hass, entry, list(coordinator.data.nodes.values()), owned.return_value
    )


@pytest.mark.parametrize(
    ("via_device_id", "identifiers", "expected"),
    [
        ("router", {(DOMAIN, "left")}, True),
        # Still in the AiMesh
        ("router", {NODE_IDENTIFIER}, False),
        # The device itself
        (None, {(DOMAIN, "device")}, False),
    ],
)
async def test_can_remove_device(
    via_device_id: str | None,
    identifiers: set[tuple[str, str]],
    expected: bool,
) -> None:
    """Test that only a node no longer in the AiMesh can be removed."""

    device = Mock(via_device_id=via_device_id, identifiers=identifiers)

    assert can_remove_device(_get_entry(mesh=[NODE_MAC]), device) is expected


# ---------------------------
# <-- SYNC
# ---------------------------
