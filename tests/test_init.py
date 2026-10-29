"""Tests for the integration setup module."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouterError
from asusrouter.error import AsusRouterAccessError
from asusrouter.modules.aimesh import ARAiMeshSourceUniversal
from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.endpoint.error import ARAccessError
from asusrouter.modules.source import ARDataSource
from asusrouter.modules.system_status import ARSystemStatusSourceUniversal
from asusrouter.modules.wifi import ARWiFiBand
from asusrouter.tools.identifiers import MacAddress
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
import pytest

from custom_components.asusrouter import (
    PLATFORMS,
    ARRuntimeData,
    async_remove_config_entry_device,
    async_remove_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.asusrouter.coordinator import ARTopologyCoordinator
from custom_components.asusrouter.modules import (
    DESCRIPTIONS,
    aimesh,
    ddns,
    network,
)

pytestmark = pytest.mark.asyncio

ENTRY_ID = "entry_id"
HOST = "192.168.1.1"

ENTRY_DATA: dict[str, Any] = {
    CONF_HOST: HOST,
    CONF_USERNAME: "user",
    CONF_PASSWORD: "password",
    CONF_PORT: 8443,
    CONF_SSL: True,
}

COORDINATORS: dict[ARDataSource, Any] = {ARSystemStatusSourceUniversal: Mock()}
# Every band, so every radio is supported
BANDS = [band for band in ARWiFiBand if band is not ARWiFiBand.UNKNOWN]

NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
OWNED_NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")


@pytest.fixture(autouse=True)
def setup_coordinators() -> Iterator[AsyncMock]:
    """Mock the coordinators setup."""

    with patch(
        "custom_components.asusrouter.async_setup_coordinators",
        AsyncMock(return_value=COORDINATORS),
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def owned_devices() -> Iterator[Mock]:
    """Mock the lookup of nodes owned by other entries."""

    with patch(
        "custom_components.asusrouter.get_owned_devices",
        Mock(return_value={}),
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def register_devices() -> Iterator[Mock]:
    """Mock the registration of the device and its nodes."""

    with patch(
        "custom_components.asusrouter.async_register_devices", Mock()
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def remove_stale_devices() -> Iterator[Mock]:
    """Mock the removal of the devices of the nodes that left."""

    with patch(
        "custom_components.asusrouter.async_remove_stale_devices", Mock()
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def take_over() -> Iterator[AsyncMock]:
    """Mock the take over of entities of other entries."""

    with patch(
        "custom_components.asusrouter.async_take_over", AsyncMock()
    ) as mock:
        yield mock


def _get_hass(unload: bool = True) -> Mock:
    """Create a Home Assistant instance with the used parts mocked."""

    hass = Mock()
    hass.bus.async_listen_once = Mock(return_value=Mock())
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=unload)

    return hass


def _get_entry() -> Mock:
    """Create a config entry with the used parts mocked."""

    return Mock(
        data=ENTRY_DATA,
        entry_id=ENTRY_ID,
        async_on_unload=Mock(),
    )


def _get_bridge(
    connect: Any = None, nodes: Any = (), serves_mesh: bool = True
) -> Mock:
    """Create a bridge with the used parts mocked."""

    bridge = Mock(
        async_connect=AsyncMock(side_effect=connect),
        async_close=AsyncMock(),
        get_nodes=Mock(return_value=[Mock(mac=mac) for mac in nodes]),
        serves_mesh=serves_mesh,
    )
    # A device not serving the mesh is a node, which is not a router
    bridge.identity.operation_mode = (
        AROperationMode.ROUTER if serves_mesh else AROperationMode.AIMESH_NODE
    )
    # The device lists itself among the nodes
    bridge.identity.aimesh.nodes = {"device": Mock()}
    bridge.identity.wifi = {band: unit for unit, band in enumerate(BANDS)}

    return bridge


# ---------------------------
# SETUP -->
# ---------------------------


async def test_setup_entry(setup_coordinators: AsyncMock) -> None:
    """Test that the entry connects and stores its runtime data."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge()

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ) as bridge_class:
        assert await async_setup_entry(hass, entry) is True

    bridge_class.assert_called_once_with(hass, ENTRY_DATA)
    bridge.async_connect.assert_awaited_once()
    setup_coordinators.assert_awaited_once_with(
        hass, entry, list(DESCRIPTIONS)
    )
    assert entry.runtime_data == ARRuntimeData(
        bridge=bridge, coordinators=COORDINATORS
    )
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry, PLATFORMS
    )


