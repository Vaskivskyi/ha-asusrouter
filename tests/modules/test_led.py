"""Tests for the LED module."""

from __future__ import annotations

from asusrouter.modules.led import (
    ARLedAction,
    ARLedField,
    ARLedSourceUniversal,
)
import pytest

from custom_components.asusrouter.modules.led import LIGHTS

DESCRIPTION = LIGHTS[0]


def test_led() -> None:
    """Test that the LED keeps its unique_id and reads its state."""

    data = {ARLedField.STATE: True}

    assert DESCRIPTION.unique_id_name == "LED"
    assert DESCRIPTION.source is ARLedSourceUniversal
    assert DESCRIPTION.data_fn is not None
    assert DESCRIPTION.data_fn(data) is data
    assert DESCRIPTION.value_fn(data) is True
    # An empty read reports nothing
    assert DESCRIPTION.value_fn({}) is None
    # Only the router reads its LED
    assert DESCRIPTION.node_source is None


@pytest.mark.parametrize("state", [True, False])
def test_led_action(state: bool) -> None:
    """Test that the LED is switched by its library action."""

    assert DESCRIPTION.action_fn(state) == ARLedAction(state=state)
