"""AsusRouter clients module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from asusrouter.modules.clients import (
    ARClient,
    ARClientsCountSourceUniversal,
    ARClientsSourceUniversal,
)
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import format_mac

from ..clients import async_clean_up_clients, get_client_device_info
from ..entity import (
    ARButtonDescription,
    ARSensorDescription,
    ARTrackerDescription,
)
from ..helpers import to_str

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)


def _is_served(bridge: ARBridge) -> bool:
    """Check whether the device serves its own clients."""

    return not bridge.is_node


def _get_ip(client: ARClient) -> str | None:
    """Get the IP address of a connected client."""

    connection = client.connection
    return None if connection is None else to_str(connection.ip)


BUTTONS: tuple[ARButtonDescription, ...] = (
    ARButtonDescription(
        key="clean_up_clients",
        translation_key="clean_up_clients",
        source=ARClientsSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Clean up clients",
        # The device reports its clients, not keyed by its MAC
        data_fn=lambda data: data or None,
        press_fn=async_clean_up_clients,
        supported_fn=_is_served,
        entity_category=EntityCategory.CONFIG,
    ),
)

SENSORS: tuple[ARSensorDescription, ...] = (
    ARSensorDescription(
        key="connected_devices",
        translation_key="connected_devices",
        source=ARClientsCountSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Connected Devices",
        # The device reports the clients of every node it serves
        data_fn=lambda data: data or None,
        value_fn=lambda counts: sum(counts.values()),
        supported_fn=_is_served,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

TRACKERS: tuple[ARTrackerDescription, ...] = (
    ARTrackerDescription(
        key="client",
        translation_key="client",
        source=ARClientsSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        # The device reports its clients, not keyed by its MAC
        data_fn=lambda data: data,
        keys_fn=lambda clients: clients,
        item_fn=lambda clients, mac: clients.get(mac),
        unique_id_fn=lambda mac: format_mac(str(mac)),
        device_info_fn=get_client_device_info,
        value_fn=lambda client: client.online,
        ip_fn=_get_ip,
        hostname_fn=lambda client: client.name,
        supported_fn=_is_served,
        entity_registry_enabled_default=False,
    ),
)
