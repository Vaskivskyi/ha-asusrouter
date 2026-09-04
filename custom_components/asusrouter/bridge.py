"""AsusRouter bridge module."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from asusrouter import AsusRouter
from asusrouter.config import ARConfigKey as ARConfKey
from asusrouter.const import DEFAULT_IDENTITY_BRAND
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
from homeassistant.helpers.device_registry import format_mac

from .const import CONF_DEFAULT_PORT, DEFAULT_IDENTITY_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ARBridge:
    """Bridge to the AsusRouter library."""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize bridge to the library."""

        self.hass = hass

        # Save all the HA configs and options
        self._configs = configs.copy()
        if options:
            self._configs.update(options)

        # Get session from HA
        # By default, don't verify SSL <- this is a temp solution
        # which should be done properly in the future
        session = async_create_clientsession(
            hass,
            verify_ssl=False,
            # Routers set cookies for a bare IP and do not quote them
            cookie_jar=aiohttp.CookieJar(unsafe=True, quote_cookie=False),
        )

        # Initialize API
        self._api = self._get_api(
            self._configs, session, self._get_api_config()
        )

        self._host = self._configs[CONF_HOST]

        # Define properties
        self._identifiers: set[tuple[str, str]] = set()
        self._manufacturer = DEFAULT_IDENTITY_BRAND
        self._model: str | None = None
        self._model_id: str | None = None
        self._name: str = DEFAULT_IDENTITY_NAME
        self._serial_number: str | None = None
        self._sw_version: str | None = None

    @staticmethod
    def _get_api(
        configs: dict[str, Any],
        session: aiohttp.ClientSession,
        config: dict[ARConfKey, Any],
    ) -> AsusRouter:
        """Get AsusRouter API."""

        return AsusRouter(
            hostname=configs[CONF_HOST],
            username=configs[CONF_USERNAME],
            password=configs[CONF_PASSWORD],
            port=configs.get(CONF_PORT, CONF_DEFAULT_PORT),
            use_ssl=configs[CONF_SSL],
            session=session,
            config=config,
        )

    def _get_api_config(self) -> dict[ARConfKey, Any]:
        """Get configuration for AsusRouter instance."""

        return {
            # Enable automatic temperature fix
            ARConfKey.OPTIMISTIC_TEMPERATURE: True,
            # Disable log warning message
            ARConfKey.NOTIFIED_OPTIMISTIC_TEMPERATURE: True,
        }

    @property
    def api(self) -> AsusRouter:
        """Return API."""

        return self._api

    @property
    def configuration_url(self) -> str:
        """Return device configuration URL."""

        return self._api.webpanel

    @property
    def connected(self) -> bool:
        """Return connection state."""

        return self._api.connected

    @property
    def identifiers(self) -> set[tuple[str, str]]:
        """Return device identifiers."""

        return self._identifiers

    @property
    def identity(self) -> ARDeviceIdentity:
        """Return device identity."""

        return self._api.description

    @property
    def manufacturer(self) -> str:
        """Return device manufacturer."""

        return self._manufacturer

    @property
    def model(self) -> str | None:
        """Return device model."""

        return self._model

    @property
    def model_id(self) -> str | None:
        """Return device model ID."""

        return self._model_id

    @property
    def name(self) -> str:
        """Return device name."""

        return self._name

    @property
    def serial_number(self) -> str | None:
        """Return device serial number."""

        return self._serial_number

    @property
    def sw_version(self) -> str | None:
        """Return device software version."""

        return self._sw_version

    # --------------------
    # Connection -->
    # --------------------

    async def async_connect(self) -> None:
        """Connect to the device."""

        _LOGGER.debug("Connecting to the API")

        await self.api.async_connect()
        identity = self.identity

        # Set properties
        self._identifiers = set()
        if identity.mac is not None:
            self._identifiers.add((DOMAIN, format_mac(str(identity.mac))))
        if identity.serial is not None:
            self._identifiers.add((DOMAIN, identity.serial))
        self._manufacturer = identity.brand
        self._model = identity.model
        self._model_id = identity.model_original
        self._name = identity.model or DEFAULT_IDENTITY_NAME
        self._serial_number = identity.serial
        # An empty version renders as a placeholder string, not as nothing
        self._sw_version = (
            str(identity.firmware)
            if identity.firmware.major is not None
            else None
        )

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""

        _LOGGER.debug("Disconnecting from the API")

        await self.api.async_disconnect()

    async def async_clean(self) -> None:
        """Cleanup."""

        _LOGGER.debug("Cleaning up")

        await self.api.async_close()

    # --------------------
    # <-- Connection
    # --------------------
