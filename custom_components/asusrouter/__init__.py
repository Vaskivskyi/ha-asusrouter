"""Support for AsusRouter devices."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from asusrouter import AsusRouterError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .bridge import ARBridge
from .const import ENTRY_VERSION

_LOGGER = logging.getLogger(__name__)

# Everything an entry needs to reach the device, and nothing else
CONNECTION_KEYS = (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
)


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

    _LOGGER.debug("Setting up entry")

    bridge = ARBridge(hass, dict(config_entry.data))

    try:
        await bridge.async_connect()
    except AsusRouterError as ex:
        await bridge.async_clean()
        raise ConfigEntryNotReady(
            f"Cannot connect to `{config_entry.data[CONF_HOST]}`"
        ) from ex

    config_entry.runtime_data = ARRuntimeData(bridge=bridge)

    # Register the device before any platform, so entities attach to a device
    # which already reports the correct model and firmware
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id, **bridge.device_info
    )

    async def async_close_connection(event: Event) -> None:
        """Close router connection on HA stop."""

        await bridge.async_clean()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, async_close_connection
        )
    )
    config_entry.async_on_unload(
        config_entry.add_update_listener(update_listener)
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> bool:
    """Unload AsusRouter config entry."""

    _LOGGER.debug("Unloading entry")

    await config_entry.runtime_data.bridge.async_clean()

    return True


async def update_listener(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
) -> None:
    """Reload on config entry update."""

    _LOGGER.debug("Update listener activated")

    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: ARConfigEntry
) -> bool:
    """Migrate an old entry."""

    if config_entry.version >= ENTRY_VERSION:
        return True

    _LOGGER.debug("Migrating from version %s", config_entry.version)

    # Connection settings used to be split between data and options, next to
    # options which no longer exist. Keep the connection, drop the rest
    stored = {**config_entry.data, **config_entry.options}
    data = {key: stored[key] for key in CONNECTION_KEYS if key in stored}

    hass.config_entries.async_update_entry(
        config_entry, data=data, options={}, version=ENTRY_VERSION
    )

    _LOGGER.debug("Migration to version %s successful", ENTRY_VERSION)

    return True
