"""Tests for the system status module."""

from __future__ import annotations

from typing import Any

from asusrouter.modules.common.metrics import ARMetricType
from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
    ARSystemType,
)
import pytest

from custom_components.asusrouter.modules.system_status import (
    SENSORS,
    _get_usage,
    _get_usage_sensor,
)

USAGE = ARMetricType.USAGE

DATA: dict[Any, Any] = {
    ARSystemType.CPU: {USAGE: 12},
    ARSystemType.RAM: {USAGE: 70},
}


@pytest.mark.parametrize(
    ("data", "system_type", "expected"),
    [
        (DATA, ARSystemType.CPU, 12),
        (DATA, ARSystemType.RAM, 70),
        (DATA, ARSystemType.CORE_1, None),
        ({}, ARSystemType.CPU, None),
    ],
)
def test_get_usage(
    data: dict[Any, Any], system_type: ARSystemType, expected: Any
) -> None:
    """Test that the usage of a component is read."""

    assert _get_usage(data, system_type) == expected


def test_get_usage_sensor() -> None:
    """Test that a usage sensor reads its own component."""

    description = _get_usage_sensor("ram", "RAM", ARSystemType.RAM)

    assert description.key == description.translation_key == "ram"
    assert description.unique_id_name == "RAM"
    assert description.source is ARSystemStatusSourceUniversal
    assert description.value_fn(DATA) == DATA[ARSystemType.RAM][USAGE]


@pytest.mark.parametrize(
    ("key", "unique_id_name", "value"),
    [
        ("cpu", "CPU", 12),
        ("ram", "RAM", 70),
    ],
)
def test_sensors(key: str, unique_id_name: str, value: Any) -> None:
    """Test that each sensor keeps its unique_id name and reads its usage."""

    description = next(item for item in SENSORS if item.key == key)

    assert description.unique_id_name == unique_id_name
    assert description.value_fn(DATA) == value
    assert description.entity_registry_enabled_default is False
    # Nodes report their usage through the router
    assert description.node_source is ARSystemStatusSource
