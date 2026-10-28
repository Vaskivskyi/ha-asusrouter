"""Tests for the clock module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from asusrouter.modules.clock import ARClockField, ARClockSourceUniversal
import pytest

from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules.clock import SENSORS

BOOTTIME = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
UPTIME = 3600

DATA = {
    ARClockField.BOOTTIME: BOOTTIME,
    ARClockField.DEVICE_TIME: datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
    ARClockField.UPTIME: UPTIME,
}

DESCRIPTIONS = {description.key: description for description in SENSORS}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "value"),
    [
        ("boot_time", "Boot Time", BOOTTIME),
        ("uptime", "Uptime", UPTIME),
    ],
)
def test_sensor(key: str, unique_id_name: str, value: Any) -> None:
    """Test that every sensor keeps its i0 unique_id and reads its value."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.value_fn(DATA) == value
    # An empty clock reports nothing
    assert description.value_fn({}) is None


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_source(description: ARSensorDescription) -> None:
    """Test that every sensor reads the whole clock of the device."""

    assert description.source is ARClockSourceUniversal
    assert description.data_fn is not None
    assert description.data_fn(DATA) is DATA
    # Only the router reads its clock
    assert description.node_source is None
