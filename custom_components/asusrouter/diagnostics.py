"""AsusRouter diagnostics."""

from __future__ import annotations

from typing import Any

import attr
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_IDENTIFIERS,
    CONF_PASSWORD,
    CONF_UNIQUE_ID,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DATA_ASUSROUTER, DEVICE_ATTRIBUTE_LAST_ACTIVITY, DOMAIN
from .router import AsusRouterObj

TO_REDACT = {CONF_PASSWORD, CONF_UNIQUE_ID, CONF_USERNAME}
TO_REDACT_DEV = {ATTR_CONNECTIONS, ATTR_IDENTIFIERS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, dict[str, Any]]:
    """Return diagnostics for a config entry."""

    data = {"entry": async_redact_data(entry.as_dict(), TO_REDACT)}

    router: AsusRouterObj = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]

    # Gather information how this AsusWrt device is represented in Home Assistant
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    hass_device = device_registry.async_get_device(
        identifiers=router.device_info["identifiers"]
    )
    if not hass_device:
        return data

    data["device"] = {
        **async_redact_data(attr.asdict(hass_device), TO_REDACT_DEV),
        "entities": {},
        "tracked_devices": [],
    }

    hass_entities = er.async_entries_for_device(
        entity_registry,
        device_id=hass_device.id,
        include_disabled_entities=True,
    )

    for entity_entry in hass_entities:
        state = hass.states.get(entity_entry.entity_id)
        state_dict = None
        if state:
            state_dict = dict(state.as_dict())
            # The entity_id is already provided at root level.
            state_dict.pop("entity_id", None)
            # The context doesn't provide useful information in this case.
            state_dict.pop("context", None)

        data["device"]["entities"][entity_entry.entity_id] = {
            **async_redact_data(
                attr.asdict(
                    entity_entry, filter=lambda attr, value: attr.name != "entity_id"
                ),
                TO_REDACT,
            ),
            "state": state_dict,
        }

    for device in router.devices.values():
        data["device"]["tracked_devices"].append(
            {
                "name": device.name,
                "ip_address": device.ip,
                "last_activity": device.extra_state_attributes[
                    DEVICE_ATTRIBUTE_LAST_ACTIVITY
                ]
                if DEVICE_ATTRIBUTE_LAST_ACTIVITY in device.extra_state_attributes
                else None,
            }
        )

    return data
