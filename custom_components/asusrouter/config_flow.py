"""Config flow for AsusRouter integration"""

import logging
_LOGGER = logging.getLogger(__name__)

import os
import socket

import voluptuous as vol

from homeassistant import config_entries

from homeassistant.components.device_tracker.const import (
    CONF_CONSIDER_HOME,
    DEFAULT_CONSIDER_HOME,
)

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_USE_SSL,
    CONF_CERT_PATH,
    CONF_CACHE_TIME,
    CONF_ENABLE_MONITOR,
    CONF_ENABLE_CONTROL,
    DEFAULT_USERNAME,
    DEFAULT_USE_SSL,
    DEFAULT_VERIFY_SSL,
    DEFAULT_ENABLE_MONITOR,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_CACHE_TIME,
    DEFAULT_PORT,
    DOMAIN,
)

from .bridge import AsusRouterBridge

_MSG_RESULT_SUCCESS = "success"
_MSG_RESULT_ERROR = "error"
_MSG_RESULT_UNKNOWN = "unknown"


def _get_ip(host):
    """Get the IP address for the hostname"""

    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


class ASUSRouterFlowHandler(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle config flow for AsusRouter"""

    VERSION = 1

    def __init__(self):
        """Initialise config flow"""

        self._host = None


    @callback
    def _show_setup_form(self, user_input = None, errors = None):
        """Show the setup form"""
        
        if user_input is None:
            user_input = {}

        schema = {
            vol.Optional(
                CONF_NAME,
                default = user_input.get(
                    CONF_NAME, ""
                )
            ): str,
            vol.Required(
                CONF_HOST,
                default = user_input.get(
                    CONF_HOST, ""
                )
            ): str,
            vol.Required(
                CONF_USERNAME,
                default = user_input.get(
                    CONF_USERNAME, DEFAULT_USERNAME
                )
            ): str,
            vol.Required(
                CONF_PASSWORD
            ): str,
            vol.Optional(
                CONF_PORT,
                default = user_input.get(
                    CONF_PORT, DEFAULT_PORT
                )
            ): int,
            vol.Optional(
                CONF_USE_SSL,
                default = user_input.get(
                    CONF_USE_SSL, DEFAULT_USE_SSL
                )
            ): bool,
            vol.Optional(
                CONF_VERIFY_SSL,
                default = user_input.get(
                    CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL
                )
            ): bool,
            vol.Optional(
                CONF_CERT_PATH,
                default = user_input.get(
                    CONF_CERT_PATH, ""
                )
            ): str,
            vol.Optional(
                CONF_ENABLE_MONITOR,
                default = user_input.get(
                    CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR
                )
            ): bool,
            vol.Optional(
                CONF_ENABLE_CONTROL,
                default = user_input.get(
                    CONF_ENABLE_CONTROL, DEFAULT_ENABLE_CONTROL
                )
            ): bool,
        }

        return self.async_show_form(
            step_id = "user",
            data_schema = vol.Schema(schema),
            errors = errors or {},
        )


    async def _async_check_connection(self, user_input):
        """Check if connection is possible"""

        api = AsusRouterBridge.get_bridge(self.hass, user_input)
        try:
            await api.async_connect()
        except OSError:
            _LOGGER.error("Error during connection for {}".format(self._host))
            return _MSG_RESULT_ERROR
        except Exception as ex:
            _LOGGER.error("Unknown error during connection for {}: {}".format(self._host, ex))
            return _MSG_RESULT_UNKNOWN

        await api.async_disconnect()

        return _MSG_RESULT_SUCCESS


    async def async_step_user(self, user_input = None):
        """Flow initiated by user"""

        if user_input is None:
            return self._show_setup_form(user_input)

        errors = {}
        self._host = user_input[CONF_HOST]
        password = user_input.get(CONF_PASSWORD)

        if not password:
            errors["base"] = "password_missing"

        if not errors:
            ip = await self.hass.async_add_executor_job(_get_ip, self._host)
            if not ip:
                errors["base"] = "cannot_resolve_host"

        if not errors:
            check = await self._async_check_connection(user_input)
            if check != _MSG_RESULT_SUCCESS:
                errors["base"] = check

        if errors:
            return self._show_setup_form(user_input, errors)

        return self.async_create_entry(
            title = self._host,
            data = user_input,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow"""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for AsusRouter"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow"""

        self.config_entry = config_entry


    async def async_step_init(self, user_input = None):
        """Handle options flow"""

        if user_input is not None:
            return self.async_create_entry(title = "", data = user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CACHE_TIME,
                    default = self.config_entry.options.get(
                        CONF_CACHE_TIME, DEFAULT_CACHE_TIME
                    )
                ): vol.All(vol.Coerce(int), vol.Clamp(min = 1, max = 3600)),
                
            }
        )

        return self.async_show_form(step_id = "init", data_schema = data_schema)


