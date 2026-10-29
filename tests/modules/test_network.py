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

SDN_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.SDN, sdn_idx=3, ap_prefix="apm", ap_idx=2
)
GUEST_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.LEGACY, units=((0, 1), (1, 1))
)
BACKHAUL_HANDLE = ARNetworkHandle(
    backend=ARNetworkBackend.SDN, sdn_idx=2, ap_prefix="apm", ap_idx=1
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

DATA: dict[ARNetworkType, list[dict[ARNetworkField, Any]]] = {
    ARNetworkType.GUEST: [GUEST],
    ARNetworkType.MAINBH: [BACKHAUL],
    ARNetworkType.MAINFH: [SDN],
}


@pytest.mark.parametrize(
    ("key", "unique_id_name"),
    [
        ("backhaul_network", "Backhaul network"),
        ("network_sdn_1", "Network SDN 1"),
        ("network_sdn_32", "Network SDN 32"),
        ("network_0_1", "Network 0.1"),
        ("network_5_7", "Network 5.7"),
    ],
)
def test_description(key: str, unique_id_name: str) -> None:
    """Test that every network is keyed by its slot on the device."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.source is ARNetworkSourceUniversal
    assert description.entity_registry_enabled_default is False
    assert description.supported_fn is _is_served


def test_categories() -> None:
    """Test that the switches configure and the backhaul is diagnostic."""

    assert DESCRIPTIONS["backhaul_network"].entity_category is (
        EntityCategory.DIAGNOSTIC
    )
    assert all(s.entity_category is EntityCategory.CONFIG for s in SWITCHES)


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

    bridge = Mock()
    bridge.identity.operation_mode = mode

    assert _is_served(bridge) is expected


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("backhaul_network", BACKHAUL),
        ("network_sdn_3", SDN),
        ("network_0_1", GUEST),
        # Only the first unit of its bands keys a network
        ("network_1_1", None),
        ("network_sdn_1", None),
    ],
)
def test_data(key: str, expected: Any) -> None:
    """Test that every entity finds its own network."""

    description = DESCRIPTIONS[key]

    assert description.data_fn is not None
    network = description.data_fn(DATA)
    assert (None if network is None else network.profile) is expected


@pytest.mark.parametrize("key", ["backhaul_network", "network_sdn_3"])
@pytest.mark.parametrize("data", [None, {}])
def test_data_unread(key: str, data: Any) -> None:
    """Test that nothing is found before the networks are read."""

    description = DESCRIPTIONS[key]

    assert description.data_fn is not None
    assert description.data_fn(data) is None


def test_backhaul_switch() -> None:
    """Test that the backhaul never gets a switch."""

    description = DESCRIPTIONS["network_sdn_2"]

    assert description.data_fn is not None
    assert description.exists_fn is not None
    assert description.exists_fn(description.data_fn(DATA)) is False
    switch = DESCRIPTIONS["network_sdn_3"]
    assert switch.data_fn is not None
    assert switch.exists_fn is not None
    assert switch.exists_fn(switch.data_fn(DATA)) is True


@pytest.mark.parametrize("state", [True, False])
def test_switch(state: bool) -> None:
    """Test that a network reports and switches its state by its handle."""

    description = next(s for s in SWITCHES if s.key == "network_0_1")
    assert description.data_fn is not None
    network = description.data_fn(
        {ARNetworkType.GUEST: [{**GUEST, ARNetworkField.ENABLED: state}]}
    )

    assert description.value_fn(network) is state
    assert description.name_fn is not None
    assert description.name_fn(network) == "Example Guest"
    action = description.action_fn(state, network)
    assert isinstance(action, ARNetworkAction)
    assert action.handle is GUEST_HANDLE
    assert action.state is state


def test_name_missing() -> None:
    """Test that a network without an SSID reports no name."""

    description = DESCRIPTIONS["network_sdn_3"]
    assert description.data_fn is not None
    network = description.data_fn(
        {ARNetworkType.MAINFH: [{ARNetworkField.HANDLE: SDN_HANDLE}]}
    )

    assert description.name_fn is not None
    assert description.name_fn(network) is None


@pytest.mark.parametrize(
    ("key", "attributes"),
    [
        (
            "network_0_1",
            {
                "ap_isolate": False,
                "bands": ["2g1", "5g1"],
                "hidden": False,
                "lan_access": False,
                "mac_filter_mode": "disabled",
                "schedule_mode": "one_time",
                "type": "guest",
                "wifi7": True,
            },
        ),
        (
            "backhaul_network",
            {
                "ap_isolate": False,
                "bands": ["2g1", "5g1"],
                "hidden": False,
                "lan_access": None,
                "mac_filter_mode": "disabled",
                "schedule_mode": None,
                "type": "MAINBH",
                "wifi7": True,
            },
        ),
    ],
)
def test_attributes(key: str, attributes: dict[str, Any]) -> None:
    """Test that a network reports its settings, never its password."""

    description = DESCRIPTIONS[key]
    assert description.data_fn is not None
    assert description.attributes_fn is not None

    assert description.attributes_fn(description.data_fn(DATA)) == attributes


def test_attributes_unknown() -> None:
    """Test that unknown modes and types report nothing."""

    description = DESCRIPTIONS["network_sdn_3"]
    assert description.data_fn is not None
    assert description.attributes_fn is not None
    profile = {
        ARNetworkField.HANDLE: SDN_HANDLE,
        ARNetworkField.MAC_FILTER_MODE: ARWiFiMacFilterMode.UNKNOWN,
        ARNetworkField.SCHEDULE_MODE: ARNetworkSchedule.UNKNOWN,
    }

    attributes = description.attributes_fn(
        description.data_fn({ARNetworkType.UNKNOWN: [profile]})
    )

    assert attributes["bands"] == []
    assert attributes["mac_filter_mode"] is None
    assert attributes["schedule_mode"] is None
    assert attributes["type"] is None
