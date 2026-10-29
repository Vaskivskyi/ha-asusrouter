"""Tests for the sysinfo module."""

from __future__ import annotations

from asusrouter.modules.sysinfo import ARSysInfoSourceUniversal, ARSysInfoType
import pytest

from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules.sysinfo import SENSORS

DATA = {ARSysInfoType.LOAD_AVERAGE: {1: 0.5, 5: 0.25, 15: 0.1}}

DESCRIPTIONS = {description.key: description for description in SENSORS}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "value"),
    [
        ("load_average_1", "Load Average (1 min)", 0.5),
        ("load_average_5", "Load Average (5 min)", 0.25),
        ("load_average_15", "Load Average (15 min)", 0.1),
    ],
)
def test_load_average(key: str, unique_id_name: str, value: float) -> None:
    """Test that every window keeps its unique_id and reads its value."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.value_fn(DATA) == value
    assert description.exists_fn is not None
    assert description.exists_fn(DATA) is True


@pytest.mark.parametrize(
    "data",
    [
        # Stock firmware has no sysinfo
        {},
        {ARSysInfoType.LOAD_AVERAGE: {1: 0.5}},
    ],
)
def test_load_average_missing(
    data: dict[ARSysInfoType, dict[int, float]],
) -> None:
    """Test that a window not reported gets no sensor."""

    description = DESCRIPTIONS["load_average_15"]

    assert description.value_fn(data) is None
    assert description.exists_fn is not None
    assert description.exists_fn(data) is False


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_source(description: ARSensorDescription) -> None:
    """Test that every sensor reads the whole sysinfo of the device."""

    assert description.source is ARSysInfoSourceUniversal
    assert description.data_fn is not None
    assert description.data_fn(DATA) is DATA
    # Only the router reads its sysinfo
    assert description.node_source is None
