"""Config flow module for AsusRouter."""

from __future__ import annotations

from collections.abc import Mapping
import logging
import socket
from typing import Any

from asusrouter.error import (
    AsusRouterAccessError,
    AsusRouterConnectionError,
    AsusRouterError,
    AsusRouterTimeoutError,
)
from asusrouter.modules.endpoint.error import ARAccessError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .bridge import ARBridge
from .const import (
    BASE,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_SSL,
    CONF_DEFAULT_USERNAME,
    DOMAIN,
    RESULT_ACCESS_ERROR,
    RESULT_CANNOT_RESOLVE,
    RESULT_CONNECTION_ERROR,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_TIMEOUT,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    STEP_CREDENTIALS,
    STEP_FIND,
    STEP_RECONFIGURE,
)

_LOGGER = logging.getLogger(__name__)

# Maps a library access error onto the string shown to the user
ACCESS_ERRORS: dict[ARAccessError, str] = {
    ARAccessError.CREDENTIALS: RESULT_WRONG_CREDENTIALS,
    ARAccessError.TRY_AGAIN: RESULT_LOGIN_BLOCKED,
    ARAccessError.RESET_REQUIRED: RESULT_LOGIN_BLOCKED,
    ARAccessError.CAPTCHA: RESULT_LOGIN_BLOCKED,
    ARAccessError.ANOTHER: RESULT_ERROR,
    ARAccessError.UNKNOWN: RESULT_UNKNOWN,
}


# ---------------------------
# HELPERS -->
# ---------------------------


def _check_host(host: str) -> bool:
    """Check whether the hostname can be resolved."""

    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        return False

    return True


async def _async_check_connection(
    hass: HomeAssistant,
    configs: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    """Connect to the device.

    Returns the device serial number, or the error which prevented connecting.
    """

    host = configs[CONF_HOST]

    _LOGGER.debug("Checking the connection to `%s`", host)

    bridge = ARBridge(hass, configs)

    try:
        await bridge.async_connect()
        # Serial number of the device is the best unique_id.
        # API provides it all the time for all the devices.
        # MAC as an alternative might not be used / found on some
        # older devices and some Merlin-builds of FW
        serial = bridge.identity.serial
    except AsusRouterAccessError as ex:
        error = ACCESS_ERRORS.get(ex.args[1], RESULT_ACCESS_ERROR)
        _LOGGER.debug(
            "Access error `%s` while connecting to `%s`: %s",
            error,
            host,
            ex,
        )
        return None, error
    except AsusRouterTimeoutError as ex:
        _LOGGER.debug("Timeout while connecting to `%s`: %s", host, ex)
        return None, RESULT_TIMEOUT
    except AsusRouterConnectionError as ex:
        _LOGGER.debug("Cannot connect to `%s`: %s", host, ex)
        return None, RESULT_CONNECTION_ERROR
    except AsusRouterError as ex:
        # Recognised by the library, but without a mapping of its own
        _LOGGER.debug(
            "Device error `%s` while connecting to `%s`: %s",
            type(ex).__name__,
            host,
            ex,
        )
        return None, RESULT_ERROR
    except Exception:
        # Only a genuine fault reaches this point, so keep the traceback
        _LOGGER.exception("Unknown error while connecting to `%s`", host)
        return None, RESULT_UNKNOWN
    finally:
        # Cleanup, so no unclosed sessions will be reported
        await bridge.async_close()

    return serial, None


# ---------------------------
# <-- HELPERS
# ---------------------------

# ---------------------------
# FORMS -->
# ---------------------------


def _create_form_find(
    user_input: Mapping[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the 'find' step."""

    user_input = user_input or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_HOST, default=user_input.get(CONF_HOST, "")
            ): cv.string,
        }
    )


def _create_form_credentials(
    user_input: Mapping[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the 'credentials' step."""

    user_input = user_input or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=user_input.get(CONF_USERNAME, CONF_DEFAULT_USERNAME),
            ): cv.string,
            vol.Required(
                CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
            ): cv.string,
            vol.Optional(
                CONF_PORT,
                default=user_input.get(CONF_PORT, CONF_DEFAULT_PORT),
            ): cv.positive_int,
            vol.Optional(
                CONF_SSL, default=user_input.get(CONF_SSL, CONF_DEFAULT_SSL)
            ): cv.boolean,
        }
    )


def _create_form_reconfigure(
    user_input: Mapping[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the `reconfigure` step."""

    return _create_form_find(user_input).extend(
        _create_form_credentials(user_input).schema
    )


# ---------------------------
# <-- FORMS
# ---------------------------


# ---------------------------
# CONFIG FLOW -->
# ---------------------------


class ARFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for AsusRouter."""

    # Connection settings live in the entry data, options are unused
    VERSION = 6

    def __init__(self) -> None:
        """Initialise config flow."""

        self._configs: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Flow initiated by user."""

        return await self.async_step_find(user_input)

    async def async_step_find(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Find the device step."""

        errors = {}

        if user_input:
            resolved = await self.hass.async_add_executor_job(
                _check_host, user_input[CONF_HOST]
            )
            if resolved:
                self._configs.update(user_input)
                return await self.async_step_credentials()

            errors[BASE] = RESULT_CANNOT_RESOLVE

        return self.async_show_form(
            step_id=STEP_FIND,
            data_schema=_create_form_find(user_input),
            errors=errors,
        )

    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Credentials step."""

        errors = {}

        if user_input:
            configs = {**self._configs, **user_input}
            serial, error = await _async_check_connection(self.hass, configs)

            if error:
                errors[BASE] = error
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: configs[CONF_HOST]}
                )

                return self.async_create_entry(
                    title=configs[CONF_HOST], data=configs
                )

        return self.async_show_form(
            step_id=STEP_CREDENTIALS,
            data_schema=_create_form_credentials(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Change the connection settings of a configured device."""

        entry = self._get_reconfigure_entry()

        errors = {}

        if user_input:
            serial, error = await _async_check_connection(
                self.hass, user_input
            )

            if error:
                errors[BASE] = error
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_mismatch()

                return self.async_update_reload_and_abort(
                    entry, data=user_input
                )

        return self.async_show_form(
            step_id=STEP_RECONFIGURE,
            data_schema=_create_form_reconfigure(user_input or entry.data),
            errors=errors,
        )


# ---------------------------
# <-- CONFIG FLOW
# ---------------------------
