"""Support for ASUS Router devices"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DATA_ASUSROUTER
from .router import AsusRouterObj

PLATFORMS = [Platform.SENSOR, Platform.DEVICE_TRACKER]


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