async def test_setup_entry_aimesh_node(setup_coordinators: AsyncMock) -> None:
    """Test that a node never follows the topology."""

    hass = _get_hass()
    entry = _get_entry()

    with patch(
        "custom_components.asusrouter.ARBridge",
        Mock(return_value=_get_bridge(serves_mesh=False)),
    ):
        await async_setup_entry(hass, entry)

    # Nothing of the AiMesh is set up, nor of a router or its networks
    excluded = [
        *aimesh.BINARY_SENSORS,
        *aimesh.SENSORS,
        *ddns.BINARY_SENSORS,
        *network.BINARY_SENSORS,
        *network.SWITCHES,
    ]
    setup_coordinators.assert_awaited_once_with(
        hass,
        entry,
        [d for d in DESCRIPTIONS if d not in excluded],
    )


async def test_setup_entry_nodes(
    setup_coordinators: AsyncMock,
    owned_devices: Mock,
    register_devices: Mock,
    remove_stale_devices: Mock,
    take_over: AsyncMock,
) -> None:
    """Test that nodes owned by no other entry are served as devices."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge(nodes=[NODE_MAC, OWNED_NODE_MAC])
    owned_devices.return_value = {OWNED_NODE_MAC: Mock(id="owned")}

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ):
        await async_setup_entry(hass, entry)

    nodes = bridge.get_nodes.return_value
    bridge.get_nodes.assert_called_once_with(bridge.identity.aimesh)
    assert list(owned_devices.call_args.args[2]) == [NODE_MAC, OWNED_NODE_MAC]
    assert entry.runtime_data.mesh == {NODE_MAC, OWNED_NODE_MAC}
    assert entry.runtime_data.nodes == [NODE_MAC]
    setup_coordinators.assert_awaited_once_with(
        hass, entry, list(DESCRIPTIONS)
    )

    device = register_devices.return_value
    register_devices.assert_called_once_with(
        hass, entry, nodes, owned_devices.return_value
    )
    remove_stale_devices.assert_called_once_with(hass, entry, device, nodes)
    take_over.assert_awaited_once_with(hass, entry, device)


async def test_setup_entry_empty_topology(remove_stale_devices: Mock) -> None:
    """Test that a failed topology read never removes node devices."""

    bridge = _get_bridge()
    bridge.identity.aimesh.nodes = {}

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ):
        await async_setup_entry(_get_hass(), _get_entry())

    remove_stale_devices.assert_not_called()


async def test_setup_entry_follows_topology(
    setup_coordinators: AsyncMock,
) -> None:
    """Test that topology updates are followed until the entry unloads."""

    hass = _get_hass()
    entry = _get_entry()
    coordinator = Mock(spec=ARTopologyCoordinator)
    setup_coordinators.return_value = {ARAiMeshSourceUniversal: coordinator}

    with (
        patch(
            "custom_components.asusrouter.ARBridge",
            Mock(return_value=_get_bridge()),
        ),
        patch(
            "custom_components.asusrouter.async_sync_topology"
        ) as sync_topology,
    ):
        await async_setup_entry(hass, entry)

        listener = coordinator.async_add_listener.call_args.args[0]
        listener()

    sync_topology.assert_called_once_with(hass, entry, coordinator)
    entry.async_on_unload.assert_any_call(
        coordinator.async_add_listener.return_value
    )


async def test_setup_entry_registers_stop_listener() -> None:
    """Test that the stop listener is removed together with the entry."""

    hass = _get_hass()
    entry = _get_entry()

    with patch(
        "custom_components.asusrouter.ARBridge",
        Mock(return_value=_get_bridge()),
    ):
        await async_setup_entry(hass, entry)

    entry.async_on_unload.assert_called_once_with(
        hass.bus.async_listen_once.return_value
    )


@pytest.mark.parametrize(
    "exception",
    [
        AsusRouterError(),
        # The device lifts this lock on its own, so reconnecting is right
        AsusRouterAccessError("Access error", ARAccessError.TRY_AGAIN, {}),
    ],
)
async def test_setup_entry_cannot_connect(exception: Exception) -> None:
    """Test that a failed connection defers the setup."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge(connect=exception)

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        pytest.raises(ConfigEntryNotReady, match=HOST),
    ):
        await async_setup_entry(hass, entry)

    bridge.async_close.assert_awaited_once()


