"""Tests for the VPN module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.vpn import (
    ARVpnClientAction,
    ARVpnClientField,
    ARVpnClientSourceUniversal,
    ARVpnPeerField,
    ARVpnProtocol,
    ARVpnServerAction,
    ARVpnServerField,
    ARVpnServerSourceUniversal,
    ARVpnState,
)
from asusrouter.tools.identifiers import IpAddress, IpInterface
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.modules.vpn import SENSORS, SWITCHES

DESCRIPTIONS: dict[str, Any] = {
    description.key: description for description in (*SENSORS, *SWITCHES)
}

# A VPN Fusion client, placed by its position with its unit as the server
FUSION_CLIENT: dict[ARVpnClientField, Any] = {
    ARVpnClientField.ADDRESS: IpInterface.from_value("10.0.0.2/32"),
    ARVpnClientField.ALLOWED_IPS: [IpInterface.from_value("0.0.0.0/0")],
    ARVpnClientField.DEFAULT_WAN: False,
    ARVpnClientField.ENABLED: True,
    ARVpnClientField.ENDPOINT_ADDRESS: IpAddress.from_value("192.0.2.1"),
    ARVpnClientField.ENDPOINT_PORT: 51820,
    ARVpnClientField.NAME: "Example",
    ARVpnClientField.PRIVATE_KEY: "secret",
    ARVpnClientField.PROTOCOL: ARVpnProtocol.WIREGUARD,
    ARVpnClientField.SERVER: 2,
    ARVpnClientField.STATE: ARVpnState.CONNECTED,
    ARVpnClientField.UNIT: 0,
    ARVpnClientField.VPNC_INDEX: 5,
}
# A classic client, placed by its unit with its server host
CLASSIC_CLIENT: dict[ARVpnClientField, Any] = {
    ARVpnClientField.ENABLED: False,
    ARVpnClientField.PASSWORD: "secret",
    ARVpnClientField.PROTOCOL: ARVpnProtocol.OPENVPN,
    ARVpnClientField.SERVER: "vpn.example.com",
    ARVpnClientField.STATE: ARVpnState.ERROR,
    ARVpnClientField.STATE_REASON: 4,
    ARVpnClientField.UNIT: 3,
}
# A client the device reports without a unit
UNPLACED_CLIENT: dict[ARVpnClientField, Any] = {
    ARVpnClientField.ENABLED: False,
}
CLIENTS: dict[ARVpnProtocol, dict[int, dict[ARVpnClientField, Any]]] = {
    ARVpnProtocol.OPENVPN: {3: CLASSIC_CLIENT, 4: UNPLACED_CLIENT},
    ARVpnProtocol.WIREGUARD: {5: FUSION_CLIENT},
}

PEER: dict[ARVpnPeerField, Any] = {
    ARVpnPeerField.ADDRESS: [IpInterface.from_value("10.6.0.2/32")],
    ARVpnPeerField.ENABLED: True,
    ARVpnPeerField.NAME: "Phone",
    ARVpnPeerField.STATE: ARVpnState.DISCONNECTED,
}
SERVER: dict[ARVpnServerField, Any] = {
    ARVpnServerField.ADDRESS: IpInterface.from_value("10.6.0.1/24"),
    ARVpnServerField.CLIENTS: [PEER],
    ARVpnServerField.ENABLED: True,
    ARVpnServerField.PORT: 51820,
    ARVpnServerField.PRIVATE_KEY: "secret",
    ARVpnServerField.STATE: ARVpnState.UNKNOWN,
}
OPENVPN_SERVER: dict[ARVpnServerField, Any] = {
    ARVpnServerField.ERRNO: 1,
    ARVpnServerField.STATE: ARVpnState.CONNECTED,
}
SERVERS: dict[ARVpnProtocol, dict[int, dict[ARVpnServerField, Any]]] = {
    # An empty server is not reported
    ARVpnProtocol.OPENVPN: {1: {}, 2: OPENVPN_SERVER},
    ARVpnProtocol.WIREGUARD: {1: SERVER},
}


def _get_item(key: str, data: Any, unit: int) -> Any:
    """Get the item of a unit from the data of a description."""

    description = DESCRIPTIONS[key]
    return description.item_fn(description.data_fn(data), unit)


@pytest.mark.parametrize(
    ("key", "unique_id_name", "placeholders", "source", "category"),
    [
        (
            "openvpn_client",
            "OpenVPN Client 3",
            {"name": "3"},
            ARVpnClientSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "wireguard_client",
            "WireGuard Client 3",
            {"name": "3"},
            ARVpnClientSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "openvpn_server",
            "OpenVPN Server 3",
            {"unit": "3"},
            ARVpnServerSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "wireguard_server",
            "WireGuard Server 3",
            {"unit": "3"},
            ARVpnServerSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "openvpn_client_state",
            "OpenVPN Client 3 State",
            {"name": "3"},
            ARVpnClientSourceUniversal,
            EntityCategory.DIAGNOSTIC,
        ),
        (
            "openvpn_server_state",
            "OpenVPN Server 3 State",
            {"unit": "3"},
            ARVpnServerSourceUniversal,
            EntityCategory.DIAGNOSTIC,
        ),
    ],
)
def test_description(
    key: str,
    unique_id_name: str,
    placeholders: dict[str, str],
    source: Any,
    category: EntityCategory,
) -> None:
    """Test that every VPN entity keeps its unique_id and default."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_fn(3) == unique_id_name
    assert description.placeholders_fn(3) == placeholders
    assert description.source is source
    assert description.remove_missing is True
    assert description.entity_category is category
    assert description.entity_registry_enabled_default is False


