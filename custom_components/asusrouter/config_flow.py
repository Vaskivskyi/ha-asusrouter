"""Config flow for AsusRouter integration"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from typing import Any

import socket

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_PORT,
    CONF_VERIFY_SSL,
    CONF_SSL,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    CONF_INTERFACES,
    DEFAULT_CACHE_TIME,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_ENABLE_MONITOR,
    DELAULT_INTERFACES,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_USERNAME,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    RESULT_ERROR,
    RESULT_SUCCESS,
    RESULT_UNKNOWN,
)

from .bridge import AsusRouterBridge


def _get_ip(host):
    """Get the IP address for the hostname"""

    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


async def async_get_network_interfaces(hass : HomeAssistant, user_input : dict[str, Any]) -> list[str]:
    """Return list of possible to monitor network interfaces"""

    api = AsusRouterBridge.get_bridge(hass = hass, conf = user_input)

    try:
        labels = await api.async_get_network_interfaces()
        await api.async_disconnect()
        return labels
    except Exception as ex:
        _LOGGER.debug("Cannot get available network stat sensors for {}: {}".format(user_input[CONF_HOST], ex))
        return DELAULT_INTERFACES


class ASUSRouterFlowHandler(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle config flow for AsusRouter"""

    VERSION = 2

    def __init__(self):
        """Initialise config flow"""

        self._host = None
        self._input = dict()


    @callback
    def _show_form_device(self, user_input = None, errors = None):
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
                CONF_SSL,
                default = user_input.get(
                    CONF_SSL, DEFAULT_SSL
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
            step_id = "device",
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
            return RESULT_ERROR
        except Exception as ex:
            _LOGGER.error("Unknown error during connection for {}: {}".format(self._host, ex))
            return RESULT_UNKNOWN

        await api.async_disconnect()

        return RESULT_SUCCESS


    async def async_step_user(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Flow initiated by user"""

        return await self.async_step_device(user_input)


    async def async_step_device(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Step to setup the device"""

        if not user_input:
            return self._show_form_device(user_input)

        self._input = user_input
        self._host = user_input[CONF_HOST]

        errors = dict()

        ip = await self.hass.async_add_executor_job(_get_ip, user_input[CONF_HOST])
        if not ip:
            errors["base"] = "cannot_resolve_host"

        if not errors:
            check = await self._async_check_connection(user_input)
            if check != RESULT_SUCCESS:
                errors["base"] = check

        if errors:
            _LOGGER.error("Some errors appear to happen")
            return self._show_form_device(user_input, errors)

        return await self.async_step_interfaces()


    async def async_step_interfaces(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Step to select interfaces for traffic monitoring"""

        if not user_input:
            interfaces = await async_get_network_interfaces(self.hass, self._input)
            return self.async_show_form(
                step_id="interfaces",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_INTERFACES): cv.multi_select(
                            {k: k for k in interfaces}
                        ),
                    }
                ),
            )

        return self.async_create_entry(
            title = self._host,
            data = self._input,
            options = user_input,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow"""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for AsusRouter"""

    def __init__(self, config_entry : config_entries.ConfigEntry) -> None:
        """Initialize options flow"""

        self.config_entry = config_entry


    async def async_step_init(self, user_input = None):
        """Handle options flow"""

        if not user_input:
            configured_interfaces : list[str] = self.config_entry.options[CONF_INTERFACES]
            interfaces = await async_get_network_interfaces(self.hass, self.config_entry.data)

            # If interface was tracked, but cannot be found now, still add it
            for interface in configured_interfaces:
                if not interface in interfaces:
                    interfaces.append(interface)

            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_INTERFACES,
                        default = configured_interfaces
                    ): cv.multi_select({k: k for k in interfaces}),

                    vol.Optional(
                        CONF_CACHE_TIME,
                        default = self.config_entry.options.get(
                            CONF_CACHE_TIME, DEFAULT_CACHE_TIME
                        )
                    ): vol.All(vol.Coerce(int), vol.Clamp(min = 1, max = 3600)),
                    
                }
            )

            return self.async_show_form(step_id = "init", data_schema = data_schema)

        return self.async_create_entry(title = self.config_entry.data[CONF_HOST], data = user_input)