async def test_setup_entry_wrong_credentials() -> None:
    """Test that refused credentials ask the user instead of retrying."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge(
        connect=AsusRouterAccessError(
            "Access error", ARAccessError.CREDENTIALS, {}
        )
    )

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        pytest.raises(ConfigEntryAuthFailed, match=HOST),
    ):
        await async_setup_entry(hass, entry)

    bridge.async_close.assert_awaited_once()


@pytest.mark.parametrize(
    "exception", [ConfigEntryNotReady, ConfigEntryAuthFailed]
)
async def test_setup_entry_first_refresh_failed(
    setup_coordinators: AsyncMock, exception: type[Exception]
) -> None:
    """Test that a failed first refresh closes the connection."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge()
    setup_coordinators.side_effect = exception

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        pytest.raises(exception),
    ):
        await async_setup_entry(hass, entry)

    bridge.async_close.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_not_awaited()


async def test_setup_entry_closes_on_stop() -> None:
    """Test that the connection is closed when HA stops."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge()

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ):
        await async_setup_entry(hass, entry)

    close_connection = hass.bus.async_listen_once.call_args.args[1]
    await close_connection(Mock())

    bridge.async_close.assert_awaited_once()


# ---------------------------
# <-- SETUP
# ---------------------------

# ---------------------------
# LIFECYCLE -->
# ---------------------------


async def test_unload_entry() -> None:
    """Test that unloading closes the connection."""

    bridge = _get_bridge()
    entry = _get_entry()
    entry.runtime_data = ARRuntimeData(bridge=bridge)

    hass = _get_hass()

    assert await async_unload_entry(hass, entry) is True

    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry, PLATFORMS
    )
    bridge.async_close.assert_awaited_once()


async def test_unload_entry_platforms_failed() -> None:
    """Test that the connection stays open while platforms are loaded."""

    bridge = _get_bridge()
    entry = _get_entry()
    entry.runtime_data = ARRuntimeData(bridge=bridge)

    assert await async_unload_entry(_get_hass(unload=False), entry) is False

    bridge.async_close.assert_not_awaited()


async def test_remove_config_entry_device() -> None:
    """Test that only a node that left the AiMesh can be removed."""

    entry = _get_entry()
    device = Mock()

    with patch(
        "custom_components.asusrouter.can_remove_device",
        Mock(return_value=True),
    ) as can_remove:
        assert await async_remove_config_entry_device(
            _get_hass(), entry, device
        )

    can_remove.assert_called_once_with(entry, device)


async def test_remove_entry() -> None:
    """Test that a removed entry hands its device back to the routers."""

    hass = _get_hass()
    entry = _get_entry()

    with patch("custom_components.asusrouter.async_hand_back") as hand_back:
        await async_remove_entry(hass, entry)

    hand_back.assert_called_once_with(hass, entry)


# ---------------------------
# <-- LIFECYCLE
# ---------------------------


@pytest.mark.parametrize(
    ("covers_mesh", "expected"),
    [(True, {NODE_MAC, OWNED_NODE_MAC}), (False, {NODE_MAC})],
)
async def test_get_node_macs(
    covers_mesh: bool, expected: set[MacAddress]
) -> None:
    """Test that only a source of the whole mesh serves every node."""

    runtime_data = ARRuntimeData(
        bridge=Mock(),
        mesh=frozenset({NODE_MAC, OWNED_NODE_MAC}),
        nodes=[NODE_MAC],
    )
    description = Mock(covers_mesh=covers_mesh)

    assert set(runtime_data.get_node_macs(description)) == expected
