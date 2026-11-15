"""AsusRouter clients module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from asusrouter.modules.clients import ARClient, ARClientsSourceUniversal
from asusrouter.tools.identifiers import MacAddress
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)

from .const import DOMAIN

if TYPE_CHECKING:
    from . import ARConfigEntry


def get_client_device_info(
    via_device_id: str, key: MacAddress, client: ARClient | None
) -> DeviceInfo:
    """Get the device of a client, linked to the device reporting it."""

    client_mac = format_mac(str(key))
    return DeviceInfo(
        connections={(CONNECTION_NETWORK_MAC, client_mac)},
        name=(client.name if client is not None else None) or client_mac,
        via_device_id=via_device_id,
    )


def _get_reported(config_entry: ARConfigEntry) -> set[str] | None:
    """Get the MACs of the reported clients, None when not read."""

    coordinator = config_entry.runtime_data.coordinators.get(
        ARClientsSourceUniversal
    )
    # An empty list is no proof that every client is gone
    if (
        coordinator is None
        or not coordinator.last_update_success
        or not coordinator.data
    ):
        return None

    return {format_mac(str(mac)) for mac in coordinator.data}


def _get_client_mac(unique_id: str, prefix: str) -> str | None:
    """Get the client MAC of an entity of a client, None for another one."""

    if not unique_id.startswith(prefix):
        return None

    # The client MAC follows the device MAC, a suffix names the entity
    candidate = unique_id[len(prefix) :].partition("_")[0]
    mac = MacAddress.from_value_safe(candidate)
    return None if mac is None else format_mac(str(mac))


def _get_client_entries(
    hass: HomeAssistant, config_entry: ARConfigEntry
) -> dict[str, list[er.RegistryEntry]]:
    """Get the registry entries of the entities of every client."""

    mac = config_entry.runtime_data.bridge.identity.mac
    if mac is None:
        return {}

    prefix = f"{format_mac(str(mac))}_"
    clients: dict[str, list[er.RegistryEntry]] = {}
    for entry in er.async_entries_for_config_entry(
        er.async_get(hass), config_entry.entry_id
    ):
        if (
            client_mac := _get_client_mac(entry.unique_id, prefix)
        ) is not None:
            clients.setdefault(client_mac, []).append(entry)

    return clients


@callback
def async_clean_up_clients(
    hass: HomeAssistant, config_entry: ARConfigEntry
) -> None:
    """Remove the clients no longer reported, but those still in use."""

    if (reported := _get_reported(config_entry)) is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="clients_unread"
        )

    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    for client_mac, entries in _get_client_entries(hass, config_entry).items():
        # A client with an enabled entity is kept until it returns
        if client_mac in reported or any(
            entry.disabled_by is None for entry in entries
        ):
            continue

        for entry in entries:
            entity_registry.async_remove(entry.entity_id)
        # A device shared with another integration stays for it
        if device := device_registry.async_get_device(
            connections={(CONNECTION_NETWORK_MAC, client_mac)}
        ):
            device_registry.async_update_device(
                device.id, remove_config_entry_id=config_entry.entry_id
            )


def can_remove_client(
    config_entry: ARConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Check whether a client device is no longer reported."""

    reported = _get_reported(config_entry)
    if reported is None:
        return False

    return all(
        connection[1] not in reported
        for connection in device.connections
        if connection[0] == CONNECTION_NETWORK_MAC
    )
