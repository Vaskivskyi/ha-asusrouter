"""Support for AsusRouter devices."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CACHE_TIME,
    CONF_CONSIDER_HOME,
    CONF_INTERFACES,
    CONF_UNITS_SPEED,
    CONF_UNITS_TRAFFIC,
    DATA_ASUSROUTER,
    DEFAULT_CACHE_TIME,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    DELAULT_INTERFACES,
    DOMAIN,
    PLATFORMS,
)
from .migrate import DEPRECATED, MOVE_TO_OPTIONS
from .router import AsusRouterObj


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Setup AsurRouter platform."""

    router = AsusRouterObj(hass, entry)
    await router.setup()

    router.async_on_close(entry.add_update_listener(update_listener))

    async def async_close_connection(event):
        """Close AsusRouter connection on HA stop."""

        await router.close()

    stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, async_close_connection
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_ASUSROUTER: router,
        "stop_listener": stop_listener,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload entry."""

    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload:
        hass.data[DOMAIN][entry.entry_id]["stop_listener"]()
        router = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
        await router.close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload


async def update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Update on config_entry update."""

    router = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]

    if router.update_options(entry.options):
        await hass.config_entries.async_reload(entry.entry_id)

    return


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate old entry."""

    version = entry.version
    _LOGGER.debug(f"Migrating from version {entry.version}")

    new_entry = {**entry.data}
    new_options = {**entry.options}

    if version == 1:
        new_options[CONF_INTERFACES] = DELAULT_INTERFACES

    if version == 2:
        new_options[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL
        new_options[CONF_CACHE_TIME] = DEFAULT_CACHE_TIME
        new_options[CONF_CONSIDER_HOME] = DEFAULT_CONSIDER_HOME

    if version == 3:
        new_options[CONF_UNITS_SPEED] = DEFAULT_UNITS_SPEED
        new_options[CONF_UNITS_TRAFFIC] = DEFAULT_UNITS_TRAFFIC
        version += 1

    while f"{version}_{version + 1}" in DEPRECATED:
        for key_old in DEPRECATED[f"{version}_{version + 1}"]:
            key_new = DEPRECATED[f"{version}_{version + 1}"][key_old]
            new_entry[key_new] = new_entry[key_old]
            new_entry.pop(key_old)

        version += 1

    while f"{version}_{version + 1}" in MOVE_TO_OPTIONS:
        for key in MOVE_TO_OPTIONS[f"{version}_{version + 1}"]:
            new_options[key] = new_entry[key]
            new_entry.pop(key)

        version += 1

    entry.version = version
    hass.config_entries.async_update_entry(entry, data=new_entry, options=new_options)

    _LOGGER.info(f"Migration to version {entry.version} successful")

    return True
