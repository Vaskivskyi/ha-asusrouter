"""AsusRouter ownership module."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from asusrouter.modules.aimesh import ARAiMeshNode
from asusrouter.modules.common.device import AROperationMode
from asusrouter.tools.identifiers import MacAddress
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .helpers import to_identifier

if TYPE_CHECKING:
    from . import ARConfigEntry
    from .bridge import ARBridge


def _is_foreign(
    hass: HomeAssistant, device: dr.DeviceEntry, config_entry: ARConfigEntry
) -> bool:
    """Check whether the device belongs to another entry of the integration."""

    if device.config_entry_id == config_entry.entry_id:
        return False

    entry = hass.config_entries.async_get_entry(device.config_entry_id)
    return entry is not None and entry.domain == DOMAIN


def get_owned_devices(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    macs: Iterable[MacAddress],
) -> dict[MacAddress, dr.DeviceEntry]:
    """Get the devices another entry connects to directly, by their MACs."""

    registry = dr.async_get(hass)
    owned: dict[MacAddress, dr.DeviceEntry] = {}

    for mac in macs:
        for device in registry.async_get_devices(
            identifiers={to_identifier(mac)}
        ):
            # A node device is linked to its router, a direct one is not
            if device.via_device_id is None and _is_foreign(
                hass, device, config_entry
            ):
                owned[mac] = device
                break

    return owned


def _find_mesh_node(
    hass: HomeAssistant, config_entry: ARConfigEntry, mac: MacAddress | None
) -> ARAiMeshNode | None:
    """Find the device in the AiMesh topology of another loaded entry."""

    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.entry_id == config_entry.entry_id:
            continue
        node: ARAiMeshNode | None = (
            entry.runtime_data.bridge.identity.aimesh.get(mac)
        )
        if node is not None:
            return node

    return None


def get_device_info(
    hass: HomeAssistant, config_entry: ARConfigEntry, bridge: ARBridge
) -> DeviceInfo:
    """Get the device information, named from any known AiMesh topology."""

    identity = bridge.identity
    # A router lists itself, a node is listed by its router only
    mesh_node = identity.aimesh.get(identity.mac) or _find_mesh_node(
        hass, config_entry, identity.mac
    )
    device_info = bridge.get_device_info(mesh_node)

    if (
        mesh_node is None
        and identity.operation_mode is AROperationMode.AIMESH_NODE
        and any(
            device.config_entry_id == config_entry.entry_id
            for device in dr.async_get(hass).async_get_devices(
                identifiers=device_info["identifiers"]
            )
        )
    ):
        # Keep the name its router gave, the node alone cannot tell it
        device_info.pop("model")
        device_info.pop("name")

    return device_info


async def async_take_over(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    device: dr.DeviceEntry,
) -> None:
    """Take over the entities other entries created for this device."""

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    previous: set[str] = set()

    for other in device_registry.async_get_devices(
        identifiers=device.identifiers
    ):
        # Only a node device another entry created through its router
        if other.via_device_id is None or not _is_foreign(
            hass, other, config_entry
        ):
            continue

        # Moving keeps the entity ids and their history
        for entity in er.async_entries_for_device(
            entity_registry, other.id, include_disabled_entities=True
        ):
            entity_registry.async_update_entity(
                entity.entity_id,
                config_entry_id=config_entry.entry_id,
                device_id=device.id,
            )
        device_registry.async_remove_device(other.id)
        previous.add(other.config_entry_id)

    # The previous owners drop their entities before ours are added
    for entry_id in previous:
        await hass.config_entries.async_reload(entry_id)


def async_hand_back(hass: HomeAssistant, config_entry: ARConfigEntry) -> None:
    """Let the routers of the removed entry's device serve it again."""

    identifiers = {
        identifier
        for device in dr.async_entries_for_config_entry(
            dr.async_get(hass), config_entry.entry_id
        )
        for identifier in device.identifiers
    }

    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.entry_id != config_entry.entry_id and any(
            to_identifier(mac) in identifiers
            for mac in entry.runtime_data.mesh
        ):
            hass.config_entries.async_schedule_reload(entry.entry_id)
