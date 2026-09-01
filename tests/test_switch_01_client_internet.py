"""Tests for the switch module / Part 01 / Client internet switches."""

from typing import Any
from unittest.mock import Mock, patch

from asusrouter.modules.parental_control import ParentalControlRule, PCRuleType
import pytest

from custom_components.asusrouter.switch import (
    ClientInternetSwitch,
    add_entities,
)

FAKE_ROUTER_MAC = "00:11:22:33:44:55"
FAKE_CLIENT_MAC = "aa:bb:cc:dd:ee:ff"
FAKE_CLIENT_NAME = "client"
FAKE_RULE_NAME = "rule"

EXPECTED_TWO_SWITCHES = 2


def mock_router(
    pc_rules: dict[str, ParentalControlRule] | None = None,
    devices: dict[str, Any] | None = None,
    create_block_switches: bool = False,
) -> Mock:
    """Mock a router."""

    router = Mock()
    router.mac = FAKE_ROUTER_MAC
    router.pc_rules = pc_rules if pc_rules is not None else {}
    router.devices = devices if devices is not None else {}
    router.create_block_switches = create_block_switches
    router.create_devices = False
    return router


def mock_client(name: str | None = FAKE_CLIENT_NAME) -> Mock:
    """Mock a connected client."""

    client = Mock()
    client.name = name
    return client


def mock_rule(
    mac: str = FAKE_CLIENT_MAC.upper(),
    name: str = FAKE_RULE_NAME,
    rule_type: PCRuleType = PCRuleType.BLOCK,
) -> ParentalControlRule:
    """Mock a parental control rule."""

    return ParentalControlRule(mac=mac, name=name, type=rule_type)


@pytest.mark.parametrize(
    ("rule_type", "expected"),
    [
        (PCRuleType.BLOCK, True),
        (PCRuleType.DISABLE, False),
    ],
    ids=["block", "disable"],
)
def test_is_on_with_rule(rule_type: PCRuleType, expected: bool) -> None:
    """Test the state of a switch backed by a rule."""

    rule = mock_rule(rule_type=rule_type)
    switch = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_RULE_NAME, rule
    )

    assert switch.is_on is expected


def test_is_on_without_rule() -> None:
    """Test that a switch without a rule reports the off state.

    A client which has never been blocked has no rule on the device. This
    must read as `off` and not as an unknown state.
    """

    switch = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_CLIENT_NAME
    )

    assert switch.is_on is False


def test_name_and_unique_id_without_rule() -> None:
    """Test the naming of a switch created without a rule."""

    switch = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_CLIENT_NAME
    )

    assert switch.name == f"{FAKE_CLIENT_NAME} Block Internet"
    assert (
        switch.unique_id
        == f"{FAKE_ROUTER_MAC}_{FAKE_CLIENT_MAC}_block_internet"
    )


def test_name_falls_back_to_mac() -> None:
    """Test that a client without a name is named after its MAC."""

    switch = ClientInternetSwitch(mock_router(), FAKE_CLIENT_MAC, None)

    assert switch.name == f"{FAKE_CLIENT_MAC} Block Internet"


def test_unique_id_is_stable_with_and_without_rule() -> None:
    """Test that the unique id does not depend on the rule.

    Existing entities must be preserved when the switch is created from a
    client instead of from a rule.
    """

    from_rule = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_RULE_NAME, mock_rule()
    )
    from_client = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_CLIENT_NAME
    )

    assert from_rule.unique_id == from_client.unique_id


def test_new_rule_without_existing_rule() -> None:
    """Test that a rule is compiled from the client when none exists."""

    switch = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_CLIENT_NAME
    )

    rule = switch._new_rule(PCRuleType.BLOCK)

    assert rule.mac == FAKE_CLIENT_MAC.upper()
    assert rule.name == FAKE_CLIENT_NAME
    assert rule.type == PCRuleType.BLOCK


def test_new_rule_reuses_existing_rule() -> None:
    """Test that an existing rule keeps its own MAC and name."""

    existing = mock_rule()
    switch = ClientInternetSwitch(
        mock_router(), FAKE_CLIENT_MAC, FAKE_RULE_NAME, existing
    )

    rule = switch._new_rule(PCRuleType.DISABLE)

    assert rule.mac == existing.mac
    assert rule.name == existing.name
    assert rule.type == PCRuleType.DISABLE


def test_on_demand_update_picks_up_new_rule() -> None:
    """Test that a rule created on the device is picked up."""

    rule = mock_rule()
    router = mock_router(pc_rules={FAKE_CLIENT_MAC: rule})
    switch = ClientInternetSwitch(router, FAKE_CLIENT_MAC, FAKE_CLIENT_NAME)

    with patch.object(ClientInternetSwitch, "async_write_ha_state"):
        switch.async_on_demand_update()

    assert switch.is_on is True


def test_on_demand_update_handles_removed_rule() -> None:
    """Test that a rule removed on the device switches the state off.

    The rule can be removed on the device itself or via the
    `device_internet_access` action. The entity must not keep the stale
    state in that case.
    """

    router = mock_router()
    switch = ClientInternetSwitch(
        router, FAKE_CLIENT_MAC, FAKE_RULE_NAME, mock_rule()
    )
    assert switch.is_on is True

    with patch.object(ClientInternetSwitch, "async_write_ha_state"):
        switch.async_on_demand_update()

    assert switch.is_on is False


def test_add_entities_rules_only() -> None:
    """Test that only rule holders get a switch when not opted in."""

    router = mock_router(
        pc_rules={FAKE_CLIENT_MAC: mock_rule()},
        devices={"11:22:33:44:55:66": mock_client("other")},
        create_block_switches=False,
    )
    async_add_entities = Mock()
    tracked: set[str] = set()

    add_entities(router, async_add_entities, tracked)

    async_add_entities.assert_called_once()
    added = async_add_entities.call_args[0][0]
    assert len(added) == 1
    assert tracked == {FAKE_CLIENT_MAC}


def test_add_entities_all_clients() -> None:
    """Test that every client gets a switch when opted in."""

    other_mac = "11:22:33:44:55:66"
    router = mock_router(
        pc_rules={FAKE_CLIENT_MAC: mock_rule()},
        devices={
            FAKE_CLIENT_MAC: mock_client(),
            other_mac: mock_client("other"),
        },
        create_block_switches=True,
    )
    async_add_entities = Mock()
    tracked: set[str] = set()

    add_entities(router, async_add_entities, tracked)

    added = async_add_entities.call_args[0][0]
    assert len(added) == EXPECTED_TWO_SWITCHES
    assert tracked == {FAKE_CLIENT_MAC, other_mac}

    # The client which has a rule must use it
    with_rule = next(sw for sw in added if sw._mac == FAKE_CLIENT_MAC)
    assert with_rule.is_on is True

    # The other one has no rule yet
    without_rule = next(sw for sw in added if sw._mac == other_mac)
    assert without_rule.is_on is False


def test_add_entities_no_duplicates() -> None:
    """Test that a second run does not duplicate the entities."""

    router = mock_router(
        pc_rules={FAKE_CLIENT_MAC: mock_rule()},
        devices={FAKE_CLIENT_MAC: mock_client()},
        create_block_switches=True,
    )
    async_add_entities = Mock()
    tracked: set[str] = set()

    add_entities(router, async_add_entities, tracked)
    async_add_entities.reset_mock()
    add_entities(router, async_add_entities, tracked)

    async_add_entities.assert_not_called()
    assert tracked == {FAKE_CLIENT_MAC}
