"""Support for AsusRouter devices."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from .const import (
    ASUSROUTER,
    DOMAIN,
    PLATFORMS,
)
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Setup AsusRouter platform."""

    _LOGGER.debug("Setting up entry")

    router = ARDevice(hass, entry)
    await router.setup()

    router.async_on_close(entry.add_update_listener(update_listener))

    async def async_close_connection(event):
        """Close AsusRouter connection on HA stop."""

        await router.close()

    stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP, async_close_connection
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        ASUSROUTER: router,
        "stop_listener": stop_listener,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload entry."""

    _LOGGER.debug("Unloading entry")

    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload:
        hass.data[DOMAIN][entry.entry_id]["stop_listener"]()
        router = hass.data[DOMAIN][entry.entry_id][ASUSROUTER]
        await router.close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload


async def update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Update on config_entry update."""

    _LOGGER.debug("Update listener activated")

    router = hass.data[DOMAIN][entry.entry_id][ASUSROUTER]

    if router.update_options(entry.options):
        await hass.config_entries.async_reload(entry.entry_id)

    return
