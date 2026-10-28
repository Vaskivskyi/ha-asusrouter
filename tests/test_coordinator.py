"""Tests for the coordinator module."""

from __future__ import annotations

from datetime import timedelta
import re
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouterError
from asusrouter.error import AsusRouterAccessError
from asusrouter.modules.aimesh import (
    ARAiMeshNode,
    ARAiMeshSourceUniversal,
    ARAiMeshTopology,
)
from asusrouter.modules.endpoint.error import ARAccessError
from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
)
from asusrouter.tools.identifiers import MacAddress
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.asusrouter import ARRuntimeData
from custom_components.asusrouter.coordinator import (
    ARCoordinator,
    ARStateCoordinator,
    ARTopologyCoordinator,
    async_setup_coordinators,
)

pytestmark = pytest.mark.asyncio

INTERVAL = timedelta(seconds=30)
SHORT_INTERVAL = timedelta(seconds=10)
SOURCE = ARSystemStatusSourceUniversal
OTHER_SOURCE = ARSystemStatusSource(target="aa:bb:cc:dd:ee:02")
NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:03")
OTHER_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:04")
DEVICE_DATA = {"key": "value"}


def _get_entry(
    fetch: Any = None,
    side_effect: Any = None,
    mesh: frozenset[MacAddress] = frozenset(),
    nodes: list[MacAddress] | None = None,
) -> Mock:
    """Create a config entry with a bridge mocked."""

    bridge = Mock()
    bridge.api.async_fetch_data = AsyncMock(
        return_value=fetch, side_effect=side_effect
    )

    entry = Mock()
    entry.runtime_data = ARRuntimeData(
        bridge=bridge, mesh=mesh, nodes=nodes or []
    )

    return entry


def _get_coordinator(entry: Mock) -> ARStateCoordinator:
    """Create a coordinator of the test source."""

    return ARStateCoordinator(Mock(), entry, SOURCE, INTERVAL)


def _get_topology(*macs: MacAddress) -> ARAiMeshTopology:
    """Create a topology of the given nodes."""

    return ARAiMeshTopology(nodes={mac: ARAiMeshNode(mac=mac) for mac in macs})


# ---------------------------
# UPDATE -->
# ---------------------------


async def test_coordinator_init() -> None:
    """Test that the coordinator is named after and polls its source."""

    coordinator = _get_coordinator(_get_entry())

    assert coordinator.name == f"asusrouter {SOURCE}"
    assert coordinator.update_interval == INTERVAL
    assert coordinator.always_update is False


@pytest.mark.parametrize(
    ("fetch", "expected"),
    [
        ({SOURCE: {"key": "value"}}, {"key": "value"}),
        # No fresh data
        (None, {}),
        ({OTHER_SOURCE: {"key": "value"}}, {}),
        ({SOURCE: None}, {}),
    ],
)
async def test_update_data(fetch: Any, expected: dict[Any, Any]) -> None:
    """Test that the coordinator keeps the content of its source only."""

    entry = _get_entry(fetch=fetch)
    coordinator = _get_coordinator(entry)

    assert await coordinator._async_update_data() == expected

    entry.runtime_data.bridge.api.async_fetch_data.assert_awaited_once_with(
        SOURCE
    )


async def test_update_data_failed() -> None:
    """Test that a failed fetch is reported as a failed update."""

    coordinator = _get_coordinator(_get_entry(side_effect=AsusRouterError()))

    with pytest.raises(UpdateFailed, match=re.escape(str(SOURCE))):
        await coordinator._async_update_data()


