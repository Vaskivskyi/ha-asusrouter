"""AsusRouter AiMesh topology module."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import TYPE_CHECKING

from asusrouter.modules.aimesh import ARAiMeshNode
from asusrouter.tools.identifiers import MacAddress
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .helpers import to_identifier
from .ownership import get_device_info, get_owned_devices

if TYPE_CHECKING:
    from . import ARConfigEntry
    from .coordinator import ARTopologyCoordinator

TOPOLOGY_INTERVAL = timedelta(seconds=30)


@callback
def async_register_devices(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    nodes: Sequence[ARAiMeshNode],
    owned: Mapping[MacAddress, dr.DeviceEntry],
) -> dr.DeviceEntry:
    """Register the device and its AiMesh nodes, named after the topology."""

    bridge = config_entry.runtime_data.bridge
    registry = dr.async_get(hass)

    device = registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        **get_device_info(hass, config_entry, bridge),
    )
    for node in nodes:
        owned_device = owned.get(node.mac)
        if owned_device is not None:
            # Only the router knows the name of its node
            model, name = bridge.get_node_naming(node)
            registry.async_update_device(
                owned_device.id, model=model, name=name
            )
            continue
        registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **bridge.get_node_device_info(node, device.id),
        )

    return device


@callback
def async_remove_stale_devices(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    device: dr.DeviceEntry,
    nodes: Sequence[ARAiMeshNode],
) -> None:
    """Remove the devices of the nodes that left the AiMesh."""

    identifiers = {to_identifier(node.mac) for node in nodes}
    registry = dr.async_get(hass)

    for node_device in dr.async_entries_for_config_entry(
        registry, config_entry.entry_id
    ):
        if (
            node_device.via_device_id == device.id
            and node_device.identifiers.isdisjoint(identifiers)
        ):
            registry.async_remove_device(node_device.id)


@callback
def async_sync_topology(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    coordinator: ARTopologyCoordinator,
) -> None:
    """Follow the AiMesh topology of the device."""

    topology = coordinator.data
    # Listeners are called on failures too, with nothing new to follow
    if not coordinator.last_update_success or not topology.nodes:
        return

    runtime_data = config_entry.runtime_data
    nodes = runtime_data.bridge.get_nodes(topology)
    macs = frozenset(node.mac for node in nodes)

    if macs != runtime_data.mesh:
        # A node joined or left, set every node up again
        hass.config_entries.async_schedule_reload(config_entry.entry_id)
        return

    async_register_devices(
        hass, config_entry, nodes, get_owned_devices(hass, config_entry, macs)
    )


def can_remove_device(
    config_entry: ARConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Check whether the device is a node no longer in the AiMesh."""

    # The device itself is never linked to another one
    return device.via_device_id is not None and not any(
        to_identifier(mac) in device.identifiers
        for mac in config_entry.runtime_data.mesh
    )
