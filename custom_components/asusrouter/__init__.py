"""Support for ASUS Router devices"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from .const import (
    CONF_INTERFACES,
    DELAULT_INTERFACES,
    DOMAIN,
    DATA_ASUSROUTER,
    PLATFORMS,
)
from .router import AsusRouterObj
from .migrate import DEPRECATED


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup ASUS Router platform"""

    router = AsusRouterObj(hass, entry)
    await router.setup()

    router.async_on_close(entry.add_update_listener(update_listener))

    async def async_close_connection(event):
        """Close AsusRouter connection on HA stop"""

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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry"""

    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload:
        hass.data[DOMAIN][entry.entry_id]["stop_listener"]()
        router = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
        await router.close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update on config_entry update"""

    router = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]

    if router.update_options(entry.options):
        await hass.config_entries.async_reload(entry.entry_id)

    return


async def async_migrate_entry(hass, config_entry : ConfigEntry):
    """Migrate old entry."""

    _LOGGER.debug("Migrating from version {}".format(config_entry.version))

    version = config_entry.version
    entry = {**config_entry.data}
    options = {**config_entry.options}

    if version == 1:
        options[CONF_INTERFACES] = DELAULT_INTERFACES

    while "{}_{}".format(version, version + 1) in DEPRECATED:
        new_entry = entry

        for key_old in DEPRECATED["{}_{}".format(version, version + 1)]:
            key_new = DEPRECATED["{}_{}".format(version, version + 1)][key_old]
            new_entry[key_new] = new_entry[key_old]
            new_entry.pop(key_old)

        entry = new_entry
        version += 1

    config_entry.version = version
    hass.config_entries.async_update_entry(config_entry, data = new_entry, options = options)

    _LOGGER.info("Migration to version {} successful".format(config_entry.version))

    return True


