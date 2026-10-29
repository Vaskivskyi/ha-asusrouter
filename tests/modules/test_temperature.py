"""Tests for the temperature module."""

from __future__ import annotations

from asusrouter.modules.temperature import (
    ARTemperatureSourceUniversal,
    ARTemperatureType,
)
import pytest

from custom_components.asusrouter.entity import ARSensorDescription
from custom_components.asusrouter.modules.temperature import SENSORS

DATA = {ARTemperatureType.CPU: 65.0, ARTemperatureType.RADIO_5G1: 68.0}

DESCRIPTIONS = {description.key: description for description in SENSORS}


@pytest.mark.parametrize(
    ("key", "unique_id_name"),
    [
        ("temperature_cpu", "Temperature CPU"),
        ("temperature_radio_2g1", "Temperature 2.4 GHz"),
        ("temperature_radio_2g2", "Temperature 2.4 GHz-2"),
        ("temperature_radio_5g1", "Temperature 5 GHz"),
        ("temperature_radio_5g2", "Temperature 5 GHz-2"),
        ("temperature_radio_6g1", "Temperature 6 GHz"),
        ("temperature_radio_6g2", "Temperature 6 GHz-2"),
    ],
)
def test_unique_id_names(key: str, unique_id_name: str) -> None:
    """Test that every sensor keeps its unique_id name."""

    assert DESCRIPTIONS[key].unique_id_name == unique_id_name


@pytest.mark.parametrize("description", SENSORS, ids=lambda d: d.key)
def test_sensor(description: ARSensorDescription) -> None:
    """Test that every sensor reads the whole device data."""

    assert description.source is ARTemperatureSourceUniversal
    assert description.data_fn is not None
    assert description.data_fn(DATA) is DATA
    # Only the router reads its temperatures
    assert description.node_source is None


@pytest.mark.parametrize(
    ("key", "value", "exists"),
    [
        ("temperature_cpu", 65.0, True),
        ("temperature_radio_5g1", 68.0, True),
        # Not reported by the device
        ("temperature_radio_6g1", None, False),
    ],
)
def test_value(key: str, value: float | None, exists: bool) -> None:
    """Test that a sensor exists only for a reported temperature."""

    description = DESCRIPTIONS[key]

    assert description.value_fn(DATA) == value
    assert description.exists_fn is not None
    assert description.exists_fn(DATA) is exists
