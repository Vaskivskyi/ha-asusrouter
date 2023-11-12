"""AsusRouter diagnostics module."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    ASUSROUTER,
    DEVICE_ATTRIBUTE_LAST_ACTIVITY,
    DOMAIN,
    TO_REDACT,
    TO_REDACT_ATTRS,
    TO_REDACT_DEV,
    TO_REDACT_STATE,
)
from .router import ARDevice


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, dict[str, Any]]:
    """Return diagnostics for a config entry."""

    data = {"entry": async_redact_data(entry.as_dict(), TO_REDACT)}

    router: ARDevice = hass.data[DOMAIN][entry.entry_id][ASUSROUTER]

    # Gather information how this device is represented in Home Assistant
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    hass_device = device_registry.async_get_device(
        identifiers=router.device_info["identifiers"]
    )
    if not hass_device:
        return data

    data["device"] = {
        **async_redact_data(hass_device.dict_repr, TO_REDACT_DEV),
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
            # Remove sensitive info from attributes.
            if "attributes" in state_dict:
                state_dict["attributes"] = async_redact_data(
                    dict(state_dict["attributes"]), TO_REDACT_ATTRS
                )
            # Remove sensitive info from sensors states.
            if entity_entry.original_name in TO_REDACT_STATE:
                state_dict = async_redact_data(state_dict, "state")

        data["device"]["entities"][entity_entry.entity_id] = {
            **async_redact_data(
                entity_entry.as_partial_dict,
                TO_REDACT,
            ),
            "state": state_dict,
        }

    for device in router.devices.values():
        data["device"]["tracked_devices"].append(
            {
                "name": device.name,
                "ip_address": device.ip_address,
                "last_activity": device.extra_state_attributes[
                    DEVICE_ATTRIBUTE_LAST_ACTIVITY
                ]
                if DEVICE_ATTRIBUTE_LAST_ACTIVITY in device.extra_state_attributes
                else None,
            }
        )

    return data
