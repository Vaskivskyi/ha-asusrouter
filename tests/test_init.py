"""Tests for the integration setup module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouterError
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady
import pytest

from custom_components.asusrouter import (
    async_migrate_entry,
    async_remove_config_entry_device,
    async_setup_entry,
    async_unload_entry,
    update_listener,
)
from custom_components.asusrouter.const import (
    ASUSROUTER,
    DOMAIN,
    STOP_LISTENER,
)

pytestmark = pytest.mark.asyncio

ENTRY_ID = "entry_id"
HOST = "192.168.1.1"

VERSION_CURRENT = 5
VERSION_LEGACY = 4


def _get_hass() -> Mock:
    """Create a Home Assistant instance with the used parts mocked."""

    hass = Mock(data={})
    hass.bus.async_listen_once = Mock(return_value=Mock())
    hass.config_entries.async_reload = AsyncMock()
    hass.config_entries.async_update_entry = Mock()

    return hass


def _get_entry(
    options: dict[str, Any] | None = None,
    version: int = VERSION_CURRENT,
) -> Mock:
    """Create a config entry with the used parts mocked."""

    return Mock(
        data={CONF_HOST: HOST},
        options=options if options is not None else {},
        entry_id=ENTRY_ID,
        version=version,
        async_on_unload=Mock(),
        add_update_listener=Mock(return_value=Mock()),
    )


async def test_setup_entry() -> None:
    """Test that the entry connects and is stored."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = Mock(async_connect=AsyncMock(), async_clean=AsyncMock())

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ) as bridge_class:
        assert await async_setup_entry(hass, entry) is True

    bridge_class.assert_called_once_with(hass, {CONF_HOST: HOST}, {})
    bridge.async_connect.assert_awaited_once()
    entry.async_on_unload.assert_called_once()
    assert hass.data[DOMAIN][ENTRY_ID][ASUSROUTER] is bridge
    assert hass.data[DOMAIN][ENTRY_ID][STOP_LISTENER] is not None


async def test_setup_entry_cannot_connect() -> None:
    """Test that a failed connection defers the setup."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = Mock(
        async_connect=AsyncMock(side_effect=AsusRouterError),
        async_clean=AsyncMock(),
    )

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        pytest.raises(ConfigEntryNotReady, match=HOST),
    ):
        await async_setup_entry(hass, entry)

    bridge.async_clean.assert_awaited_once()
    assert DOMAIN not in hass.data


async def test_setup_entry_closes_on_stop() -> None:
    """Test that the connection is closed when HA stops."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = Mock(async_connect=AsyncMock(), async_clean=AsyncMock())

    with patch(
        "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
    ):
        await async_setup_entry(hass, entry)

    close_connection = hass.bus.async_listen_once.call_args.args[1]
    await close_connection(Mock())

    bridge.async_clean.assert_awaited_once()


async def test_unload_entry() -> None:
    """Test that unloading closes the connection and drops the data."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = Mock(async_clean=AsyncMock())
    stop_listener = Mock()
    hass.data[DOMAIN] = {
        ENTRY_ID: {ASUSROUTER: bridge, STOP_LISTENER: stop_listener}
    }

    assert await async_unload_entry(hass, entry) is True

    stop_listener.assert_called_once()
    bridge.async_clean.assert_awaited_once()
    assert hass.data[DOMAIN] == {}


async def test_update_listener() -> None:
    """Test that changed options reload the entry."""

    hass = _get_hass()
    entry = _get_entry()

    await update_listener(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(ENTRY_ID)


async def test_migrate_entry() -> None:
    """Test the migration of the network interval option."""

    hass = _get_hass()
    entry = _get_entry(
        options={"interval_network_stat": 60}, version=VERSION_LEGACY
    )

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == VERSION_CURRENT
    hass.config_entries.async_update_entry.assert_called_once_with(
        entry, options={"interval_network": 60}
    )


async def test_migrate_entry_current_version() -> None:
    """Test that a current entry is not migrated."""

    hass = _get_hass()
    entry = _get_entry()

    assert await async_migrate_entry(hass, entry) is True

    hass.config_entries.async_update_entry.assert_not_called()


async def test_remove_config_entry_device() -> None:
    """Test that removing a device is allowed."""

    assert (
        await async_remove_config_entry_device(_get_hass(), Mock(), Mock())
        is True
    )
