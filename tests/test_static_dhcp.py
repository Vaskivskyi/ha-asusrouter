"""Tests for static DHCP helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import pytest

from custom_components.asusrouter.button import ClientStaticDHCPReserveButton
from custom_components.asusrouter.const import DNS, IP, LIST, MAC, ROUTER
from custom_components.asusrouter.router import ARDevice
from custom_components.asusrouter.services import _get_entity_ids


@dataclass
class Lease:
    """Static DHCP lease fixture."""

    mac: str
    ip: str
    dns: str = ""
    hostname: str = ""


def _router() -> ARDevice:
    """Create a static-DHCP-capable router shell."""

    router = ARDevice.__new__(ARDevice)
    router.hass = Mock()
    router.bridge = Mock()
    router._mac = "AA:AA:AA:AA:AA:AA"
    router._mode = ROUTER
    router._static_dhcp_lock = asyncio.Lock()
    router._static_dhcp_leases = []
    router._sensor_coordinator = {}
    return router


@pytest.mark.asyncio
async def test_reserve_current_ip_rejects_existing_different_ip() -> None:
    """Reserve current IP should not move an existing reservation."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        return_value=[Lease("00:11:22:33:44:55", "192.168.50.20")]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock()

    with (
        patch("custom_components.asusrouter.router.async_dispatcher_send"),
        pytest.raises(ServiceValidationError),
    ):
        await router.async_reserve_current_ip(
            "00:11:22:33:44:55",
            "192.168.50.21",
        )

    router.bridge.async_set_static_dhcp_lease.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_static_dhcp_lease_rejects_duplicate_ip() -> None:
    """Manual set should reject IPs already reserved for another MAC."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        return_value=[Lease("00:11:22:33:44:55", "192.168.50.20")]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock()

    with (
        patch("custom_components.asusrouter.router.async_dispatcher_send"),
        pytest.raises(ServiceValidationError),
    ):
        await router.async_set_static_dhcp_lease(
            "AA:BB:CC:DD:EE:FF",
            "192.168.50.20",
        )

    router.bridge.async_set_static_dhcp_lease.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_static_dhcp_lease_verifies_after_write() -> None:
    """Manual set reads leases again and caches verified data."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        side_effect=[
            [],
            [Lease("00:11:22:33:44:55", "192.168.50.20", hostname="Printer")],
        ]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock(return_value=True)

    with patch("custom_components.asusrouter.router.async_dispatcher_send"):
        result = await router.async_set_static_dhcp_lease(
            "00:11:22:33:44:55",
            "192.168.50.20",
            hostname="Printer",
        )

    assert result[MAC] == "00:11:22:33:44:55"
    assert result[IP] == "192.168.50.20"
    assert router.static_dhcp_leases == [
        {
            MAC: "00:11:22:33:44:55",
            IP: "192.168.50.20",
            "dns": "",
            "hostname": "Printer",
        }
    ]
    router.bridge.async_get_static_dhcp_leases.assert_awaited()
    router.bridge.async_set_static_dhcp_lease.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_static_dhcp_lease_rejects_field_mismatch() -> None:
    """Manual set fails if optional fields do not match after apply."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        side_effect=[
            [],
            [Lease("00:11:22:33:44:55", "192.168.50.20", hostname="Printer")],
        ]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock(return_value=True)

    with (
        patch("custom_components.asusrouter.router.async_dispatcher_send"),
        pytest.raises(HomeAssistantError, match="did not match"),
    ):
        await router.async_set_static_dhcp_lease(
            "00:11:22:33:44:55",
            "192.168.50.20",
            dns="1.1.1.1",
            hostname="Printer",
        )


@pytest.mark.asyncio
async def test_set_static_dhcp_lease_raises_when_verify_fails() -> None:
    """Manual set fails if the applied lease does not appear."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        side_effect=[[], []]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock(return_value=True)

    with (
        patch("custom_components.asusrouter.router.async_dispatcher_send"),
        pytest.raises(HomeAssistantError),
    ):
        await router.async_set_static_dhcp_lease(
            "00:11:22:33:44:55",
            "192.168.50.20",
        )


@pytest.mark.asyncio
async def test_reserve_current_ip_same_lease_is_noop() -> None:
    """Reserve current IP should no-op when the reservation already matches."""

    router = _router()
    router.bridge.async_get_static_dhcp_leases = AsyncMock(
        return_value=[Lease("00:11:22:33:44:55", "192.168.50.20")]
    )
    router.bridge.async_set_static_dhcp_lease = AsyncMock()

    with patch("custom_components.asusrouter.router.async_dispatcher_send"):
        result = await router.async_reserve_current_ip(
            "00:11:22:33:44:55",
            "192.168.50.20",
        )

    assert result[MAC] == "00:11:22:33:44:55"
    assert result[IP] == "192.168.50.20"
    assert router._static_dhcp_payload(router.static_dhcp_leases)[LIST] == [
        result
    ]
    router.bridge.async_set_static_dhcp_lease.assert_not_awaited()


def test_reserve_current_ip_button_unavailable_for_duplicate_ip() -> None:
    """Reserve button is unavailable when another MAC owns the current IP."""

    router = _router()
    router._static_dhcp_leases = [
        {
            MAC: "00:11:22:33:44:55",
            IP: "192.168.50.20",
            DNS: "",
            "hostname": "",
        }
    ]
    client = Mock()
    client.mac_address = "AA:BB:CC:DD:EE:FF"
    client.ip_address = "192.168.50.20"
    client.name = "Client"

    button = ClientStaticDHCPReserveButton(router, client)

    assert button.available is False


def test_get_entity_ids_filters_indirect_non_trackers() -> None:
    """Device targets should not expand to unrelated sensors or buttons."""

    selected = Mock(
        referenced={"device_tracker.explicit"},
        indirectly_referenced={
            "button.reserve_ip",
            "device_tracker.indirect",
            "sensor.reservation_count",
        },
    )
    entries = {
        "button.reserve_ip": Mock(domain="button", platform="asusrouter"),
        "device_tracker.indirect": Mock(
            domain="device_tracker", platform="asusrouter"
        ),
        "sensor.reservation_count": Mock(
            domain="sensor", platform="asusrouter"
        ),
    }
    registry = Mock()
    registry.async_get.side_effect = entries.get
    call = Mock(data={"device_id": ["client-device"]})

    with (
        patch(
            "custom_components.asusrouter.services."
            "target_helpers.async_extract_referenced_entity_ids",
            return_value=selected,
        ),
        patch(
            "custom_components.asusrouter.services.er.async_get",
            return_value=registry,
        ),
    ):
        result = _get_entity_ids(Mock(), call)

    assert result == [
        "device_tracker.explicit",
        "device_tracker.indirect",
    ]
