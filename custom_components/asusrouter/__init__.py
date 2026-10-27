"""AsusRouter integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any

from asusrouter import AsusRouterError
from asusrouter.modules.aimesh import ARAiMeshSourceUniversal
from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .bridge import ARBridge
from .coordinator import (
    ARCoordinator,
    ARTopologyCoordinator,
    async_setup_coordinators,
)
from .errors import is_auth_error
from .modules import DESCRIPTIONS
from .ownership import async_hand_back, async_take_over, get_owned_devices
from .topology import (
    TOPOLOGY_INTERVAL,
    async_register_devices,
    async_remove_stale_devices,
    async_sync_topology,
    can_remove_device,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class ARRuntimeData:
    """Runtime data of an AsusRouter config entry."""

    bridge: ARBridge
    coordinators: dict[ARDataSource, ARCoordinator[Any]] = field(
        default_factory=dict
    )
    # Every AiMesh node at setup, including the ones other entries serve
    mesh: frozenset[MacAddress] = frozenset()
    # AiMesh nodes served through this entry
    nodes: list[MacAddress] = field(default_factory=list)


type ARConfigEntry = ConfigEntry[ARRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> bool:
    """Set up AsusRouter platform."""

    bridge = ARBridge(hass, config_entry.data)

    try:
        await bridge.async_connect()
    except AsusRouterError as ex:
        await bridge.async_close()
        host = config_entry.data[CONF_HOST]
        if is_auth_error(ex):
            # Reconnecting cannot help, requires new credentials
            raise ConfigEntryAuthFailed(
                f"Device `{host}` refused the saved credentials"
            ) from ex
        raise ConfigEntryNotReady(f"Cannot connect to `{host}`") from ex

    runtime_data = config_entry.runtime_data = ARRuntimeData(bridge=bridge)

    topology = bridge.identity.aimesh
    nodes = bridge.get_nodes(topology)
    # A node added as its own entry is served by that entry only
    owned = get_owned_devices(hass, config_entry, (node.mac for node in nodes))
    runtime_data.mesh = frozenset(node.mac for node in nodes)
    runtime_data.nodes = [node.mac for node in nodes if node.mac not in owned]

    # The topology is followed even with no entity using it
    background = (
        [(ARAiMeshSourceUniversal, TOPOLOGY_INTERVAL)]
        if bridge.serves_mesh
        else []
    )

    # Platforms cannot defer the setup or ask for new credentials, so the
    # first refresh of every coordinator runs here
    try:
        runtime_data.coordinators = await async_setup_coordinators(
            hass, config_entry, DESCRIPTIONS, runtime_data.nodes, background
        )
    except Exception:
        # A failed setup is never unloaded
        await bridge.async_close()
        raise

    device = async_register_devices(hass, config_entry, nodes, owned)
    # The device lists itself, so an empty topology is a failed read
    if topology.nodes:
        async_remove_stale_devices(hass, config_entry, device, nodes)
    await async_take_over(hass, config_entry, device)

    coordinator = runtime_data.coordinators.get(ARAiMeshSourceUniversal)
    if isinstance(coordinator, ARTopologyCoordinator):
        config_entry.async_on_unload(
            coordinator.async_add_listener(
                partial(async_sync_topology, hass, config_entry, coordinator)
            )
        )

    async def async_close_connection(event: Event) -> None:
        """Close router connection on HA stop."""

        await bridge.async_close()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, async_close_connection
        )
    )

    await hass.config_entries.async_forward_entry_setups(
        config_entry, PLATFORMS
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> bool:
    """Unload AsusRouter config entry."""

    if not await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        return False

    await config_entry.runtime_data.bridge.async_close()

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow removing the device of a node that left the AiMesh."""

    return can_remove_device(config_entry, device_entry)


async def async_remove_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> None:
    """Remove AsusRouter config entry."""

    async_hand_back(hass, config_entry)
