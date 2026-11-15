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

COUNT = 13
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
CLIENTS: dict[ARVpnProtocol, dict[int, dict[ARVpnClientField, Any]]] = {
    ARVpnProtocol.OPENVPN: {3: CLASSIC_CLIENT},
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
SERVERS: dict[ARVpnProtocol, dict[int, dict[ARVpnServerField, Any]]] = {
    ARVpnProtocol.OPENVPN: {2: {ARVpnServerField.STATE: ARVpnState.CONNECTED}},
    ARVpnProtocol.WIREGUARD: {1: SERVER},
}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "source", "category"),
    [
        (
            "openvpn_client_1",
            "OpenVPN Client 1",
            ARVpnClientSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "wireguard_client_5",
            "WireGuard Client 5",
            ARVpnClientSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "openvpn_server_2",
            "OpenVPN Server 2",
            ARVpnServerSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "wireguard_server_1",
            "WireGuard Server 1",
            ARVpnServerSourceUniversal,
            EntityCategory.CONFIG,
        ),
        (
            "openvpn_client_1_state",
            "OpenVPN Client 1 State",
            ARVpnClientSourceUniversal,
            EntityCategory.DIAGNOSTIC,
        ),
        (
            "openvpn_server_2_state",
            "OpenVPN Server 2 State",
            ARVpnServerSourceUniversal,
            EntityCategory.DIAGNOSTIC,
        ),
    ],
)
def test_description(
    key: str, unique_id_name: str, source: Any, category: EntityCategory
) -> None:
    """Test that every VPN entity keeps its unique_id and default."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.source is source
    # A client is named by its profile, the unit until it is read
    placeholder = "name" if "client" in key else "unit"
    unit = key.removesuffix("_state")[-1]
    assert description.translation_placeholders == {placeholder: unit}
    assert description.entity_category is category
    assert description.entity_registry_enabled_default is False


def test_descriptions() -> None:
    """Test that every client unit and server of each protocol is listed."""

    # 5 clients of each protocol, 2 OpenVPN servers and 1 WireGuard server
    assert len(SWITCHES) == COUNT
    # A WireGuard server reports no state of its own
    assert len(SENSORS) == COUNT - 1
    assert "wireguard_server_2" not in DESCRIPTIONS
    assert "wireguard_server_1_state" not in DESCRIPTIONS


@pytest.mark.parametrize("is_router", [True, False])
def test_supported(is_router: bool) -> None:
    """Test that only a router has the VPN."""

    for description in DESCRIPTIONS.values():
        assert description.supported_fn is not None
        assert description.supported_fn(Mock(is_router=is_router)) is is_router


@pytest.mark.parametrize(
    ("key", "data", "expected"),
    [
        # A VPN Fusion client is keyed by its server
        ("wireguard_client_2", CLIENTS, FUSION_CLIENT),
        ("wireguard_client_1", CLIENTS, None),
        # A classic client is keyed by its unit
        ("openvpn_client_3", CLIENTS, CLASSIC_CLIENT),
        ("openvpn_client_1", CLIENTS, None),
        ("wireguard_server_1", SERVERS, SERVER),
        ("openvpn_server_1", SERVERS, None),
        ("openvpn_server_1", {ARVpnProtocol.OPENVPN: {1: {}}}, None),
        ("openvpn_client_3", {}, None),
        ("openvpn_client_3", None, None),
        ("openvpn_server_2", None, None),
    ],
)
def test_data(key: str, data: Any, expected: Any) -> None:
    """Test that every switch and state finds its own unit."""

    keys = (key, f"{key}_state")
    for description in (DESCRIPTIONS[k] for k in keys if k in DESCRIPTIONS):
        assert description.data_fn is not None
        assert description.data_fn(data) is expected


@pytest.mark.parametrize(
    ("key", "profile", "state"),
    [
        ("wireguard_client_2", FUSION_CLIENT, True),
        ("openvpn_client_3", CLASSIC_CLIENT, False),
        ("wireguard_server_1", SERVER, True),
        ("openvpn_server_2", {}, None),
    ],
)
def test_value(key: str, profile: dict[Any, Any], state: bool | None) -> None:
    """Test that every switch reports whether its unit is enabled."""

    description = DESCRIPTIONS[key]

    assert description.exists_fn is not None
    assert description.exists_fn(profile) is True
    assert description.value_fn(profile) is state


def test_client_name() -> None:
    """Test that a client is named by its profile."""

    for key in ("wireguard_client_2", "wireguard_client_2_state"):
        description = DESCRIPTIONS[key]
        assert description.name_fn is not None
        assert description.name_fn(FUSION_CLIENT) == "Example"
        assert description.name_fn(CLASSIC_CLIENT) is None
    assert DESCRIPTIONS["wireguard_server_1"].name_fn is None
    assert DESCRIPTIONS["openvpn_server_2_state"].name_fn is None


@pytest.mark.parametrize("state", [True, False])
@pytest.mark.parametrize(
    ("key", "action_type", "protocol", "unit"),
    [
        ("wireguard_client_2", ARVpnClientAction, ARVpnProtocol.WIREGUARD, 2),
        ("openvpn_client_3", ARVpnClientAction, ARVpnProtocol.OPENVPN, 3),
        ("openvpn_server_2", ARVpnServerAction, ARVpnProtocol.OPENVPN, 2),
        ("wireguard_server_1", ARVpnServerAction, ARVpnProtocol.WIREGUARD, 1),
    ],
)
def test_action(
    key: str,
    action_type: type[Any],
    protocol: ARVpnProtocol,
    unit: int,
    state: bool,
) -> None:
    """Test that every switch toggles its own unit."""

    action = DESCRIPTIONS[key].action_fn(state, {})

    assert isinstance(action, action_type)
    assert action.protocol is protocol
    assert action.unit == unit
    assert action.state is state


def test_switch_no_attributes() -> None:
    """Test that no switch exposes attributes."""

    for description in SWITCHES:
        assert description.attributes_fn is None


@pytest.mark.parametrize(
    ("key", "profile", "state"),
    [
        ("wireguard_client_2_state", FUSION_CLIENT, "connected"),
        ("openvpn_client_3_state", CLASSIC_CLIENT, "error"),
        (
            "openvpn_server_2_state",
            SERVERS[ARVpnProtocol.OPENVPN][2],
            "connected",
        ),
        ("openvpn_server_2_state", {}, None),
    ],
)
def test_state(key: str, profile: dict[Any, Any], state: str | None) -> None:
    """Test that every state sensor reports its option."""

    description = DESCRIPTIONS[key]

    assert description.device_class is SensorDeviceClass.ENUM
    assert description.options == [
        "error",
        "disconnected",
        "connecting",
        "connected",
    ]
    assert description.value_fn(profile) == state


@pytest.mark.parametrize(
    ("key", "profile", "attributes"),
    [
        ("wireguard_client_2_state", FUSION_CLIENT, {"state_reason": None}),
        (
            "openvpn_client_3_state",
            CLASSIC_CLIENT,
            {"connected_since": None, "state_reason": 4},
        ),
        (
            "openvpn_server_2_state",
            {ARVpnServerField.ERRNO: 1},
            {"errno": 1},
        ),
    ],
)
def test_state_attributes(
    key: str, profile: dict[Any, Any], attributes: dict[str, Any]
) -> None:
    """Test that a state reports why, never keys or settings."""

    description = DESCRIPTIONS[key]

    assert description.attributes_fn is not None
    assert description.attributes_fn(profile) == attributes
