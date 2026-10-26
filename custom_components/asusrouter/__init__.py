"""AsusRouter integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from asusrouter import AsusRouterError
from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .bridge import ARBridge
from .coordinator import async_setup_coordinators
from .errors import is_auth_error
from .modules import DESCRIPTIONS
from .ownership import (
    async_hand_back,
    async_take_over,
    get_device_info,
    get_owned_devices,
)

if TYPE_CHECKING:
    from .coordinator import ARCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class ARRuntimeData:
    """Runtime data of an AsusRouter config entry."""

    bridge: ARBridge
    coordinators: dict[ARDataSource, ARCoordinator] = field(
        default_factory=dict
    )
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

    # A node added as its own entry is served by that entry only
    nodes = bridge.nodes
    owned = get_owned_devices(hass, config_entry, (node.mac for node in nodes))
    runtime_data.nodes = [node.mac for node in nodes if node.mac not in owned]

    # Platforms cannot defer the setup or ask for new credentials, so the
    # first refresh of every coordinator runs here
    try:
        runtime_data.coordinators = await async_setup_coordinators(
            hass, config_entry, DESCRIPTIONS, runtime_data.nodes
        )
    except Exception:
        # A failed setup is never unloaded
        await bridge.async_close()
        raise

    # Register the bridge device and its AiMesh nodes
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

    await async_take_over(hass, config_entry, device)

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


async def async_remove_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> None:
    """Remove AsusRouter config entry."""

    async_hand_back(hass, config_entry)
