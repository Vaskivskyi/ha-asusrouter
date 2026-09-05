"""Tests for the integration setup module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouterError
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.exceptions import ConfigEntryNotReady
import pytest

from custom_components.asusrouter import (
    ARRuntimeData,
    async_setup_entry,
    async_unload_entry,
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

DEVICE_INFO = {"identifiers": {("asusrouter", HOST)}, "name": "Model"}


def _get_hass() -> Mock:
    """Create a Home Assistant instance with the used parts mocked."""

    hass = Mock()
    hass.bus.async_listen_once = Mock(return_value=Mock())

    return hass


def _get_entry() -> Mock:
    """Create a config entry with the used parts mocked."""

    return Mock(
        data=ENTRY_DATA,
        entry_id=ENTRY_ID,
        async_on_unload=Mock(),
    )


def _get_bridge(connect: Any = None) -> Mock:
    """Create a bridge with the used parts mocked."""

    return Mock(
        async_connect=AsyncMock(side_effect=connect),
        async_close=AsyncMock(),
        device_info=DEVICE_INFO,
    )


# ---------------------------
# SETUP -->
# ---------------------------


async def test_setup_entry() -> None:
    """Test that the entry connects and stores its runtime data."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge()

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ) as bridge_class,
        patch("custom_components.asusrouter.dr.async_get"),
    ):
        assert await async_setup_entry(hass, entry) is True

    bridge_class.assert_called_once_with(hass, ENTRY_DATA)
    bridge.async_connect.assert_awaited_once()
    assert entry.runtime_data == ARRuntimeData(bridge=bridge)


async def test_setup_entry_registers_device() -> None:
    """Test that the device is registered from the bridge identity."""

    hass = _get_hass()
    entry = _get_entry()

    with (
        patch(
            "custom_components.asusrouter.ARBridge",
            Mock(return_value=_get_bridge()),
        ),
        patch("custom_components.asusrouter.dr.async_get") as registry,
    ):
        await async_setup_entry(hass, entry)

    registry.return_value.async_get_or_create.assert_called_once_with(
        config_entry_id=ENTRY_ID, **DEVICE_INFO
    )


async def test_setup_entry_registers_stop_listener() -> None:
    """Test that the stop listener is removed together with the entry."""

    hass = _get_hass()
    entry = _get_entry()

    with (
        patch(
            "custom_components.asusrouter.ARBridge",
            Mock(return_value=_get_bridge()),
        ),
        patch("custom_components.asusrouter.dr.async_get"),
    ):
        await async_setup_entry(hass, entry)

    entry.async_on_unload.assert_called_once_with(
        hass.bus.async_listen_once.return_value
    )


async def test_setup_entry_cannot_connect() -> None:
    """Test that a failed connection defers the setup."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge(connect=AsusRouterError)

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        pytest.raises(ConfigEntryNotReady, match=HOST),
    ):
        await async_setup_entry(hass, entry)

    bridge.async_close.assert_awaited_once()


async def test_setup_entry_closes_on_stop() -> None:
    """Test that the connection is closed when HA stops."""

    hass = _get_hass()
    entry = _get_entry()
    bridge = _get_bridge()

    with (
        patch(
            "custom_components.asusrouter.ARBridge", Mock(return_value=bridge)
        ),
        patch("custom_components.asusrouter.dr.async_get"),
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

    assert await async_unload_entry(_get_hass(), entry) is True

    bridge.async_close.assert_awaited_once()


# ---------------------------
# <-- LIFECYCLE
# ---------------------------
