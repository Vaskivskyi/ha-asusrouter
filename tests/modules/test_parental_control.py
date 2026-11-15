"""Tests for the parental control module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.parental_control import (
    ARBlockAllAction,
    ARBlockAllSourceUniversal,
    ARParentalControlAction,
    ARParentalControlCommand,
    ARParentalControlField,
    ARParentalControlSourceUniversal,
    ARParentalControlType,
)
from asusrouter.tools.identifiers import MacAddress
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.entity import ARSwitchDescription
from custom_components.asusrouter.modules.parental_control import SWITCHES

DESCRIPTIONS: dict[str, ARSwitchDescription] = {
    description.key: description for description in SWITCHES
}
BLOCK = DESCRIPTIONS["block_internet"]
PARENTAL_CONTROL = DESCRIPTIONS["parental_control"]

RULE: dict[ARParentalControlField, Any] = {
    ARParentalControlField.MAC: MacAddress.from_value("AA:BB:CC:DD:EE:01"),
    ARParentalControlField.TYPE: ARParentalControlType.TIME,
}
DATA: dict[ARParentalControlField, Any] = {
    ARParentalControlField.STATE: True,
    ARParentalControlField.RULES: [RULE],
}


@pytest.mark.parametrize(
    ("description", "unique_id_name", "source", "enabled"),
    [
        (BLOCK, "Block Internet", ARBlockAllSourceUniversal, True),
        (
            PARENTAL_CONTROL,
            "Parental control",
            ARParentalControlSourceUniversal,
            False,
        ),
    ],
)
def test_description(
    description: ARSwitchDescription,
    unique_id_name: str,
    source: Any,
    enabled: bool,
) -> None:
    """Test that every switch keeps its unique_id and default."""

    assert description.unique_id_name == unique_id_name
    assert description.source is source
    assert description.entity_category is EntityCategory.CONFIG
    assert description.entity_registry_enabled_default is enabled


@pytest.mark.parametrize("is_router", [True, False])
@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
def test_supported(description: ARSwitchDescription, is_router: bool) -> None:
    """Test that only a router has the parental control."""

    assert description.supported_fn is not None
    assert description.supported_fn(Mock(is_router=is_router)) is is_router


@pytest.mark.parametrize("state", [True, False])
def test_block(state: bool) -> None:
    """Test that the block reports and switches its state."""

    assert BLOCK.data_fn is not None
    assert BLOCK.value_fn(BLOCK.data_fn(state)) is state
    action = BLOCK.action_fn(state, state)
    assert isinstance(action, ARBlockAllAction)
    assert action.state is state


@pytest.mark.parametrize(
    ("data", "expected"),
    [(DATA, DATA), ({}, None), (None, None)],
)
def test_data(data: Any, expected: Any) -> None:
    """Test that nothing is read before the parental control state is."""

    assert PARENTAL_CONTROL.data_fn is not None
    assert PARENTAL_CONTROL.data_fn(data) == expected


@pytest.mark.parametrize("state", [True, False])
def test_parental_control(state: bool) -> None:
    """Test that the parental control reports and switches its state."""

    data = {**DATA, ARParentalControlField.STATE: state}

    assert PARENTAL_CONTROL.value_fn(data) is state
    action = PARENTAL_CONTROL.action_fn(state, data)
    assert isinstance(action, ARParentalControlAction)
    assert action.command is ARParentalControlCommand.STATE
    assert action.state is state


def test_no_attributes() -> None:
    """Test that the rules are not exposed as attributes."""

    assert PARENTAL_CONTROL.attributes_fn is None
