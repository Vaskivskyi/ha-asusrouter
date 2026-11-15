"""Tests for the clients module."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock, patch

from asusrouter.modules.clients import ARClient, ARClientsSourceUniversal
from asusrouter.tools.identifiers import MacAddress
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
import pytest

from custom_components.asusrouter import clients
from custom_components.asusrouter.clients import (
    _get_client_mac,
    async_clean_up_clients,
    can_remove_client,
    get_client_device_info,
)

pytestmark = pytest.mark.asyncio

ENTRY_ID = "entry"
ROUTER_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
ROUTER = "aa:bb:cc:dd:ee:01"
REPORTED = "aa:bb:cc:dd:ee:10"
WANTED = "aa:bb:cc:dd:ee:11"
FORGOTTEN = "aa:bb:cc:dd:ee:12"


def _get_entry(
    data: Any = None, success: bool = True, mac: Any = ROUTER_MAC
) -> Mock:
    """Create the entry of a router reporting its clients."""

    coordinator = Mock(
        data={MacAddress.from_value(REPORTED): Mock()}
        if data is None
        else data,
        last_update_success=success,
    )
    entry = Mock(entry_id=ENTRY_ID)
    entry.runtime_data.coordinators = {ARClientsSourceUniversal: coordinator}
    entry.runtime_data.bridge.identity.mac = mac

    return entry


def _get_registry_entry(unique_id: str, enabled: bool = False) -> Mock:
    """Create an entity registry entry."""

    return Mock(
        unique_id=unique_id,
        entity_id=f"entity.{unique_id}",
        disabled_by=None if enabled else "integration",
    )


@pytest.fixture(name="registries")
def fixture_registries() -> Iterator[tuple[Mock, Mock, Mock]]:
    """Mock the entity and device registries."""

    with (
        patch.object(clients, "er") as er,
        patch.object(clients, "dr") as dr,
    ):
        yield er, er.async_get.return_value, dr.async_get.return_value


async def test_get_client_device_info() -> None:
    """Test that a client device has its MAC and is linked to its router."""

    client = ARClient(mac=MacAddress.from_value(REPORTED), name="Phone")

    info = get_client_device_info("router", client.mac, client)

    assert info.connections == {(CONNECTION_NETWORK_MAC, REPORTED)}
    assert info.name == "Phone"
    assert info.via_device_id == "router"


@pytest.mark.parametrize(
    "client", [None, ARClient(mac=MacAddress.from_value(REPORTED))]
)
async def test_get_client_device_info_unnamed(client: Any) -> None:
    """Test that a client without a name is named by its MAC."""

    info = get_client_device_info(
        "router", MacAddress.from_value(REPORTED), client
    )

    assert info.name == REPORTED


@pytest.mark.parametrize(
    ("unique_id", "expected"),
    [
        (f"{ROUTER}_{REPORTED}", REPORTED),
        (f"{ROUTER}_{REPORTED}_internet_access", REPORTED),
        # An entity of the router itself
        (f"{ROUTER}_firmware_update", None),
        # An entity of another device
        (f"{REPORTED}_connected", None),
    ],
)
async def test_get_client_mac(unique_id: str, expected: str | None) -> None:
    """Test that only an entity of a client has its client MAC."""

    assert _get_client_mac(unique_id, f"{ROUTER}_") == expected


async def test_clean_up_clients(
    registries: tuple[Mock, Mock, Mock],
) -> None:
    """Test that only forgotten clients without enabled entities go."""

    er, entity_registry, device_registry = registries
    er.async_entries_for_config_entry.return_value = [
        _get_registry_entry(f"{ROUTER}_{REPORTED}"),
        _get_registry_entry(f"{ROUTER}_{WANTED}"),
        _get_registry_entry(
            f"{ROUTER}_{WANTED}_internet_access", enabled=True
        ),
        _get_registry_entry(f"{ROUTER}_{FORGOTTEN}"),
        _get_registry_entry(f"{ROUTER}_firmware_update"),
    ]
    device_registry.async_get_device.return_value = Mock(id="device")

    async_clean_up_clients(Mock(), _get_entry())

    entity_registry.async_remove.assert_called_once_with(
        f"entity.{ROUTER}_{FORGOTTEN}"
    )
    device_registry.async_get_device.assert_called_once_with(
        connections={(CONNECTION_NETWORK_MAC, FORGOTTEN)}
    )
    # A device shared with another integration stays for it
    device_registry.async_update_device.assert_called_once_with(
        "device", remove_config_entry_id=ENTRY_ID
    )


async def test_clean_up_clients_without_device(
    registries: tuple[Mock, Mock, Mock],
) -> None:
    """Test that a forgotten client without a device loses its entities."""

    er, entity_registry, device_registry = registries
    er.async_entries_for_config_entry.return_value = [
        _get_registry_entry(f"{ROUTER}_{FORGOTTEN}")
    ]
    device_registry.async_get_device.return_value = None

    async_clean_up_clients(Mock(), _get_entry())

    entity_registry.async_remove.assert_called_once()
    device_registry.async_update_device.assert_not_called()


async def test_clean_up_clients_without_mac(
    registries: tuple[Mock, Mock, Mock],
) -> None:
    """Test that a device without a MAC has no client entities."""

    er, entity_registry, _ = registries

    async_clean_up_clients(Mock(), _get_entry(mac=None))

    er.async_entries_for_config_entry.assert_not_called()
    entity_registry.async_remove.assert_not_called()


@pytest.mark.parametrize(
    ("data", "success"),
    [
        ({MacAddress.from_value(REPORTED): Mock()}, False),
        # An empty list is no proof that every client is gone
        ({}, True),
    ],
)
async def test_clean_up_clients_unread(
    registries: tuple[Mock, Mock, Mock], data: Any, success: bool
) -> None:
    """Test that nothing is removed before the clients are read."""

    _, entity_registry, _ = registries

    with pytest.raises(HomeAssistantError) as error:
        async_clean_up_clients(Mock(), _get_entry(data, success))

    assert error.value.translation_key == "clients_unread"
    entity_registry.async_remove.assert_not_called()


async def test_clean_up_clients_no_source(
    registries: tuple[Mock, Mock, Mock],
) -> None:
    """Test that a device without clients cannot clean them up."""

    entry = _get_entry()
    entry.runtime_data.coordinators = {}

    with pytest.raises(HomeAssistantError):
        async_clean_up_clients(Mock(), entry)


@pytest.mark.parametrize(
    ("mac", "expected"),
    [(FORGOTTEN, True), (REPORTED, False)],
)
async def test_can_remove_client(mac: str, expected: bool) -> None:
    """Test that only a client the device no longer reports can be removed."""

    device = Mock(
        connections={(CONNECTION_NETWORK_MAC, mac), ("other", "connection")}
    )

    assert can_remove_client(_get_entry(), device) is expected


async def test_can_remove_client_unread() -> None:
    """Test that no client is removed before the clients are read."""

    device = Mock(connections={(CONNECTION_NETWORK_MAC, FORGOTTEN)})

    assert can_remove_client(_get_entry(success=False), device) is False
