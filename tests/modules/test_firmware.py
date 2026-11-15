"""Tests for the firmware module."""

from __future__ import annotations

from typing import Any

from asusrouter.modules.firmware import (
    ARFirmware,
    ARFirmwareSourceUniversal,
    ARFirmwareState,
    ARFirmwareWeb,
)
from homeassistant.components.update import UpdateDeviceClass
import pytest

from custom_components.asusrouter.entity import ARUpdateDescription
from custom_components.asusrouter.modules.firmware import UPDATES

DESCRIPTIONS: dict[str, ARUpdateDescription] = {
    description.key: description for description in UPDATES
}
STABLE = DESCRIPTIONS["firmware"]
BETA = DESCRIPTIONS["firmware_beta"]

CURRENT = "3.0.0.4.388.24000_0"
AVAILABLE = "3.0.0.4.388.25000_0"
AVAILABLE_BETA = "3.0.0.6.102.30000_0"


def _get_state(**web: Any) -> ARFirmwareState:
    """Create a firmware state."""

    return ARFirmwareState(
        current=ARFirmware.from_string(CURRENT), web=ARFirmwareWeb(**web)
    )


@pytest.mark.parametrize(
    ("description", "unique_id_name", "enabled"),
    [
        (STABLE, "Firmware update", True),
        (BETA, "Firmware update (Beta)", False),
    ],
)
def test_description(
    description: ARUpdateDescription, unique_id_name: str, enabled: bool
) -> None:
    """Test that every update keeps its unique_id and default."""

    assert description.unique_id_name == unique_id_name
    assert description.source is ARFirmwareSourceUniversal
    assert description.device_class is UpdateDeviceClass.FIRMWARE
    assert description.entity_registry_enabled_default is enabled


@pytest.mark.parametrize("data", [{}, None])
def test_data_unread(data: Any) -> None:
    """Test that nothing is read before the firmware is."""

    assert STABLE.data_fn is not None
    assert STABLE.data_fn(data) is None


@pytest.mark.parametrize("description", UPDATES, ids=lambda d: d.key)
def test_installed(description: ARUpdateDescription) -> None:
    """Test that every update reports the installed version."""

    firmware = _get_state()

    assert description.data_fn is not None
    assert description.data_fn(firmware) is firmware
    assert description.value_fn(firmware) == CURRENT
    assert description.value_fn(ARFirmwareState()) is None


@pytest.mark.parametrize(
    ("web", "stable", "beta"),
    [
        (
            {
                "available": ARFirmware.from_string(AVAILABLE),
                "available_beta": ARFirmware.from_string(AVAILABLE_BETA),
                "state": True,
                "state_beta": True,
            },
            AVAILABLE,
            AVAILABLE_BETA,
        ),
        # A version without the update flag is no update
        (
            {
                "available": ARFirmware.from_string(AVAILABLE),
                "available_beta": ARFirmware.from_string(AVAILABLE_BETA),
            },
            CURRENT,
            CURRENT,
        ),
        ({"state": True, "state_beta": True}, CURRENT, CURRENT),
    ],
)
def test_latest(web: dict[str, Any], stable: str, beta: str) -> None:
    """Test that the latest version is the available update."""

    firmware = _get_state(**web)

    assert STABLE.latest_fn(firmware) == stable
    assert BETA.latest_fn(firmware) == beta


def test_release_notes() -> None:
    """Test that only the stable update reports the release notes."""

    assert STABLE.release_notes_fn is not None
    assert STABLE.release_notes_fn(_get_state(release_note="Notes")) == "Notes"
    assert BETA.release_notes_fn is None
