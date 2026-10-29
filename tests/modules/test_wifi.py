"""Tests for the WiFi module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.wifi import (
    ARWiFiAction,
    ARWiFiBand,
    ARWiFiBandwidth,
    ARWiFiField,
    ARWiFiSourceUniversal,
)
from homeassistant.const import EntityCategory
import pytest

from custom_components.asusrouter.entity import ARSwitchDescription
from custom_components.asusrouter.modules.wifi import SWITCHES

DESCRIPTIONS: dict[str, ARSwitchDescription] = {
    description.key: description for description in SWITCHES
}

RADIO: dict[ARWiFiField, Any] = {
    ARWiFiField.BANDWIDTH: ARWiFiBandwidth.WIDTH_80,
    ARWiFiField.CHANNEL: 36,
    ARWiFiField.CHANNEL_SPEC: "36/80",
    ARWiFiField.COUNTRY: "US",
    ARWiFiField.STATE: True,
}


@pytest.mark.parametrize(
    ("band", "unique_id_name"),
    [
        (ARWiFiBand.BAND_2G1, "Wireless 2.4 GHz"),
        (ARWiFiBand.BAND_2G2, "Wireless 2.4 GHz-2"),
        (ARWiFiBand.BAND_5G1, "Wireless 5 GHz"),
        (ARWiFiBand.BAND_5G2, "Wireless 5 GHz-2"),
        (ARWiFiBand.BAND_6G1, "Wireless 6 GHz"),
        (ARWiFiBand.BAND_6G2, "Wireless 6 GHz-2"),
    ],
)
def test_description(band: ARWiFiBand, unique_id_name: str) -> None:
    """Test that every radio is named by its band."""

    description = DESCRIPTIONS[f"wifi_{band.value}"]

    assert description.translation_key == f"wifi_{band.value}"
    assert description.unique_id_name == unique_id_name
    assert description.source is ARWiFiSourceUniversal
    assert description.entity_category is EntityCategory.CONFIG
    assert description.entity_registry_enabled_default is True


@pytest.mark.parametrize(
    ("bands", "expected"),
    [
        ({ARWiFiBand.BAND_5G1: 1}, True),
        # The 6 GHz radio is not a second 5 GHz one
        ({ARWiFiBand.BAND_6G1: 1}, False),
        ({}, False),
    ],
)
def test_supported(bands: dict[ARWiFiBand, int], expected: bool) -> None:
    """Test that a radio exists only on a device with its band."""

    description = DESCRIPTIONS["wifi_5g1"]
    bridge = Mock()
    bridge.identity.wifi = bands

    assert description.supported_fn is not None
    assert description.supported_fn(bridge) is expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({ARWiFiBand.BAND_5G1: RADIO}, RADIO),
        # The band is missing from the read
        ({ARWiFiBand.BAND_2G1: RADIO}, None),
        ({}, None),
        (None, None),
    ],
)
def test_data(data: Any, expected: Any) -> None:
    """Test that a radio reads the data of its band only."""

    description = DESCRIPTIONS["wifi_5g1"]

    assert description.data_fn is not None
    assert description.data_fn(data) == expected


@pytest.mark.parametrize("state", [True, False])
def test_value(state: bool) -> None:
    """Test that a radio reports its state."""

    description = DESCRIPTIONS["wifi_5g1"]

    assert description.value_fn({**RADIO, ARWiFiField.STATE: state}) is state


@pytest.mark.parametrize("state", [True, False])
def test_action(state: bool) -> None:
    """Test that a radio is switched by its library action."""

    action = DESCRIPTIONS["wifi_6g1"].action_fn(state, {})

    assert isinstance(action, ARWiFiAction)
    assert action.band is ARWiFiBand.BAND_6G1
    assert action.state is state


@pytest.mark.parametrize(
    ("bandwidth", "expected"),
    [
        (ARWiFiBandwidth.AUTO, "auto"),
        (ARWiFiBandwidth.WIDTH_80, 80),
        (ARWiFiBandwidth.WIDTH_320, 320),
        (ARWiFiBandwidth.UNKNOWN, None),
        (None, None),
    ],
)
def test_attributes(
    bandwidth: ARWiFiBandwidth | None, expected: int | str | None
) -> None:
    """Test that a radio reports its channel."""

    description = DESCRIPTIONS["wifi_5g1"]

    assert description.attributes_fn is not None
    assert description.attributes_fn(
        {**RADIO, ARWiFiField.BANDWIDTH: bandwidth}
    ) == {
        "channel": 36,
        "channel_bandwidth": expected,
        "chanspec": "36/80",
        "country_code": "US",
    }