def test_descriptions() -> None:
    """Test that the clients and servers of every protocol are described."""

    # A WireGuard server reports no state of its own
    assert set(DESCRIPTIONS) == {
        "openvpn_client",
        "openvpn_client_state",
        "openvpn_server",
        "openvpn_server_state",
        "wireguard_client",
        "wireguard_client_state",
        "wireguard_server",
    }


@pytest.mark.parametrize("is_router", [True, False])
def test_supported(is_router: bool) -> None:
    """Test that only a router has the VPN."""

    for description in DESCRIPTIONS.values():
        assert description.supported_fn is not None
        assert description.supported_fn(Mock(is_router=is_router)) is is_router


@pytest.mark.parametrize(
    ("key", "data", "keys"),
    [
        # A VPN Fusion client is keyed by its server
        ("wireguard_client", CLIENTS, {2}),
        # A classic client is keyed by its unit, one without a unit is not
        ("openvpn_client", CLIENTS, {3}),
        ("openvpn_server", SERVERS, {2}),
        ("wireguard_server", SERVERS, {1}),
        ("openvpn_client", {}, set()),
        ("openvpn_client", {ARVpnProtocol.OPENVPN: None}, set()),
        ("openvpn_server", None, set()),
    ],
)
def test_keys(key: str, data: Any, keys: set[int]) -> None:
    """Test that every description reads the units the device reports."""

    for description in (DESCRIPTIONS[key], DESCRIPTIONS.get(f"{key}_state")):
        if description is None:
            continue
        assert set(description.keys_fn(description.data_fn(data))) == keys


@pytest.mark.parametrize(
    ("key", "data", "unit", "profile"),
    [
        ("wireguard_client", CLIENTS, 2, FUSION_CLIENT),
        ("openvpn_client", CLIENTS, 3, CLASSIC_CLIENT),
        ("wireguard_server", SERVERS, 1, SERVER),
        ("openvpn_server", SERVERS, 2, OPENVPN_SERVER),
    ],
)
def test_item(key: str, data: Any, unit: int, profile: Any) -> None:
    """Test that every unit finds its profile."""

    item = _get_item(key, data, unit)

    assert item.unit == unit
    assert item.profile is profile
    assert _get_item(key, data, 9) is None


