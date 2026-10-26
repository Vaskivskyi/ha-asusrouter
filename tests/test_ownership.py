"""Tests for the ownership module."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, Mock, call, patch

from asusrouter.modules.common.device import AROperationMode
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import ownership
from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.ownership import (
    _find_mesh_node,
    _is_foreign,
    async_hand_back,
    async_take_over,
    get_device_info,
    get_owned_devices,
)

pytestmark = pytest.mark.asyncio

ENTRY_ID = "entry"
OTHER_ENTRY_ID = "other_entry"
FOREIGN_ENTRY_ID = "foreign_entry"

NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
OTHER_NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
NODE_IDENTIFIER = (DOMAIN, str(NODE_MAC))


def _get_hass() -> Mock:
    """Create Home Assistant with entries of this and another integration."""

    entries = {
        ENTRY_ID: Mock(entry_id=ENTRY_ID, domain=DOMAIN),
        OTHER_ENTRY_ID: Mock(entry_id=OTHER_ENTRY_ID, domain=DOMAIN),
        FOREIGN_ENTRY_ID: Mock(entry_id=FOREIGN_ENTRY_ID, domain="other"),
    }

    hass = Mock()
    hass.config_entries.async_get_entry = Mock(side_effect=entries.get)
    hass.config_entries.async_reload = AsyncMock()

    return hass


def _get_entry(entry_id: str = ENTRY_ID, nodes: Any = ()) -> Mock:
    """Create a config entry serving the given nodes."""

    entry = Mock(entry_id=entry_id)
    entry.runtime_data.bridge.nodes = [Mock(mac=mac) for mac in nodes]

    return entry


def _get_device(
    config_entry_id: str = OTHER_ENTRY_ID,
    via_device_id: str | None = None,
    device_id: str = "device",
) -> Mock:
    """Create a device of the node owned by the config entry."""

    return Mock(
        id=device_id,
        config_entry_id=config_entry_id,
        identifiers={NODE_IDENTIFIER},
        via_device_id=via_device_id,
    )


@pytest.fixture
def registries() -> Iterator[tuple[Mock, Mock]]:
    """Mock the device and entity registry modules."""

    with (
        patch.object(ownership, "dr") as dr,
        patch.object(ownership, "er") as er,
    ):
        yield dr, er


@pytest.mark.parametrize(
    ("config_entry_id", "expected"),
    [
        (ENTRY_ID, False),
        (OTHER_ENTRY_ID, True),
        # Another integration sharing the identifier
        (FOREIGN_ENTRY_ID, False),
        ("removed_entry", False),
    ],
)
async def test_is_foreign(config_entry_id: str, expected: bool) -> None:
    """Test that only devices of other entries of ours are foreign."""

    device = _get_device(config_entry_id)

    assert _is_foreign(_get_hass(), device, _get_entry()) is expected


@pytest.mark.parametrize(
    ("devices", "expected"),
    [
        ([], {}),
        # Connected directly by another entry
        ([_get_device()], {NODE_MAC: "device"}),
        # Served through another router only
        ([_get_device(via_device_id="router")], {}),
        ([_get_device(ENTRY_ID)], {}),
    ],
)
async def test_get_owned_devices(
    registries: tuple[Mock, Mock],
    devices: list[Mock],
    expected: dict[MacAddress, str],
) -> None:
    """Test that a node added as its own entry is owned by it."""

    dr, _ = registries
    dr.async_get.return_value.async_get_devices.side_effect = (
        lambda identifiers: devices if NODE_IDENTIFIER in identifiers else []
    )

    owned = get_owned_devices(
        _get_hass(), _get_entry(), [NODE_MAC, OTHER_NODE_MAC]
    )

    assert {mac: device.id for mac, device in owned.items()} == expected


async def test_find_mesh_node() -> None:
    """Test that the device is found in the topology of another entry."""

    hass = _get_hass()
    entry = _get_entry()
    node = Mock()
    router = _get_entry(OTHER_ENTRY_ID)
    router.runtime_data.bridge.identity.aimesh.get = Mock(
        side_effect={NODE_MAC: node}.get
    )
    hass.config_entries.async_loaded_entries.return_value = [entry, router]

    assert _find_mesh_node(hass, entry, NODE_MAC) is node
    assert _find_mesh_node(hass, entry, OTHER_NODE_MAC) is None
    # The own topology is read by the bridge itself
    entry.runtime_data.bridge.identity.aimesh.get.assert_not_called()
    hass.config_entries.async_loaded_entries.assert_called_with(DOMAIN)


def _get_bridge(own: Any, mode: AROperationMode) -> Mock:
    """Create a bridge of a device with or without its own AiMesh node."""

    bridge = Mock()
    bridge.identity.mac = NODE_MAC
    bridge.identity.operation_mode = mode
    bridge.identity.aimesh.get = Mock(return_value=own)
    bridge.get_device_info = Mock(
        side_effect=lambda mesh_node: {
            "identifiers": {NODE_IDENTIFIER},
            "model": "Model",
            "name": "Name",
        }
    )

    return bridge


@pytest.mark.parametrize(
    ("own", "found", "expected"),
    [
        ("own", "found", "own"),
        (None, "found", "found"),
        (None, None, None),
    ],
)
async def test_get_device_info_mesh_node(
    registries: tuple[Mock, Mock],
    own: str | None,
    found: str | None,
    expected: str | None,
) -> None:
    """Test that the own AiMesh node wins over one of another entry."""

    bridge = _get_bridge(own, AROperationMode.ROUTER)

    with patch.object(ownership, "_find_mesh_node", Mock(return_value=found)):
        device_info = get_device_info(_get_hass(), _get_entry(), bridge)

    bridge.get_device_info.assert_called_once_with(expected)
    assert device_info["name"] == "Name"


@pytest.mark.parametrize(
    ("own", "mode", "devices", "keeps"),
    [
        # A node without its router keeps the name the router gave
        (None, AROperationMode.AIMESH_NODE, [_get_device(ENTRY_ID)], True),
        # A new device still needs a name
        (None, AROperationMode.AIMESH_NODE, [], False),
        (None, AROperationMode.AIMESH_NODE, [_get_device()], False),
        ("own", AROperationMode.AIMESH_NODE, [_get_device(ENTRY_ID)], False),
        (None, AROperationMode.ROUTER, [_get_device(ENTRY_ID)], False),
    ],
)
async def test_get_device_info_keeps_name(
    registries: tuple[Mock, Mock],
    own: str | None,
    mode: AROperationMode,
    devices: list[Mock],
    keeps: bool,
) -> None:
    """Test that only a node without any AiMesh data keeps its name."""

    dr, _ = registries
    dr.async_get.return_value.async_get_devices.return_value = devices
    bridge = _get_bridge(own, mode)

    with patch.object(ownership, "_find_mesh_node", Mock(return_value=None)):
        device_info = get_device_info(_get_hass(), _get_entry(), bridge)

    assert ("name" in device_info) is not keeps
    assert ("model" in device_info) is not keeps
    assert device_info["identifiers"] == {NODE_IDENTIFIER}


async def test_take_over(registries: tuple[Mock, Mock]) -> None:
    """Test that node entities move to the entry of the node itself."""

    dr, er = registries
    hass = _get_hass()
    device = _get_device(ENTRY_ID, device_id="own")
    node_device = _get_device(via_device_id="router", device_id="node")
    dr.async_get.return_value.async_get_devices.return_value = [
        device,
        node_device,
        # Not created through a router
        _get_device(device_id="direct"),
        _get_device(FOREIGN_ENTRY_ID, "router", "foreign"),
    ]
    er.async_entries_for_device.return_value = [
        Mock(entity_id="sensor.cpu"),
        Mock(entity_id="sensor.ram"),
    ]

    await async_take_over(hass, _get_entry(), device)

    er.async_entries_for_device.assert_called_once_with(
        er.async_get.return_value, "node", include_disabled_entities=True
    )
    assert er.async_get.return_value.async_update_entity.call_args_list == [
        call(entity_id, config_entry_id=ENTRY_ID, device_id="own")
        for entity_id in ("sensor.cpu", "sensor.ram")
    ]
    dr.async_get.return_value.async_remove_device.assert_called_once_with(
        "node"
    )
    hass.config_entries.async_reload.assert_awaited_once_with(OTHER_ENTRY_ID)


async def test_take_over_nothing(registries: tuple[Mock, Mock]) -> None:
    """Test that no entry is reloaded when nothing was taken over."""

    dr, _ = registries
    hass = _get_hass()
    device = _get_device(ENTRY_ID)
    dr.async_get.return_value.async_get_devices.return_value = [device]

    await async_take_over(hass, _get_entry(), device)

    hass.config_entries.async_reload.assert_not_awaited()


async def test_hand_back(registries: tuple[Mock, Mock]) -> None:
    """Test that the routers serving the removed node reload."""

    dr, _ = registries
    hass = _get_hass()
    entry = _get_entry()
    router = _get_entry(OTHER_ENTRY_ID, [OTHER_NODE_MAC, NODE_MAC])
    hass.config_entries.async_loaded_entries.return_value = [
        entry,
        router,
        # A router of another mesh
        _get_entry("other_router", [OTHER_NODE_MAC]),
    ]
    dr.async_entries_for_config_entry.return_value = [_get_device(ENTRY_ID)]

    async_hand_back(hass, entry)

    dr.async_entries_for_config_entry.assert_called_once_with(
        dr.async_get.return_value, ENTRY_ID
    )
    hass.config_entries.async_loaded_entries.assert_called_once_with(DOMAIN)
    hass.config_entries.async_schedule_reload.assert_called_once_with(
        OTHER_ENTRY_ID
    )