async def test_update_data_wrong_credentials() -> None:
    """Test that refused credentials ask the user instead of retrying."""

    coordinator = _get_coordinator(
        _get_entry(
            side_effect=AsusRouterAccessError(
                "Access error", ARAccessError.CREDENTIALS, {}
            )
        )
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


def _get_topology_coordinator() -> ARTopologyCoordinator:
    """Create a coordinator of the AiMesh topology."""

    return ARTopologyCoordinator(
        Mock(), _get_entry(), ARAiMeshSourceUniversal, INTERVAL
    )


async def test_topology_content() -> None:
    """Test that a fetched topology becomes the data."""

    topology = _get_topology(NODE_MAC)

    assert _get_topology_coordinator()._get_content(topology) is topology


@pytest.mark.parametrize("content", [_get_topology(), None, {}])
async def test_topology_content_failed(content: Any) -> None:
    """Test that a read with no topology fails the update."""

    with pytest.raises(UpdateFailed):
        _get_topology_coordinator()._get_content(content)


async def test_state_get_device() -> None:
    """Test that the state of a device is read by its MAC."""

    coordinator = _get_coordinator(_get_entry())
    coordinator.data = {NODE_MAC: DEVICE_DATA}

    assert coordinator.get_device(NODE_MAC) is DEVICE_DATA
    assert coordinator.get_device(OTHER_MAC) is None


async def test_topology_get_device() -> None:
    """Test that the AiMesh node of a device is read by its MAC."""

    coordinator = _get_topology_coordinator()
    coordinator.data = _get_topology(NODE_MAC)

    assert coordinator.get_device(NODE_MAC) is coordinator.data.nodes[NODE_MAC]
    assert coordinator.get_device(OTHER_MAC) is None


# ---------------------------
# <-- UPDATE
# ---------------------------

# ---------------------------
# SETUP COORDINATORS -->
# ---------------------------


async def test_setup_coordinators() -> None:
    """Test that every source gets one coordinator at its shortest interval."""

    descriptions = [
        Mock(source=SOURCE, update_interval=INTERVAL),
        Mock(source=SOURCE, update_interval=SHORT_INTERVAL),
        Mock(source=OTHER_SOURCE, update_interval=INTERVAL),
    ]

    with patch.object(ARCoordinator, "async_refresh", AsyncMock()) as refresh:
        coordinators = await async_setup_coordinators(
            Mock(), _get_entry(), descriptions
        )

    assert list(coordinators) == [SOURCE, OTHER_SOURCE]
    assert coordinators[SOURCE].update_interval == SHORT_INTERVAL
    assert coordinators[OTHER_SOURCE].update_interval == INTERVAL
    assert refresh.await_count == len(coordinators)


async def test_setup_coordinators_nodes() -> None:
    """Test that the nodes served through the entry get coordinators."""

    descriptions = [
        Mock(
            source=SOURCE,
            update_interval=INTERVAL,
            node_source=ARSystemStatusSource,
            covers_mesh=False,
        ),
        # Available on the router only
        Mock(source=OTHER_SOURCE, update_interval=INTERVAL, node_source=None),
    ]

    with patch.object(ARCoordinator, "async_refresh", AsyncMock()) as refresh:
        coordinators = await async_setup_coordinators(
            Mock(),
            _get_entry(
                mesh=frozenset({NODE_MAC, OTHER_MAC}), nodes=[NODE_MAC]
            ),
            descriptions,
        )

    # The node another entry serves gets no coordinator here
    assert list(coordinators) == [
        SOURCE,
        OTHER_SOURCE,
        ARSystemStatusSource(target=NODE_MAC),
    ]
    assert refresh.await_count == len(coordinators)


async def test_setup_coordinators_mesh() -> None:
    """Test that a source of the whole mesh serves every node."""

    description = Mock(
        source=SOURCE,
        update_interval=INTERVAL,
        node_source=ARSystemStatusSource,
        covers_mesh=True,
    )

    with patch.object(ARCoordinator, "async_refresh", AsyncMock()):
        coordinators = await async_setup_coordinators(
            Mock(),
            _get_entry(mesh=frozenset({NODE_MAC}), nodes=[]),
            [description],
        )

    assert ARSystemStatusSource(target=NODE_MAC) in coordinators


async def test_setup_coordinators_topology() -> None:
    """Test that the AiMesh topology gets its own coordinator type."""

    descriptions = [
        Mock(source=SOURCE, update_interval=INTERVAL),
        Mock(source=ARAiMeshSourceUniversal, update_interval=INTERVAL),
    ]

    with patch.object(ARCoordinator, "async_refresh", AsyncMock()):
        coordinators = await async_setup_coordinators(
            Mock(), _get_entry(), descriptions
        )

    assert isinstance(coordinators[SOURCE], ARStateCoordinator)
    assert isinstance(
        coordinators[ARAiMeshSourceUniversal], ARTopologyCoordinator
    )


@pytest.mark.parametrize(
    ("exception", "raised"),
    [
        # Only the entities of the failed source are left unavailable
        (UpdateFailed(), False),
        (ConfigEntryAuthFailed(), True),
    ],
)
async def test_setup_coordinators_failed(
    exception: Exception, raised: bool
) -> None:
    """Test that only refused credentials fail the setup."""

    descriptions = [
        Mock(source=SOURCE, update_interval=INTERVAL),
        Mock(source=OTHER_SOURCE, update_interval=INTERVAL),
    ]
    refreshed: list[ARCoordinator[Any]] = []

    async def _refresh(coordinator: ARCoordinator[Any]) -> None:
        """Fail the refresh of the other source only."""

        refreshed.append(coordinator)
        coordinator.last_exception = (
            exception if coordinator.name.endswith(str(OTHER_SOURCE)) else None
        )

    with patch.object(ARCoordinator, "async_refresh", _refresh):
        if raised:
            with pytest.raises(type(exception)):
                await async_setup_coordinators(
                    Mock(), _get_entry(), descriptions
                )
        else:
            await async_setup_coordinators(Mock(), _get_entry(), descriptions)

    # Every refresh runs to the end, none is left behind
    assert len(refreshed) == len(descriptions)


# ---------------------------
# <-- SETUP COORDINATORS
# ---------------------------
