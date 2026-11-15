"""AsusRouter parental control module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.parental_control import (
    ARBlockAllAction,
    ARBlockAllSourceUniversal,
    ARParentalControlAction,
    ARParentalControlCommand,
    ARParentalControlField,
    ARParentalControlSourceUniversal,
)
from homeassistant.const import EntityCategory

from ..entity import ARSwitchDescription

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_parental_control(
    data: Any,
) -> dict[ARParentalControlField, Any] | None:
    """Get the parental control state, None when nothing was read."""

    return data if isinstance(data, dict) and data else None


SWITCHES: tuple[ARSwitchDescription, ...] = (
    ARSwitchDescription(
        key="block_internet",
        translation_key="block_internet",
        source=ARBlockAllSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Block Internet",
        # The device reports its block, not keyed by its MAC
        data_fn=lambda data: data,
        value_fn=lambda data: data,
        action_fn=lambda state, _: ARBlockAllAction(state=state),
        supported_fn=lambda bridge: bridge.is_router,
        entity_category=EntityCategory.CONFIG,
    ),
    ARSwitchDescription(
        key="parental_control",
        translation_key="parental_control",
        source=ARParentalControlSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Parental control",
        # The device reports its parental control, not keyed by its MAC
        data_fn=_get_parental_control,
        value_fn=lambda data: data.get(ARParentalControlField.STATE),
        action_fn=lambda state, _: ARParentalControlAction(
            command=ARParentalControlCommand.STATE, state=state
        ),
        supported_fn=lambda bridge: bridge.is_router,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)
