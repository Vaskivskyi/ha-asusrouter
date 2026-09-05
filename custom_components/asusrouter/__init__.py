"""AsusRouter integration."""

from __future__ import annotations

from dataclasses import dataclass

from asusrouter import AsusRouterError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .bridge import ARBridge


@dataclass
class ARRuntimeData:
    """Runtime data of an AsusRouter config entry."""

    bridge: ARBridge


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
        raise ConfigEntryNotReady(
            f"Cannot connect to `{config_entry.data[CONF_HOST]}`"
        ) from ex

    config_entry.runtime_data = ARRuntimeData(bridge=bridge)

    # Register the bridge device
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id, **bridge.device_info
    )

    async def async_close_connection(event: Event) -> None:
        """Close router connection on HA stop."""

        await bridge.async_close()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, async_close_connection
        )
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> bool:
    """Unload AsusRouter config entry."""

    await config_entry.runtime_data.bridge.async_close()

    return True
