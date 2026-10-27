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
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
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


def _get_entry(fetch: Any = None, side_effect: Any = None) -> Mock:
    """Create a config entry with a bridge mocked."""

    bridge = Mock()
    bridge.api.async_fetch_data = AsyncMock(
        return_value=fetch, side_effect=side_effect
    )

    entry = Mock()
    entry.runtime_data = ARRuntimeData(bridge=bridge)

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


@pytest.mark.parametrize(
    ("content", "previous", "expected"),
    [
        (_get_topology(NODE_MAC), None, _get_topology(NODE_MAC)),
        # A failed read keeps the last known topology
        (_get_topology(), _get_topology(NODE_MAC), _get_topology(NODE_MAC)),
        (None, _get_topology(NODE_MAC), _get_topology(NODE_MAC)),
        (None, None, _get_topology()),
    ],
)
async def test_topology_content(
    content: Any,
    previous: ARAiMeshTopology | None,
    expected: ARAiMeshTopology,
) -> None:
    """Test that the topology never empties after a failed read."""

    coordinator = ARTopologyCoordinator(
        Mock(), _get_entry(), ARAiMeshSourceUniversal, INTERVAL
    )
    # A new coordinator has no data yet
    if previous is not None:
        coordinator.data = previous

    assert coordinator._get_content(content) == expected


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

    with patch.object(
        ARCoordinator, "async_config_entry_first_refresh", AsyncMock()
    ) as first_refresh:
        coordinators = await async_setup_coordinators(
            Mock(), _get_entry(), descriptions
        )

    assert list(coordinators) == [SOURCE, OTHER_SOURCE]
    assert coordinators[SOURCE].update_interval == SHORT_INTERVAL
    assert coordinators[OTHER_SOURCE].update_interval == INTERVAL
    assert first_refresh.await_count == len(coordinators)


async def test_setup_coordinators_nodes() -> None:
    """Test that node coordinators refresh without failing the setup."""

    descriptions = [
        Mock(
            source=SOURCE,
            update_interval=INTERVAL,
            node_source=ARSystemStatusSource,
        ),
        # Available on the router only
        Mock(source=OTHER_SOURCE, update_interval=INTERVAL, node_source=None),
    ]

    with (
        patch.object(
            ARCoordinator, "async_config_entry_first_refresh", AsyncMock()
        ) as first_refresh,
        # Unlike the first refresh, a plain refresh never raises
        patch.object(ARCoordinator, "async_refresh", AsyncMock()) as refresh,
    ):
        coordinators = await async_setup_coordinators(
            Mock(), _get_entry(), descriptions, [NODE_MAC]
        )

    assert list(coordinators) == [
        SOURCE,
        OTHER_SOURCE,
        ARSystemStatusSource(target=NODE_MAC),
    ]
    assert first_refresh.await_count == len(descriptions)
    refresh.assert_awaited_once()


async def test_setup_coordinators_background() -> None:
    """Test that a source of no entity is polled without failing the setup."""

    with (
        patch.object(
            ARCoordinator, "async_config_entry_first_refresh", AsyncMock()
        ) as first_refresh,
        patch.object(ARCoordinator, "async_refresh", AsyncMock()) as refresh,
    ):
        coordinators = await async_setup_coordinators(
            Mock(),
            _get_entry(),
            [Mock(source=SOURCE, update_interval=INTERVAL)],
            background=[(ARAiMeshSourceUniversal, SHORT_INTERVAL)],
        )

    assert isinstance(coordinators[SOURCE], ARStateCoordinator)
    topology = coordinators[ARAiMeshSourceUniversal]
    assert isinstance(topology, ARTopologyCoordinator)
    assert topology.update_interval == SHORT_INTERVAL
    first_refresh.assert_awaited_once()
    refresh.assert_awaited_once()


@pytest.mark.parametrize(
    ("side_effect", "expected"),
    [
        ([ConfigEntryNotReady, None], ConfigEntryNotReady),
        # New credentials win over any other failure
        ([ConfigEntryNotReady, ConfigEntryAuthFailed], ConfigEntryAuthFailed),
    ],
)
async def test_setup_coordinators_failed(
    side_effect: list[Any], expected: type[Exception]
) -> None:
    """Test that a failed first refresh fails the setup."""

    descriptions = [
        Mock(source=SOURCE, update_interval=INTERVAL),
        Mock(source=OTHER_SOURCE, update_interval=INTERVAL),
    ]

    with (
        patch.object(
            ARCoordinator,
            "async_config_entry_first_refresh",
            AsyncMock(side_effect=side_effect),
        ) as first_refresh,
        pytest.raises(expected),
    ):
        await async_setup_coordinators(Mock(), _get_entry(), descriptions)

    # Every refresh runs to the end, none is left behind
    assert first_refresh.await_count == len(descriptions)


# ---------------------------
# <-- SETUP COORDINATORS
# ---------------------------
