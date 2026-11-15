"""AsusRouter firmware module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.firmware import (
    ARFirmwareSourceUniversal,
    ARFirmwareState,
)
from homeassistant.components.update import UpdateDeviceClass

from ..entity import ARUpdateDescription
from ..helpers import to_version

UPDATE_INTERVAL = timedelta(minutes=5)


def _get_firmware(data: Any) -> ARFirmwareState | None:
    """Get the firmware state, None when nothing was read."""

    return data if isinstance(data, ARFirmwareState) else None


def _get_latest(firmware: ARFirmwareState, *, beta: bool) -> str | None:
    """Get the latest version, the installed one without an update."""

    web = firmware.web
    available = web.available_beta if beta else web.available
    state = web.state_beta if beta else web.state

    return to_version(available if state and available else firmware.current)


UPDATES: tuple[ARUpdateDescription, ...] = (
    ARUpdateDescription(
        key="firmware",
        translation_key="firmware",
        source=ARFirmwareSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Firmware update",
        # The device reports its firmware, not keyed by its MAC
        data_fn=_get_firmware,
        value_fn=lambda firmware: to_version(firmware.current),
        latest_fn=lambda firmware: _get_latest(firmware, beta=False),
        release_notes_fn=lambda firmware: firmware.web.release_note,
        device_class=UpdateDeviceClass.FIRMWARE,
    ),
    ARUpdateDescription(
        key="firmware_beta",
        translation_key="firmware_beta",
        source=ARFirmwareSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Firmware update (Beta)",
        # The device reports its firmware, not keyed by its MAC
        data_fn=_get_firmware,
        value_fn=lambda firmware: to_version(firmware.current),
        latest_fn=lambda firmware: _get_latest(firmware, beta=True),
        device_class=UpdateDeviceClass.FIRMWARE,
        entity_registry_enabled_default=False,
    ),
)
