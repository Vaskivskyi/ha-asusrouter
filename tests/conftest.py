"""Fixtures for tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.asusrouter import bridge as bridge_module
from tests.helpers import SyncPatch


class UniversalMockPatcher:
    """Universal mock patcher for async methods."""

    def __init__(self) -> None:
        """Initialize the UniversalMockPatcher."""

        self.patches: list[Any] = []

    def patch(
        self,
        obj: Any,
        method_name: str,
        side_effect: Any = None,
        return_value: Any = None,
        mock_type: type = AsyncMock,
    ) -> AsyncMock | Mock:
        """Patch a method on the provided object."""

        patcher = patch.object(obj, method_name, new_callable=mock_type)
        mock_method = patcher.start()
        self.patches.append(patcher)
        if side_effect is not None:
            mock_method.side_effect = side_effect
        elif return_value is not None:
            mock_method.return_value = return_value
        return mock_method

    def stop(self) -> None:
        """Stop all patches."""

        for patcher in self.patches:
            patcher.stop()


@pytest.fixture
def universal_mock() -> Generator[UniversalMockPatcher]:
    """Fixture for a universal mock patcher."""

    patcher = UniversalMockPatcher()
    yield patcher
    patcher.stop()


@pytest.fixture(name="create_clientsession")
def mock_create_clientsession(
    universal_mock: UniversalMockPatcher,
) -> SyncPatch:
    """Mock the async_create_clientsession function."""

    def _patch(
        obj: Any, side_effect: Any = None, return_value: Any = None
    ) -> Mock:
        return universal_mock.patch(
            obj, "async_create_clientsession", side_effect, return_value, Mock
        )

    return _patch


@pytest.fixture(name="get_cookie_jar")
def mock_get_cookie_jar(universal_mock: UniversalMockPatcher) -> SyncPatch:
    """Mock the get_cookie_jar function."""

    def _patch(side_effect: Any = None, return_value: Any = None) -> Mock:
        return universal_mock.patch(
            bridge_module, "get_cookie_jar", side_effect, return_value, Mock
        )

    return _patch


@pytest.fixture(name="format_mac")
def mock_format_mac(universal_mock: UniversalMockPatcher) -> SyncPatch:
    """Mock the format_mac function."""

    def mock_format_mac(mac_addr: str) -> str:
        """Mock format_mac."""

        return mac_addr

    def _patch(
        side_effect: Any = mock_format_mac, return_value: Any = None
    ) -> Mock:
        return universal_mock.patch(
            bridge_module, "format_mac", side_effect, return_value, Mock
        )

    return _patch
