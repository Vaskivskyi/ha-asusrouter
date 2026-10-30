"""Tests for the port forwarding module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.port_forwarding import (
    ARPortForwardingAction,
    ARPortForwardingCommand,
    ARPortForwardingField,
    ARPortForwardingProtocol,
    ARPortForwardingSourceUniversal,
)
from asusrouter.tools.identifiers import IpAddress
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.modules.port_forwarding import SWITCHES

DESCRIPTION = SWITCHES[0]

RULE: dict[ARPortForwardingField, Any] = {
    ARPortForwardingField.EXTERNAL_PORT: "8080",
    ARPortForwardingField.INTERNAL_IP: IpAddress.from_value("192.168.1.10"),
    ARPortForwardingField.INTERNAL_PORT: "80",
    ARPortForwardingField.NAME: "Web",
    ARPortForwardingField.PROTOCOL: ARPortForwardingProtocol.TCP,
    ARPortForwardingField.WAN_UNIT: 0,
}
OTHER_RULE: dict[ARPortForwardingField, Any] = {
    ARPortForwardingField.INTERNAL_IP: IpAddress.from_value("192.168.1.11"),
    ARPortForwardingField.PROTOCOL: ARPortForwardingProtocol.OTHER,
    ARPortForwardingField.PROTOCOL_NUMBER: 47,
    ARPortForwardingField.WAN_UNIT: 1,
}
DATA: dict[ARPortForwardingField, Any] = {
    ARPortForwardingField.STATE: True,
    ARPortForwardingField.RULES: [RULE, OTHER_RULE],
}


def test_description() -> None:
    """Test that the port forwarding keeps its unique_id and default."""

    assert DESCRIPTION.translation_key == "port_forwarding"
    assert DESCRIPTION.unique_id_name == "Port forwarding"
    assert DESCRIPTION.source is ARPortForwardingSourceUniversal
    assert DESCRIPTION.entity_category is EntityCategory.CONFIG
    assert DESCRIPTION.entity_registry_enabled_default is False


@pytest.mark.parametrize("is_router", [True, False])
def test_supported(is_router: bool) -> None:
    """Test that only a router has the port forwarding."""

    assert DESCRIPTION.supported_fn is not None
    assert DESCRIPTION.supported_fn(Mock(is_router=is_router)) is is_router


@pytest.mark.parametrize(
    ("data", "expected"),
    [(DATA, DATA), ({}, None), (None, None)],
)
def test_data(data: Any, expected: Any) -> None:
    """Test that nothing is read before the port forwarding state is."""

    assert DESCRIPTION.data_fn is not None
    assert DESCRIPTION.data_fn(data) == expected


@pytest.mark.parametrize("state", [True, False])
def test_value(state: bool) -> None:
    """Test that the port forwarding reports its state."""

    assert (
        DESCRIPTION.value_fn({**DATA, ARPortForwardingField.STATE: state})
        is state
    )


@pytest.mark.parametrize("state", [True, False])
def test_action(state: bool) -> None:
    """Test that the port forwarding is switched by its library action."""

    assert DESCRIPTION.action_fn(state, DATA) == ARPortForwardingAction(
        command=ARPortForwardingCommand.STATE, state=state
    )


def test_attributes() -> None:
    """Test that the port forwarding reports every rule."""

    assert DESCRIPTION.attributes_fn is not None
    assert DESCRIPTION.attributes_fn(DATA) == {
        "rules": [
            {
                "external_port": "8080",
                "internal_ip": "192.168.1.10",
                "internal_port": "80",
                "name": "Web",
                "protocol": "TCP",
                "protocol_number": None,
                "source_ip": None,
                "wan_unit": 0,
            },
            {
                "external_port": None,
                "internal_ip": "192.168.1.11",
                "internal_port": None,
                "name": None,
                "protocol": "OTHER",
                "protocol_number": 47,
                "source_ip": None,
                "wan_unit": 1,
            },
        ]
    }


def test_attributes_unknown() -> None:
    """Test that an unknown protocol and a missing rule list report nothing."""

    unknown = {
        ARPortForwardingField.PROTOCOL: ARPortForwardingProtocol.UNKNOWN
    }
    data = {ARPortForwardingField.RULES: [unknown]}

    assert DESCRIPTION.attributes_fn is not None
    rules = DESCRIPTION.attributes_fn(data)["rules"]
    assert rules[0]["protocol"] is None
    assert DESCRIPTION.attributes_fn({ARPortForwardingField.STATE: True}) == {
        "rules": []
    }
