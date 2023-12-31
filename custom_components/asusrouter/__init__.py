"""Support for AsusRouter devices."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import ASUSROUTER, DOMAIN, PLATFORMS, STOP_LISTENER
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up AsusRouter platform."""

    _LOGGER.debug("Setting up entry")

    router = ARDevice(hass, config_entry)
    await router.setup()

    router.async_on_close(config_entry.add_update_listener(update_listener))

    async def async_close_connection(event):
        """Close router connection on HA stop."""

        await router.close()

    stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, async_close_connection
    )

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        ASUSROUTER: router,
        STOP_LISTENER: stop_listener,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Unload AsusRouter config entry."""

    _LOGGER.debug("Unloading entry")

    unload = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    if unload:
        # Close connection
        hass.data[DOMAIN][config_entry.entry_id][STOP_LISTENER]()
        await hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER].close()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload


async def update_listener(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Reload on config entry update."""

    _LOGGER.debug("Update listener activated")

    router = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]

    if router.update_options(config_entry.options):
        await hass.config_entries.async_reload(config_entry.entry_id)

    return


# Example migration function
async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""

    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 4:
        new_options = {**config_entry.options}
        new_options["interval_network"] = new_options.pop("interval_network_stat", 30)

        config_entry.version = 5
        hass.config_entries.async_update_entry(config_entry, options=new_options)

    _LOGGER.debug("Migration to version %s successful", config_entry.version)

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a device."""

    # This would actually work and should not provide any issues

    _LOGGER.debug("Removing device")

    return True
