"""AsusRouter port forwarding module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.port_forwarding import (
    ARPortForwardingAction,
    ARPortForwardingCommand,
    ARPortForwardingField,
    ARPortForwardingProtocol,
    ARPortForwardingSourceUniversal,
)
from homeassistant.const import EntityCategory

from ..entity import ARSwitchDescription
from ..helpers import to_str, to_value

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_port_forwarding(data: Any) -> dict[ARPortForwardingField, Any] | None:
    """Get the port forwarding state, None when nothing was read."""

    return data if isinstance(data, dict) and data else None


def _get_rule(rule: dict[ARPortForwardingField, Any]) -> dict[str, Any]:
    """Get a rule as plain values."""

    return {
        "external_port": rule.get(ARPortForwardingField.EXTERNAL_PORT),
        "internal_ip": to_str(rule.get(ARPortForwardingField.INTERNAL_IP)),
        "internal_port": rule.get(ARPortForwardingField.INTERNAL_PORT),
        "name": rule.get(ARPortForwardingField.NAME),
        "protocol": to_value(
            rule.get(ARPortForwardingField.PROTOCOL), ARPortForwardingProtocol
        ),
        "protocol_number": rule.get(ARPortForwardingField.PROTOCOL_NUMBER),
        "source_ip": to_str(rule.get(ARPortForwardingField.SOURCE_IP)),
        "wan_unit": rule.get(ARPortForwardingField.WAN_UNIT),
    }


SWITCHES: tuple[ARSwitchDescription, ...] = (
    ARSwitchDescription(
        key="port_forwarding",
        translation_key="port_forwarding",
        source=ARPortForwardingSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Port forwarding",
        # The device reports its port forwarding, not keyed by its MAC
        data_fn=_get_port_forwarding,
        value_fn=lambda data: data.get(ARPortForwardingField.STATE),
        attributes_fn=lambda data: {
            "rules": [
                _get_rule(rule)
                for rule in data.get(ARPortForwardingField.RULES, [])
            ]
        },
        action_fn=lambda state, _: ARPortForwardingAction(
            command=ARPortForwardingCommand.STATE, state=state
        ),
        supported_fn=lambda bridge: bridge.is_router,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)