@pytest.mark.parametrize(
    ("key", "data", "unit", "state"),
    [
        ("wireguard_client", CLIENTS, 2, True),
        ("openvpn_client", CLIENTS, 3, False),
        ("wireguard_server", SERVERS, 1, True),
        ("openvpn_server", SERVERS, 2, None),
    ],
)
def test_value(key: str, data: Any, unit: int, state: bool | None) -> None:
    """Test that every switch reports whether its unit is enabled."""

    item = _get_item(key, data, unit)

    assert DESCRIPTIONS[key].value_fn(item) is state


def test_client_name() -> None:
    """Test that a client is named by its profile."""

    for key in ("wireguard_client", "wireguard_client_state"):
        description = DESCRIPTIONS[key]
        assert description.name_fn is not None
        assert description.name_fn(_get_item(key, CLIENTS, 2)) == "Example"
    # A classic client has no profile name
    description = DESCRIPTIONS["openvpn_client"]
    assert description.name_fn is not None
    assert description.name_fn(_get_item("openvpn_client", CLIENTS, 3)) is None
    assert DESCRIPTIONS["wireguard_server"].name_fn is None
    assert DESCRIPTIONS["openvpn_server_state"].name_fn is None


@pytest.mark.parametrize("state", [True, False])
@pytest.mark.parametrize(
    ("key", "data", "action_type", "protocol", "unit"),
    [
        (
            "wireguard_client",
            CLIENTS,
            ARVpnClientAction,
            ARVpnProtocol.WIREGUARD,
            2,
        ),
        (
            "openvpn_client",
            CLIENTS,
            ARVpnClientAction,
            ARVpnProtocol.OPENVPN,
            3,
        ),
        (
            "openvpn_server",
            SERVERS,
            ARVpnServerAction,
            ARVpnProtocol.OPENVPN,
            2,
        ),
        (
            "wireguard_server",
            SERVERS,
            ARVpnServerAction,
            ARVpnProtocol.WIREGUARD,
            1,
        ),
    ],
)
def test_action(
    key: str,
    data: Any,
    action_type: type[Any],
    protocol: ARVpnProtocol,
    unit: int,
    state: bool,
) -> None:
    """Test that every switch toggles its own unit."""

    item = _get_item(key, data, unit)
    action = DESCRIPTIONS[key].action_fn(state, item)

    assert isinstance(action, action_type)
    assert action.protocol is protocol
    assert action.unit == unit
    assert action.state is state


def test_switch_no_attributes() -> None:
    """Test that no switch exposes attributes."""

    for description in SWITCHES:
        assert description.attributes_fn is None


@pytest.mark.parametrize(
    ("key", "data", "unit", "state"),
    [
        ("wireguard_client_state", CLIENTS, 2, "connected"),
        ("openvpn_client_state", CLIENTS, 3, "error"),
        ("openvpn_server_state", SERVERS, 2, "connected"),
    ],
)
def test_state(key: str, data: Any, unit: int, state: str | None) -> None:
    """Test that every state sensor reports its option."""

    description = DESCRIPTIONS[key]

    assert description.device_class is SensorDeviceClass.ENUM
    assert description.options == [
        "error",
        "disconnected",
        "connecting",
        "connected",
    ]
    assert description.value_fn(_get_item(key, data, unit)) == state


def test_state_unknown() -> None:
    """Test that an unknown state reports no option."""

    description = DESCRIPTIONS["openvpn_server_state"]
    item = _get_item(
        "openvpn_server_state",
        {ARVpnProtocol.OPENVPN: {1: {ARVpnServerField.ENABLED: True}}},
        1,
    )

    assert description.value_fn(item) is None


@pytest.mark.parametrize(
    ("key", "data", "unit", "attributes"),
    [
        ("wireguard_client_state", CLIENTS, 2, {"state_reason": None}),
        (
            "openvpn_client_state",
            CLIENTS,
            3,
            {"connected_since": None, "state_reason": 4},
        ),
        ("openvpn_server_state", SERVERS, 2, {"errno": 1}),
    ],
)
def test_state_attributes(
    key: str, data: Any, unit: int, attributes: dict[str, Any]
) -> None:
    """Test that a state reports why, never keys or settings."""

    description = DESCRIPTIONS[key]

    assert description.attributes_fn is not None
    assert description.attributes_fn(_get_item(key, data, unit)) == attributes
