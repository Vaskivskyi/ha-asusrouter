"""Tests for the device tracker module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from asusrouter.modules.clients import ARClient, ARClientConnection
from asusrouter.tools.identifiers import IpAddress, MacAddress
from homeassistant.helpers.device_registry import DeviceInfo
import pytest

from custom_components.asusrouter import device_tracker
from custom_components.asusrouter.device_tracker import (
    ARTracker,
    async_setup_entry,
)
from custom_components.asusrouter.modules import TRACKERS

pytestmark = pytest.mark.asyncio

COMPONENT = Path("custom_components/asusrouter")
ROUTER = MacAddress.from_value("AA:BB:CC:DD:EE:01")
CLIENT_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:10")
CLIENT = ARClient(
    mac=CLIENT_MAC,
    online=True,
    name="Phone",
    connection=ARClientConnection(ip=IpAddress.from_value("192.168.1.10")),
)


async def test_setup_entry() -> None:
    """Test that every client tracker is added."""

    entry = Mock()
    add_entities = Mock()

    with patch.object(device_tracker, "async_setup_entities") as setup:
        await async_setup_entry(Mock(), entry, add_entities)

    setup.assert_called_once_with(entry, TRACKERS, ARTracker, add_entities)


def _get_tracker(data: Any, success: bool = True) -> ARTracker:
    """Create the tracker of the test client."""

    coordinator = Mock(data=data, last_update_success=success)
    with patch(
        "custom_components.asusrouter.entity.dr."
        "async_get_device_id_by_identifier",
        return_value="router",
    ):
        return ARTracker(coordinator, TRACKERS[0], ROUTER, CLIENT_MAC)


async def test_tracker() -> None:
    """Test that a tracker reports its client."""

    tracker = _get_tracker({CLIENT_MAC: CLIENT})

    # The same unique_id as before, not the MAC alone
    assert tracker.unique_id == "aa:bb:cc:dd:ee:01_aa:bb:cc:dd:ee:10"
    assert tracker.available is True
    assert tracker.is_connected is True
    assert tracker.ip_address == "192.168.1.10"
    assert tracker.mac_address == "aa:bb:cc:dd:ee:10"
    assert tracker.hostname == "Phone"
    assert tracker.name is None
    assert isinstance(tracker.device_info, DeviceInfo)
    assert tracker.device_info.via_device_id == "router"


async def test_tracker_offline() -> None:
    """Test that an offline client is away without an IP address."""

    tracker = _get_tracker(
        {CLIENT_MAC: ARClient(mac=CLIENT_MAC, online=False)}
    )

    assert tracker.is_connected is False
    assert tracker.ip_address is None
    assert tracker.hostname is None


async def test_tracker_forgotten() -> None:
    """Test that a client the device no longer reports is away."""

    tracker = _get_tracker({})

    assert tracker.available is True
    assert tracker.is_connected is False
    assert tracker.ip_address is None
    assert tracker.hostname is None


async def test_tracker_unread() -> None:
    """Test that a failed read makes the tracker unavailable."""

    assert _get_tracker({CLIENT_MAC: CLIENT}, success=False).available is False


async def test_tracker_icons() -> None:
    """Test that a tracker has an icon for its state."""

    icons = json.loads((COMPONENT / "icons.json").read_text("utf-8"))

    assert icons["entity"]["device_tracker"]["client"] == {
        "default": "mdi:lan-disconnect",
        "state": {"home": "mdi:lan-connect"},
    }
