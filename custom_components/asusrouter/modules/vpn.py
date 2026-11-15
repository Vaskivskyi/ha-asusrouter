"""AsusRouter VPN module."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from typing import Any

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

# Units of the clients and servers of every protocol
_CLIENT_UNITS = range(1, 6)
_SERVER_UNITS: dict[ARVpnProtocol, range] = {
    ARVpnProtocol.OPENVPN: range(1, 3),
    ARVpnProtocol.WIREGUARD: range(1, 2),
}
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


def _find_client(
    data: Any, protocol: ARVpnProtocol, unit: int
) -> dict[ARVpnClientField, Any] | None:
    """Find the client of the protocol and unit, None when not reported."""

    profiles = data.get(protocol) if isinstance(data, dict) else None
    if not isinstance(profiles, dict):
        return None

    return next(
        (
            profile
            for profile in profiles.values()
            if _get_unit(profile) == unit
        ),
        None,
    )


def _find_server(
    data: Any, protocol: ARVpnProtocol, unit: int
) -> dict[ARVpnServerField, Any] | None:
    """Find the server of the protocol and unit, None when not reported."""

    profiles = data.get(protocol) if isinstance(data, dict) else None
    if not isinstance(profiles, dict):
        return None

    profile: dict[ARVpnServerField, Any] | None = profiles.get(unit) or None
    return profile


def _get_client_args(protocol: ARVpnProtocol, unit: int) -> dict[str, Any]:
    """Get the arguments shared by the entities of a client."""

    return {
        # The unit names the client until its profile name is read
        "translation_placeholders": {"name": str(unit)},
        "source": ARVpnClientSourceUniversal,
        "update_interval": UPDATE_INTERVAL,
        # The device reports its clients, not keyed by its MAC
        "data_fn": lambda data: _find_client(data, protocol, unit),
        "name_fn": lambda profile: to_str(profile.get(ARVpnClientField.NAME)),
        # Only the units the device reports
        "exists_fn": lambda _: True,
        "supported_fn": lambda bridge: bridge.is_router,
        "entity_registry_enabled_default": False,
    }


def _get_server_args(protocol: ARVpnProtocol, unit: int) -> dict[str, Any]:
    """Get the arguments shared by the entities of a server."""

    return {
        "translation_placeholders": {"unit": str(unit)},
        "source": ARVpnServerSourceUniversal,
        "update_interval": UPDATE_INTERVAL,
        # The device reports its servers, not keyed by its MAC
        "data_fn": lambda data: _find_server(data, protocol, unit),
        # Only the units the device reports
        "exists_fn": lambda _: True,
        "supported_fn": lambda bridge: bridge.is_router,
        "entity_registry_enabled_default": False,
    }


def _get_client_switch(
    protocol: ARVpnProtocol, unit: int
) -> ARSwitchDescription:
    """Get the description of the switch of a client."""

    return ARSwitchDescription(
        key=f"{protocol.value}_client_{unit}",
        translation_key=f"{protocol.value}_client",
        unique_id_name=f"{_LABELS[protocol]} Client {unit}",
        value_fn=lambda profile: profile.get(ARVpnClientField.ENABLED),
        action_fn=lambda state, _: ARVpnClientAction(
            protocol, state, unit=unit
        ),
        entity_category=EntityCategory.CONFIG,
        **_get_client_args(protocol, unit),
    )


def _get_client_state(
    protocol: ARVpnProtocol, unit: int
) -> ARSensorDescription:
    """Get the description of the state sensor of a client."""

    return ARSensorDescription(
        key=f"{protocol.value}_client_{unit}_state",
        translation_key=f"{protocol.value}_client_state",
        unique_id_name=f"{_LABELS[protocol]} Client {unit} State",
        value_fn=lambda profile: _get_state(
            profile.get(ARVpnClientField.STATE)
        ),
        attributes_fn=lambda profile: _get_attributes(
            profile, _CLIENT_ATTRIBUTES[protocol]
        ),
        device_class=SensorDeviceClass.ENUM,
        options=_STATE_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_get_client_args(protocol, unit),
    )


def _get_server_switch(
    protocol: ARVpnProtocol, unit: int
) -> ARSwitchDescription:
    """Get the description of the switch of a server."""

    return ARSwitchDescription(
        key=f"{protocol.value}_server_{unit}",
        translation_key=f"{protocol.value}_server",
        unique_id_name=f"{_LABELS[protocol]} Server {unit}",
        value_fn=lambda profile: profile.get(ARVpnServerField.ENABLED),
        action_fn=lambda state, _: ARVpnServerAction(
            protocol, state, unit=unit
        ),
        entity_category=EntityCategory.CONFIG,
        **_get_server_args(protocol, unit),
    )


def _get_server_state(
    protocol: ARVpnProtocol, unit: int
) -> ARSensorDescription:
    """Get the description of the state sensor of a server."""

    fields = _SERVER_ATTRIBUTES[protocol]
    return ARSensorDescription(
        key=f"{protocol.value}_server_{unit}_state",
        translation_key=f"{protocol.value}_server_state",
        unique_id_name=f"{_LABELS[protocol]} Server {unit} State",
        value_fn=lambda profile: _get_state(
            profile.get(ARVpnServerField.STATE)
        ),
        attributes_fn=lambda profile: _get_attributes(profile, fields),
        device_class=SensorDeviceClass.ENUM,
        options=_STATE_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_get_server_args(protocol, unit),
    )


_CLIENTS = [(protocol, unit) for protocol in _LABELS for unit in _CLIENT_UNITS]
_SERVERS = [
    (protocol, unit)
    for protocol, units in _SERVER_UNITS.items()
    for unit in units
]

SENSORS: tuple[ARSensorDescription, ...] = (
    *(_get_client_state(protocol, unit) for protocol, unit in _CLIENTS),
    *(
        _get_server_state(protocol, unit)
        for protocol, unit in _SERVERS
        if protocol in _SERVER_ATTRIBUTES
    ),
)
SWITCHES: tuple[ARSwitchDescription, ...] = (
    *(_get_client_switch(protocol, unit) for protocol, unit in _CLIENTS),
    *(_get_server_switch(protocol, unit) for protocol, unit in _SERVERS),
)
