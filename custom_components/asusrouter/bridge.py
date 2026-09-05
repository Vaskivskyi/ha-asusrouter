"""Bridge module for AsusRouter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
from asusrouter import AsusRouter
from asusrouter.config import ARConfigKey
from asusrouter.modules.device.identity import ARDeviceIdentity
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import DeviceInfo, format_mac

from .const import CONF_DEFAULT_PORT, DEFAULT_IDENTITY_NAME, DOMAIN

API_CONFIG: dict[ARConfigKey, Any] = {
    # Enable automatic temperature fix and disable the notification
    ARConfigKey.OPTIMISTIC_TEMPERATURE: True,
    ARConfigKey.NOTIFIED_OPTIMISTIC_TEMPERATURE: True,
}


class ARBridge:
    """Bridge to the AsusRouter library."""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: Mapping[str, Any],
    ) -> None:
        """Initialize bridge to the library."""

        session = async_create_clientsession(
            hass,
            # TODO: implement proper SSL verification eventually
            verify_ssl=False,
            # Routers set cookies for a bare IP and do not quote them
            cookie_jar=aiohttp.CookieJar(unsafe=True, quote_cookie=False),
        )

        self._api = self._get_api(configs, session)

    # ---------------------------
    # Properties -->
    # ---------------------------

    @property
    def api(self) -> AsusRouter:
        """Return API."""

        return self._api

    @property
    def identity(self) -> ARDeviceIdentity:
        """Return device identity."""

        return self._api.description

    # ---------------------------
    # <-- Properties
    # ---------------------------

    # ---------------------------
    # Connection -->
    # ---------------------------

    @staticmethod
    def _get_api(
        configs: Mapping[str, Any],
        session: aiohttp.ClientSession,
    ) -> AsusRouter:
        """Get AsusRouter API."""

        return AsusRouter(
            hostname=configs[CONF_HOST],
            username=configs[CONF_USERNAME],
            password=configs[CONF_PASSWORD],
            port=configs.get(CONF_PORT, CONF_DEFAULT_PORT),
            use_ssl=configs[CONF_SSL],
            session=session,
            config=API_CONFIG,
        )

    async def async_connect(self) -> None:
        """Connect to the device and read its identity."""

        await self._api.async_connect()

    async def async_close(self) -> None:
        """Log out from the device and release the connection."""

        await self._api.async_close()

    # ---------------------------
    # <-- Connection
    # ---------------------------

    # ---------------------------
    # Device -->
    # ---------------------------

    @staticmethod
    def _get_identifiers(identity: ARDeviceIdentity) -> set[tuple[str, str]]:
        """Get device identifiers."""

        identifiers: set[tuple[str, str]] = set()
        if identity.mac is not None:
            identifiers.add((DOMAIN, format_mac(str(identity.mac))))
        if identity.serial is not None:
            identifiers.add((DOMAIN, identity.serial))

        return identifiers

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""

        identity = self.identity
        firmware = identity.firmware

        return DeviceInfo(
            configuration_url=self._api.webpanel,
            identifiers=self._get_identifiers(identity),
            manufacturer=identity.brand,
            model=identity.model,
            model_id=identity.model_original,
            name=identity.model or DEFAULT_IDENTITY_NAME,
            serial_number=identity.serial,
            # Safelock against placeholders-filled string
            sw_version=str(firmware) if firmware.major is not None else None,
        )

    # ---------------------------
    # <-- Device
    # ---------------------------
