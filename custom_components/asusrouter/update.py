"""AsusRouter update module."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from asusrouter.modules.system import AsusSystem
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import STATIC_UPDATES
from .dataclass import ARUpdateDescription
from .entity import ARBinaryEntity, async_setup_ar_entry
from .merlin_update import (
    MerlinUpdateError,
    install_merlin_update,
    is_merlin_firmware,
)
from .router import ARDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AsusRouter updates."""

    updates = STATIC_UPDATES.copy()

    await async_setup_ar_entry(
        hass, config_entry, async_add_entities, updates, ARUpdate
    )


class ARUpdate(ARBinaryEntity, UpdateEntity):
    """AsusRouter update."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: ARDevice,
        description: ARUpdateDescription,
    ) -> None:
        """Initialize AsusRouter update."""

        super().__init__(coordinator, router, description)
        self.entity_description: ARUpdateDescription = description

        self._attr_installed_version = self.extra_state_attributes.get(
            "current"
        )
        self._attr_latest_version = self.extra_state_attributes.get("latest")
        self._attr_release_summary = self.extra_state_attributes.get(
            "release_note"
        )
        self._attr_in_progress = False

        self._attr_supported_features = (
            UpdateEntityFeature.RELEASE_NOTES
            | UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
        )

    def release_notes(self) -> str | None:
        """Return the release notes."""

        return self.extra_state_attributes.get("release_note")

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install the update."""
        target_version = version or self.latest_version

        if (
            is_merlin_firmware(self.installed_version)
            or is_merlin_firmware(target_version)
        ):
            await self._async_install_merlin(target_version)
            return

        try:
            _LOGGER.debug(
                "Trying to install Firmware update. "
                "This might take several minutes."
            )
            result = await self.api.async_set_state(
                state=AsusSystem.FIRMWARE_UPGRADE,
            )
            if not result:
                _LOGGER.debug(
                    "Something went wrong while trying to install the update."
                )
            else:
                self._attr_in_progress = True
                await asyncio.sleep(120)
                self._attr_in_progress = False

        except Exception as ex:  # noqa: BLE001
            _LOGGER.error(
                "An exception occurred while trying to install the update: %s",
                ex,
            )

    async def _async_install_merlin(self, target_version: str | None) -> None:
        """Install an Asuswrt-Merlin firmware update."""

        if target_version != self.latest_version:
            raise HomeAssistantError(
                "Installing a specific Merlin firmware version is not "
                "supported. Use the detected latest version."
            )

        if not target_version:
            raise HomeAssistantError("No Merlin firmware version is available")

        model = (
            self.router._identity.product_id
            if self.router._identity is not None
            else None
        )
        if not model:
            raise HomeAssistantError(
                "The router model is not available; cannot select a Merlin "
                "firmware image."
            )

        try:
            _LOGGER.info(
                "Trying to install Merlin firmware update `%s`",
                target_version,
            )
            self._attr_in_progress = 1
            self.async_write_ha_state()

            def _set_progress(progress: int) -> None:
                self._attr_in_progress = progress
                self.async_write_ha_state()

            await install_merlin_update(
                api=self.api,
                model=model,
                latest_version=target_version,
                progress=_set_progress,
            )
            await asyncio.sleep(120)
            try:
                await self.coordinator.async_request_refresh()
            except Exception as ex:  # noqa: BLE001
                _LOGGER.debug(
                    "Could not refresh firmware data after Merlin upload: %s",
                    ex,
                )

        except MerlinUpdateError as ex:
            raise HomeAssistantError(str(ex)) from ex
        except Exception as ex:
            _LOGGER.error(
                "An exception occurred while trying to install the Merlin "
                "firmware update: %s",
                ex,
            )
            raise HomeAssistantError(
                "An exception occurred while trying to install the Merlin "
                "firmware update."
            ) from ex
        finally:
            self._attr_in_progress = False
            self.async_write_ha_state()
