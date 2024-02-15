"""AsusRouter button module."""

from __future__ import annotations

import logging
from typing import Any, Optional

from asusrouter.modules.state import AsusState
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ASUSROUTER,
    CONF_MODE,
    DOMAIN,
    ROUTER,
    STATIC_BUTTONS,
    STATIC_BUTTONS_OPTIONAL,
)
from .dataclass import ARButtonDescription
from .helpers import to_unique_id
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter buttons."""

    buttons = STATIC_BUTTONS.copy()

    router: ARDevice = hass.data[DOMAIN][config_entry.entry_id][ASUSROUTER]
    entities = []

    if config_entry.options.get(CONF_MODE) == ROUTER:
        buttons.extend(STATIC_BUTTONS_OPTIONAL)

    for button in buttons:
        try:
            entities.append(ARButton(router, button))
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning(ex)

    async_add_entities(entities)


class ARButton(ButtonEntity):
    """AsusRouter button."""

    def __init__(
        self,
        router: ARDevice,
        description: ARButtonDescription,
    ) -> None:
        """Initialize AsusRouter button."""

        self.router = router
        self.api = router.bridge.api

        self._attr_device_info = router.device_info
        self._attr_name = f"{router._conf_name} {description.name}"
        self._attr_unique_id = to_unique_id(f"{router.mac}_{description.name}")
        self._attr_capability_attributes = description.capabilities

        self._state = description.state
        self._state_args = description.state_args
        self._state_expect_modify = description.state_expect_modify

        if description.icon:
            self._attr_icon = description.icon

    async def async_press(
        self,
        **kwargs: Any,
    ) -> None:
        """Press button."""

        kwargs = self._state_args if self._state_args is not None else {}

        await self._set_state(
            state=self._state,
            expect_modify=self._state_expect_modify,
            **kwargs,
        )

    async def _set_state(
        self,
        state: AsusState,
        expect_modify: bool = False,
        **kwargs: Any,
    ) -> None:
        """Set switch state."""

        try:
            _LOGGER.debug("Pressing %s", state)
            result = await self.api.async_set_state(
                state=state, expect_modify=expect_modify, **kwargs
            )
            if not result:
                _LOGGER.debug("Didn't manage to press %s", state)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Pressing %s caused an exception: %s", state, ex)
