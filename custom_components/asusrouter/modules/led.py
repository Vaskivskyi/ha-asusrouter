"""AsusRouter LED module."""

from __future__ import annotations

from datetime import timedelta

from asusrouter.modules.led import (
    ARLedAction,
    ARLedField,
    ARLedSourceUniversal,
)
from homeassistant.const import EntityCategory

from ..entity import ARLightDescription

UPDATE_INTERVAL = timedelta(seconds=30)

LIGHTS: tuple[ARLightDescription, ...] = (
    ARLightDescription(
        key="led",
        translation_key="led",
        source=ARLedSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="LED",
        # The device reports its LED, not keyed by its MAC
        data_fn=lambda data: data,
        value_fn=lambda data: data.get(ARLedField.STATE),
        action_fn=lambda state: ARLedAction(state=state),
        entity_category=EntityCategory.CONFIG,
    ),
)
