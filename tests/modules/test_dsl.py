"""Tests for the DSL module."""

from __future__ import annotations

from asusrouter.modules.common.metrics import ARMetricType
from asusrouter.modules.dsl import ARDSLSourceUniversal
from homeassistant.const import UnitOfDataRate
import pytest

from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules.dsl import SENSORS

DESCRIPTIONS: dict[str, ARSensorDescription] = {
    description.key: description for description in SENSORS
}

DOWN = 24_000_000.0
UP = 2_000_000.0
DATA = {ARMetricType.DOWNLOAD_SPEED: DOWN, ARMetricType.UPLOAD_SPEED: UP}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "value"),
    [
        ("dsl_datarate_down", "DSL Datarate Down", DOWN),
        ("dsl_datarate_up", "DSL Datarate Up", UP),
    ],
)
def test_rate(key: str, unique_id_name: str, value: float) -> None:
    """Test that every rate keeps its unique_id and reads its value."""

    description = DESCRIPTIONS[key]

    assert description.unique_id_name == unique_id_name
    assert description.source is ARDSLSourceUniversal
    assert description.native_unit_of_measurement == (
        UnitOfDataRate.BITS_PER_SECOND
    )
    assert description.suggested_unit_of_measurement == (
        UnitOfDataRate.KILOBITS_PER_SECOND
    )
    assert description.data_fn is not None
    assert description.data_fn(DATA) is DATA
    assert description.value_fn(DATA) == value


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_exists(description: ARSensorDescription) -> None:
    """Test that only a device reporting its DSL has the rates."""

    assert description.exists_fn is not None
    assert description.exists_fn(DATA) is True
    assert description.exists_fn({}) is False
