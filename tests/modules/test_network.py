"""Tests for the network module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.network import (
    ARNetworkAction,
    ARNetworkBackend,
    ARNetworkField,
    ARNetworkHandle,
    ARNetworkSchedule,
    ARNetworkSourceUniversal,
    ARNetworkType,
)
from asusrouter.modules.wifi import ARWiFiBand, ARWiFiMacFilterMode
from asusrouter.tools.identifiers import Ssid
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.entity import AREntityDescription
from custom_components.asusrouter.modules.network import (
    BINARY_SENSORS,
    SWITCHES,
    _is_served,
)

DESCRIPTIONS: dict[str, AREntityDescription] = {
    description.key: description
    for description in (*BINARY_SENSORS, *SWITCHES)
}
BACKHAUL_SENSOR = DESCRIPTIONS["backhaul_network"]
(SWITCH,) = SWITCHES

SDN_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.SDN, sdn_idx=3, ap_prefix="apm", ap_idx=2
)
GUEST_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.LEGACY, units=((0, 1), (1, 1))
)
BACKHAUL_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.SDN, sdn_idx=2, ap_prefix="apm", ap_idx=1
)
# The main network of the legacy firmware is switched by its radio
MAIN_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.LEGACY, units=((0, None),)
)


def _get_profile(
    handle: ARNetworkHandle,
    ssid: str,
    fields: dict[ARNetworkField, Any] | None = None,
) -> dict[ARNetworkField, Any]:
    """Create a network profile."""

    return {
        ARNetworkField.AP_ISOLATE: False,
        ARNetworkField.BANDS: [ARWiFiBand.BAND_2G1, ARWiFiBand.BAND_5G1],
        ARNetworkField.ENABLED: True,
        ARNetworkField.HANDLE: handle,
        ARNetworkField.HIDDEN: False,
        ARNetworkField.MAC_FILTER_MODE: ARWiFiMacFilterMode.DISABLED,
        ARNetworkField.SSID: Ssid(ssid),
        ARNetworkField.WIFI7: True,
        **(fields or {}),
    }


SDN = _get_profile(SDN_HANDLE, "Example")
GUEST = _get_profile(
    GUEST_HANDLE,
    "Example Guest",
    {
        ARNetworkField.LAN_ACCESS: False,
        ARNetworkField.SCHEDULE_MODE: ARNetworkSchedule.ONE_TIME,
    },
)
BACKHAUL = _get_profile(BACKHAUL_HANDLE, "Example Backhaul")
MAIN = _get_profile(MAIN_HANDLE, "Example Main")

DATA: dict[ARNetworkType, list[dict[ARNetworkField, Any]]] = {
    ARNetworkType.GUEST: [GUEST, {ARNetworkField.SSID: Ssid("No handle")}],
    ARNetworkType.MAINBH: [BACKHAUL],
    ARNetworkType.MAINFH: [SDN, MAIN],
}
SDN_KEY = ("sdn", 3)
GUEST_KEY = ("legacy", 0, 1)


def _get_network(key: Any, data: Any = None) -> Any:
    """Get the network of a key."""

    assert SWITCH.item_fn is not None
    return SWITCH.item_fn(DATA if data is None else data, key)


@pytest.mark.parametrize(
    ("key", "unique_id_name", "name"),
    [
        (("sdn", 1), "Network SDN 1", "SDN 1"),
        (("sdn", 32), "Network SDN 32", "SDN 32"),
        (("legacy", 0, 1), "Network 0.1", "0.1"),
        (("legacy", 5, 7), "Network 5.7", "5.7"),
    ],
)
def test_unique_id(key: Any, unique_id_name: str, name: str) -> None:
    """Test that every network keeps the unique_id of its slot."""

    assert SWITCH.unique_id_fn is not None
    assert SWITCH.placeholders_fn is not None
    assert SWITCH.unique_id_fn(key) == unique_id_name
    # The handle names the network until its SSID is read
    assert SWITCH.placeholders_fn(key) == {"name": name}


@pytest.mark.parametrize("description", [BACKHAUL_SENSOR, SWITCH])
def test_description(description: AREntityDescription) -> None:
    """Test that every network entity is disabled and served by its device."""

    assert description.source is ARNetworkSourceUniversal
    assert description.entity_registry_enabled_default is False
    assert description.supported_fn is _is_served


def test_categories() -> None:
    """Test that the switches configure and the backhaul is diagnostic."""

    assert BACKHAUL_SENSOR.entity_category is EntityCategory.DIAGNOSTIC
    assert SWITCH.entity_category is EntityCategory.CONFIG
    assert SWITCH.remove_missing is True


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (AROperationMode.ACCESS_POINT, True),
        (AROperationMode.AIMESH_NODE, False),
        (AROperationMode.ROUTER, True),
    ],
)
def test_is_served(mode: AROperationMode, expected: bool) -> None:
    """Test that a node does not serve the networks of its router."""

    bridge = Mock(is_node=mode is AROperationMode.AIMESH_NODE)

    assert _is_served(bridge) is expected


@pytest.mark.parametrize(
    ("data", "keys"),
    [(DATA, {SDN_KEY, GUEST_KEY}), (None, set()), ({}, set())],
)
def test_keys(data: Any, keys: set[Any]) -> None:
    """Test that every network gets a switch, but the backhaul and main."""

    assert SWITCH.keys_fn is not None
    assert SWITCH.data_fn is not None
    assert set(SWITCH.keys_fn(SWITCH.data_fn(data))) == keys


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (SDN_KEY, SDN),
        (GUEST_KEY, GUEST),
        # Only the first unit of its bands keys a network
        (("legacy", 1, 1), None),
        (("sdn", 1), None),
    ],
)
def test_item(key: Any, expected: Any) -> None:
    """Test that every switch finds its own network."""

    network = _get_network(key)

    assert (None if network is None else network.profile) is expected


@pytest.mark.parametrize(
    ("data", "expected"), [(DATA, BACKHAUL), (None, None), ({}, None)]
)
def test_backhaul(data: Any, expected: Any) -> None:
    """Test that the backhaul sensor finds the backhaul."""

    assert BACKHAUL_SENSOR.data_fn is not None
    network = BACKHAUL_SENSOR.data_fn(data)

    assert (None if network is None else network.profile) is expected


@pytest.mark.parametrize("state", [True, False])
def test_switch(state: bool) -> None:
    """Test that a network reports and switches its state by its handle."""

    network = _get_network(
        GUEST_KEY,
        {ARNetworkType.GUEST: [{**GUEST, ARNetworkField.ENABLED: state}]},
    )

    assert SWITCH.value_fn(network) is state
    assert SWITCH.name_fn is not None
    assert SWITCH.name_fn(network) == "Example Guest"
    action = SWITCH.action_fn(state, network)
    assert isinstance(action, ARNetworkAction)
    assert action.handle is GUEST_HANDLE
    assert action.state is state


def test_name_missing() -> None:
    """Test that a network without an SSID reports no name."""

    network = _get_network(
        SDN_KEY, {ARNetworkType.MAINFH: [{ARNetworkField.HANDLE: SDN_HANDLE}]}
    )

    assert SWITCH.name_fn is not None
    assert SWITCH.name_fn(network) is None


def test_attributes() -> None:
    """Test that a network reports its settings, never its password."""

    assert SWITCH.attributes_fn is not None
    assert BACKHAUL_SENSOR.attributes_fn is not None
    assert BACKHAUL_SENSOR.data_fn is not None

    assert SWITCH.attributes_fn(_get_network(GUEST_KEY)) == {
        "ap_isolate": False,
        "bands": ["2g1", "5g1"],
        "hidden": False,
        "lan_access": False,
        "mac_filter_mode": "disabled",
        "schedule_mode": "one_time",
        "type": "guest",
        "wifi7": True,
    }
    assert BACKHAUL_SENSOR.attributes_fn(BACKHAUL_SENSOR.data_fn(DATA)) == {
        "ap_isolate": False,
        "bands": ["2g1", "5g1"],
        "hidden": False,
        "lan_access": None,
        "mac_filter_mode": "disabled",
        "schedule_mode": None,
        "type": "MAINBH",
        "wifi7": True,
    }


def test_attributes_unknown() -> None:
    """Test that unknown modes and types report nothing."""

    assert SWITCH.attributes_fn is not None
    profile = {
        ARNetworkField.HANDLE: SDN_HANDLE,
        ARNetworkField.MAC_FILTER_MODE: ARWiFiMacFilterMode.UNKNOWN,
        ARNetworkField.SCHEDULE_MODE: ARNetworkSchedule.UNKNOWN,
    }

    attributes = SWITCH.attributes_fn(
        _get_network(SDN_KEY, {ARNetworkType.UNKNOWN: [profile]})
    )

    assert attributes["bands"] == []
    assert attributes["mac_filter_mode"] is None
    assert attributes["schedule_mode"] is None
    assert attributes["type"] is None
