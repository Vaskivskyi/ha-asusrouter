"""AsusRouter VPN module."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from typing import Any, NamedTuple

from asusrouter.modules.vpn import (
    ARVpnClientAction,
    ARVpnClientField,
    ARVpnClientSourceUniversal,
    ARVpnProtocol,
    ARVpnServerAction,
    ARVpnServerField,
    ARVpnServerSourceUniversal,
    ARVpnState,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory

from ..entity import ARSensorDescription, ARSwitchDescription
from ..helpers import to_str

UPDATE_INTERVAL = timedelta(seconds=30)

# Names of the protocols in the unique_id names
_LABELS: dict[ARVpnProtocol, str] = {
    ARVpnProtocol.OPENVPN: "OpenVPN",
    ARVpnProtocol.WIREGUARD: "WireGuard",
}

_STATE_OPTIONS = [
    state.name.lower()
    for state in ARVpnState
    if state is not ARVpnState.UNKNOWN
]
# Attributes of the state of a client or server by protocol
_CLIENT_ATTRIBUTES: dict[ARVpnProtocol, tuple[ARVpnClientField, ...]] = {
    ARVpnProtocol.OPENVPN: (
        ARVpnClientField.CONNECTED_SINCE,
        ARVpnClientField.STATE_REASON,
    ),
    ARVpnProtocol.WIREGUARD: (ARVpnClientField.STATE_REASON,),
}
# A WireGuard server reports only the state of its peers
_SERVER_ATTRIBUTES: dict[ARVpnProtocol, tuple[ARVpnServerField, ...]] = {
    ARVpnProtocol.OPENVPN: (ARVpnServerField.ERRNO,),
}


class _Unit(NamedTuple):
    """A client or server profile with the unit it is controlled by."""

    unit: int
    profile: dict[Any, Any]


def _get_state(value: Any) -> str | None:
    """Get the state as an option, None when unknown."""

    return (
        value.name.lower()
        if isinstance(value, ARVpnState) and value is not ARVpnState.UNKNOWN
        else None
    )


def _get_attributes(
    data: dict[Any, Any], fields: Iterable[Any]
) -> dict[str, Any]:
    """Get the attributes of the fields."""

    return {field.value: data.get(field) for field in fields}


def _get_unit(profile: dict[ARVpnClientField, Any]) -> Any:
    """Get the unit of a client of its protocol."""

    # A VPN Fusion client is placed by its position, its unit is the server
    if ARVpnClientField.VPNC_INDEX in profile:
        return profile.get(ARVpnClientField.SERVER)

    return profile.get(ARVpnClientField.UNIT)


def _get_profiles(data: Any, protocol: ARVpnProtocol) -> dict[Any, Any]:
    """Get the profiles of the protocol, empty when none is reported."""

    profiles = data.get(protocol) if isinstance(data, dict) else None
    return profiles if isinstance(profiles, dict) else {}


def _get_clients(data: Any, protocol: ARVpnProtocol) -> dict[int, _Unit]:
    """Get the clients of the protocol by their unit."""

    clients: dict[int, _Unit] = {}
    for profile in _get_profiles(data, protocol).values():
        if isinstance(unit := _get_unit(profile), int):
            clients[unit] = _Unit(unit, profile)
    return clients


def _get_servers(data: Any, protocol: ARVpnProtocol) -> dict[int, _Unit]:
    """Get the servers of the protocol by their unit."""

    return {
        unit: _Unit(unit, profile)
        for unit, profile in _get_profiles(data, protocol).items()
        if isinstance(unit, int) and profile
    }


def _get_client_args(protocol: ARVpnProtocol) -> dict[str, Any]:
    """Get the arguments shared by the entities of the clients."""

    return {
        "source": ARVpnClientSourceUniversal,
        "update_interval": UPDATE_INTERVAL,
        # The device reports its clients, not keyed by its MAC
        "data_fn": lambda data: data,
        "keys_fn": lambda data: _get_clients(data, protocol),
        "item_fn": lambda data, unit: _get_clients(data, protocol).get(unit),
        # The unit names a client until its profile name is read
        "placeholders_fn": lambda unit: {"name": str(unit)},
        "name_fn": lambda client: to_str(
            client.profile.get(ARVpnClientField.NAME)
        ),
        "remove_missing": True,
        "supported_fn": lambda bridge: bridge.is_router,
        "entity_registry_enabled_default": False,
    }


def _get_server_args(protocol: ARVpnProtocol) -> dict[str, Any]:
    """Get the arguments shared by the entities of the servers."""

    return {
        "source": ARVpnServerSourceUniversal,
        "update_interval": UPDATE_INTERVAL,
        # The device reports its servers, not keyed by its MAC
        "data_fn": lambda data: data,
        "keys_fn": lambda data: _get_servers(data, protocol),
        "item_fn": lambda data, unit: _get_servers(data, protocol).get(unit),
        "placeholders_fn": lambda unit: {"unit": str(unit)},
        "remove_missing": True,
        "supported_fn": lambda bridge: bridge.is_router,
        "entity_registry_enabled_default": False,
    }


def _get_client_switch(protocol: ARVpnProtocol) -> ARSwitchDescription:
    """Get the description of the switches of the clients."""

    label = _LABELS[protocol]
    return ARSwitchDescription(
        key=f"{protocol.value}_client",
        translation_key=f"{protocol.value}_client",
        unique_id_fn=lambda unit: f"{label} Client {unit}",
        value_fn=lambda client: client.profile.get(ARVpnClientField.ENABLED),
        action_fn=lambda state, client: ARVpnClientAction(
            protocol, state, unit=client.unit
        ),
        entity_category=EntityCategory.CONFIG,
        **_get_client_args(protocol),
    )


def _get_client_state(protocol: ARVpnProtocol) -> ARSensorDescription:
    """Get the description of the state sensors of the clients."""

    label = _LABELS[protocol]
    fields = _CLIENT_ATTRIBUTES[protocol]
    return ARSensorDescription(
        key=f"{protocol.value}_client_state",
        translation_key=f"{protocol.value}_client_state",
        unique_id_fn=lambda unit: f"{label} Client {unit} State",
        value_fn=lambda client: _get_state(
            client.profile.get(ARVpnClientField.STATE)
        ),
        attributes_fn=lambda client: _get_attributes(client.profile, fields),
        device_class=SensorDeviceClass.ENUM,
        options=_STATE_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_get_client_args(protocol),
    )


def _get_server_switch(protocol: ARVpnProtocol) -> ARSwitchDescription:
    """Get the description of the switches of the servers."""

    label = _LABELS[protocol]
    return ARSwitchDescription(
        key=f"{protocol.value}_server",
        translation_key=f"{protocol.value}_server",
        unique_id_fn=lambda unit: f"{label} Server {unit}",
        value_fn=lambda server: server.profile.get(ARVpnServerField.ENABLED),
        action_fn=lambda state, server: ARVpnServerAction(
            protocol, state, unit=server.unit
        ),
        entity_category=EntityCategory.CONFIG,
        **_get_server_args(protocol),
    )


def _get_server_state(protocol: ARVpnProtocol) -> ARSensorDescription:
    """Get the description of the state sensors of the servers."""

    label = _LABELS[protocol]
    fields = _SERVER_ATTRIBUTES[protocol]
    return ARSensorDescription(
        key=f"{protocol.value}_server_state",
        translation_key=f"{protocol.value}_server_state",
        unique_id_fn=lambda unit: f"{label} Server {unit} State",
        value_fn=lambda server: _get_state(
            server.profile.get(ARVpnServerField.STATE)
        ),
        attributes_fn=lambda server: _get_attributes(server.profile, fields),
        device_class=SensorDeviceClass.ENUM,
        options=_STATE_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_get_server_args(protocol),
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    *(_get_client_state(protocol) for protocol in _LABELS),
    *(_get_server_state(protocol) for protocol in _SERVER_ATTRIBUTES),
)
SWITCHES: tuple[ARSwitchDescription, ...] = (
    *(_get_client_switch(protocol) for protocol in _LABELS),
    *(_get_server_switch(protocol) for protocol in _LABELS),
)
