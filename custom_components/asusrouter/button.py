"""AsusRouter buttons."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_ASUSROUTER,
    DOMAIN,
)
from .dataclass import ARButtonDescription
from .entity import ARButtonEntity
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)

BUTTONS = {
    "reboot": ARButtonDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart",
        service="reboot",
        service_args={},
        device_class=ButtonDeviceClass.RESTART,
        service_expect_modify=False,
        entity_registry_enabled_default=True,
    )
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup AsusRouter buttons."""

    router: ARDevice = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
    entities = []

    for button in BUTTONS:
        try:
            entities.append(ARButton(router, BUTTONS[button]))
        except Exception as ex:
            _LOGGER.warning(ex)

    async_add_entities(entities, True)


class ARButton(ARButtonEntity, ButtonEntity):
    """AsusRouter button."""

    def __init__(
        self,
        router: ARDevice,
        description: ARButtonDescription,
    ) -> None:
        """Initialize AsusRouter button."""

        super().__init__(router, description)
        self._service = description.service
        self._service_args = description.service_args
        self._service_expect_modify = description.service_expect_modify

    async def async_press(
        self,
        **kwargs: Any,
    ) -> None:
        """Press button."""

        try:
            result = await self.api.async_service_run(
                self._service,
                arguments=self._service_args,
                expect_modify=self._service_expect_modify,
            )
            if not result:
                _LOGGER.debug("Button press failed!")
        except Exception as ex:
            _LOGGER.error(f"Button press has returned an exception: {ex}")
