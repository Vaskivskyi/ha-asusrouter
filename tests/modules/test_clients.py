"""Tests for the clients module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.clients import (
    ARClient,
    ARClientConnection,
    ARClientsCountSourceUniversal,
    ARClientsSourceUniversal,
)
from asusrouter.tools.identifiers import IpAddress, MacAddress
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.clients import (
    async_clean_up_clients,
    get_client_device_info,
)
from custom_components.asusrouter.modules.clients import (
    BUTTONS,
    SENSORS,
    TRACKERS,
    _is_served,
)

CLIENT_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:10")
NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
(CLEAN_UP,) = BUTTONS
(CONNECTED,) = SENSORS
(TRACKER,) = TRACKERS


@pytest.mark.parametrize("is_node", [True, False])
def test_is_served(is_node: bool) -> None:
    """Test that a node does not serve the clients of its router."""

    assert _is_served(Mock(is_node=is_node)) is not is_node


@pytest.mark.parametrize("description", [CLEAN_UP, CONNECTED, TRACKER])
def test_supported(description: Any) -> None:
    """Test that every client entity is served by its device only."""

    assert description.supported_fn is _is_served


def test_clean_up() -> None:
    """Test that the button cleans up the clients in Home Assistant."""

    assert CLEAN_UP.unique_id_name == "Clean up clients"
    assert CLEAN_UP.source is ARClientsSourceUniversal
    assert CLEAN_UP.press_fn is async_clean_up_clients
    assert CLEAN_UP.action_fn is None
    assert CLEAN_UP.entity_category is EntityCategory.CONFIG
    assert CLEAN_UP.data_fn is not None
    assert CLEAN_UP.data_fn({}) is None
    data = {CLIENT_MAC: Mock()}
    assert CLEAN_UP.data_fn(data) is data


@pytest.mark.parametrize(
    ("data", "expected"),
    [({NODE_MAC: 3, CLIENT_MAC: 4}, 7), ({NODE_MAC: 0}, 0)],
)
def test_connected_devices(data: dict[MacAddress, int], expected: int) -> None:
    """Test that the clients of every node are added up."""

    assert CONNECTED.unique_id_name == "Connected Devices"
    assert CONNECTED.source is ARClientsCountSourceUniversal
    assert CONNECTED.data_fn is not None
    assert CONNECTED.value_fn(CONNECTED.data_fn(data)) == expected


@pytest.mark.parametrize("data", [{}, None])
def test_connected_devices_unread(data: Any) -> None:
    """Test that nothing is counted before the clients are read."""

    assert CONNECTED.data_fn is not None
    assert CONNECTED.data_fn(data) is None


def test_tracker() -> None:
    """Test that every reported client gets a disabled tracker."""

    client = ARClient(
        mac=CLIENT_MAC,
        online=True,
        name="Phone",
        connection=ARClientConnection(ip=IpAddress.from_value("192.0.2.10")),
    )
    data = {CLIENT_MAC: client}

    assert TRACKER.source is ARClientsSourceUniversal
    assert TRACKER.entity_registry_enabled_default is False
    assert TRACKER.remove_missing is False
    assert TRACKER.device_info_fn is get_client_device_info
    assert TRACKER.data_fn is not None
    assert TRACKER.keys_fn is not None
    assert TRACKER.item_fn is not None
    assert TRACKER.unique_id_fn is not None
    assert set(TRACKER.keys_fn(TRACKER.data_fn(data))) == {CLIENT_MAC}
    assert TRACKER.item_fn(data, CLIENT_MAC) is client
    assert TRACKER.unique_id_fn(CLIENT_MAC) == "aa:bb:cc:dd:ee:10"
    assert TRACKER.value_fn(client) is True
    assert TRACKER.ip_fn(client) == "192.0.2.10"
    assert TRACKER.hostname_fn(client) == "Phone"


def test_tracker_offline() -> None:
    """Test that an offline client has no IP address."""

    assert TRACKER.ip_fn(ARClient(mac=CLIENT_MAC)) is None
