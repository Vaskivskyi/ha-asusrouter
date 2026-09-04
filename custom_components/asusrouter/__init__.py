"""Support for AsusRouter devices."""

from __future__ import annotations

import logging

from asusrouter import AsusRouterError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .bridge import ARBridge
from .const import ASUSROUTER, DOMAIN, STOP_LISTENER

_LOGGER = logging.getLogger(__name__)

# The last entry version that stored the network interval under its old name
VERSION_LEGACY_INTERVAL_NETWORK = 4


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up AsusRouter platform."""

    _LOGGER.debug("Setting up entry")

    bridge = ARBridge(
        hass, dict(config_entry.data), dict(config_entry.options)
    )

    try:
        await bridge.async_connect()
    except AsusRouterError as ex:
        await bridge.async_clean()
        raise ConfigEntryNotReady(
            f"Cannot connect to `{config_entry.data.get(CONF_HOST)}`"
        ) from ex

    config_entry.async_on_unload(
        config_entry.add_update_listener(update_listener)
    )

    async def async_close_connection(event: Event) -> None:
        """Close router connection on HA stop."""

        await bridge.async_clean()

    stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, async_close_connection
    )

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        ASUSROUTER: bridge,
        STOP_LISTENER: stop_listener,
    }

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Unload AsusRouter config entry."""

    _LOGGER.debug("Unloading entry")

    entry_data = hass.data[DOMAIN].pop(config_entry.entry_id)
    entry_data[STOP_LISTENER]()
    await entry_data[ASUSROUTER].async_clean()

    return True


async def update_listener(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Reload on config entry update."""

    _LOGGER.debug("Update listener activated")

    await hass.config_entries.async_reload(config_entry.entry_id)


# Example migration function
async def async_migrate_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Migrate old entry."""

    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == VERSION_LEGACY_INTERVAL_NETWORK:
        new_options = {**config_entry.options}
        new_options["interval_network"] = new_options.pop(
            "interval_network_stat", 30
        )

        config_entry.version = 5
        hass.config_entries.async_update_entry(
            config_entry, options=new_options
        )

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a device."""

    # This would actually work and should not provide any issues

    _LOGGER.debug("Removing device")

    return True
