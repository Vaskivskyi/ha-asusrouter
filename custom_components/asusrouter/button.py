"""AsusRouter button module."""

from __future__ import annotations

import logging
from typing import Any

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

        self._service = description.service
        self._service_args = description.service_args
        self._service_expect_modify = description.service_expect_modify

    async def async_press(
        self,
        **kwargs: Any,
    ) -> None:
        """Press button."""

        try:
            result = await self.api.async_service_generic_apply(
                self._service,
                arguments=self._service_args,
                expect_modify=self._service_expect_modify,
            )
            if not result:
                _LOGGER.debug("Button press failed!")
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("Button press has returned an exception: %s", ex)
