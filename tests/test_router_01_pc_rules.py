"""Tests for the router module / Part 01 / Parental control rules."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter.modules.parental_control import ParentalControlRule, PCRuleType
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL
import pytest

from custom_components.asusrouter import router as router_module
from custom_components.asusrouter.const import CONF_CREATE_BLOCK_SWITCHES
from custom_components.asusrouter.router import ARDevice

FAKE_HOST = "hostname"
FAKE_CLIENT_MAC = "AA:BB:CC:DD:EE:FF"
FAKE_CLIENT_MAC_HA = "aa:bb:cc:dd:ee:ff"


def mock_config_entry(options: dict[str, Any] | None = None) -> Mock:
    """Mock a config entry."""

    config_entry = Mock()
    config_entry.data = {CONF_HOST: FAKE_HOST}
    config_entry.options = {
        CONF_PORT: 8443,
        CONF_SSL: True,
        **(options or {}),
    }
    return config_entry


def make_device(options: dict[str, Any] | None = None) -> ARDevice:
    """Make an ARDevice with a mocked bridge."""

    with patch.object(router_module, "ARBridge"):
        return ARDevice(Mock(), mock_config_entry(options))


def mock_rule(mac: str = FAKE_CLIENT_MAC) -> ParentalControlRule:
    """Mock a parental control rule."""

    return ParentalControlRule(mac=mac, name="client", type=PCRuleType.BLOCK)


@pytest.mark.asyncio
async def test_pc_rules_mac_is_normalized() -> None:
    """Test that rule MAC addresses are normalized.

    The library reports MAC addresses in the device format, while clients
    are stored using the HA `format_mac`. Without normalization the same
    device ends up tracked under two different keys, which results in
    duplicate entities.
    """

    device = make_device()
    rule = mock_rule()

    with (
        patch.object(
            device.bridge,
            "_get_data_parental_control",
            AsyncMock(return_value={"rules": {FAKE_CLIENT_MAC: rule}}),
        ),
        patch.object(router_module, "async_dispatcher_send"),
    ):
        await device.update_pc_rules()

    assert FAKE_CLIENT_MAC_HA in device.pc_rules
    assert FAKE_CLIENT_MAC not in device.pc_rules


@pytest.mark.asyncio
async def test_pc_rules_removed_rule_is_dropped() -> None:
    """Test that a rule removed on the device is dropped."""

    device = make_device()

    with (
        patch.object(
            device.bridge,
            "_get_data_parental_control",
            AsyncMock(return_value={"rules": {FAKE_CLIENT_MAC: mock_rule()}}),
        ),
        patch.object(router_module, "async_dispatcher_send"),
    ):
        await device.update_pc_rules()

    assert device.pc_rules != {}

    with (
        patch.object(
            device.bridge,
            "_get_data_parental_control",
            AsyncMock(return_value={"rules": {}}),
        ),
        patch.object(router_module, "async_dispatcher_send"),
    ):
        await device.update_pc_rules()

    assert device.pc_rules == {}


@pytest.mark.asyncio
async def test_pc_rules_empty_mac_is_skipped() -> None:
    """Test that a rule with an empty MAC is not saved."""

    device = make_device()

    with (
        patch.object(
            device.bridge,
            "_get_data_parental_control",
            AsyncMock(return_value={"rules": {"": mock_rule(mac="")}}),
        ),
        patch.object(router_module, "async_dispatcher_send"),
    ):
        await device.update_pc_rules()

    assert device.pc_rules == {}


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, False),
        ({CONF_CREATE_BLOCK_SWITCHES: False}, False),
        ({CONF_CREATE_BLOCK_SWITCHES: True}, True),
    ],
    ids=["default", "disabled", "enabled"],
)
def test_create_block_switches_option(
    options: dict[str, Any], expected: bool
) -> None:
    """Test that the option is read from the config entry."""

    device = make_device(options)

    assert device.create_block_switches is expected
