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
    RESULT_CONNECTION_REFUSED,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_SUCCESS,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    SIMPLE_SETUP_PARAMETERS,
)

from .bridge import AsusRouterBridge
from asusrouter import AsusRouterConnectionError, AsusRouterLoginBlockError, AsusRouterLoginError


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
        self._unique_id = None
        self._simple = False


    async def _async_check_connection(self, user_input : dict[str, Any]) -> str:
        """Check if connection is possible"""

        step_type = "complete"

        config = self._input.copy()
        config.update(user_input)

        if self._simple:
            config.update(SIMPLE_SETUP_PARAMETERS["ssl"] if user_input[CONF_SSL] else SIMPLE_SETUP_PARAMETERS["no_ssl"])
            step_type = "simplified"

        _LOGGER.debug("Setup ({}) initiated".format(step_type))

        api = AsusRouterBridge.get_bridge(self.hass, config)

        try:
            await api.async_connect()
        # Credentials error
        except AsusRouterLoginError:
            _LOGGER.error("Error during connection to '{}'. Wrong credentials".format(self._host))
            return RESULT_WRONG_CREDENTIALS
        # Login blocked by the device
        except AsusRouterLoginBlockError as ex:
            _LOGGER.error("Device '{}' has reported block for the login (to many wrong attempts were made). Please try again in {} seconds".format(self._host, ex.timeout))
            return RESULT_LOGIN_BLOCKED
        # Connection refused
        except AsusRouterConnectionError as ex:
            if self._simple:
                _LOGGER.debug("Simplified setup failed for {}. Switching to the complete mode. Original exception of type {}: {}".format(self._host, type(ex), ex))
            else:
                _LOGGER.error("Connection refused by {}. Check SSL and port settings. Original exception: {}".format(self._host, ex))
            return RESULT_CONNECTION_REFUSED
        # Anything else
        except Exception as ex:
            if self._simple:
                _LOGGER.debug("Simplified setup failed for {}. Switching to the complete mode. Original exception of type {}: {}".format(self._host, type(ex), ex))
            else:
                _LOGGER.error("Unknown error of type '{}' during connection to {}: {}".format(type(ex), self._host, ex))
            return RESULT_UNKNOWN
        # Cleanup, so no unclosed sessions will be reported
        finally:
            await api.async_clean()

        self._unique_id = await api.get_serial()
        await api.async_disconnect()
        self._input.update(config)

        _LOGGER.debug("Setup ({}) successful".format(step_type))

        return RESULT_SUCCESS


    ### USER SETUP -->


    async def async_step_user(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Flow initiated by user"""

        return await self.async_step_discovery(user_input)


    # Step #1 - discover the device
    async def async_step_discovery(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Device discovery step"""

        errors = dict()

        if user_input:
            self._input.update(user_input)
            self._host = user_input[CONF_HOST]

            ip = await self.hass.async_add_executor_job(_get_ip, user_input[CONF_HOST])
            if not ip:
                errors["base"] = "cannot_resolve_host"

            if not errors:
                return await self.async_step_credentials()

        if not user_input:
            user_input = dict()

        return self.async_show_form(
            step_id = "discovery",
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default = user_input.get(
                            CONF_HOST, ""
                        )
                    ): str,
                }
            ),
            errors = errors
        )


    # Step #2 - credentials and SSL (simplified setup)
    async def async_step_credentials(self, user_input : dict[str, Any] | None = None, errors : dict[str, str] = dict()) -> FlowResult:
        """Credentials step"""

        if user_input:
            self._input.update(user_input)
            self._simple = True
            check = await self._async_check_connection(user_input)
            if check != RESULT_SUCCESS:
                errors["base"] = check
                if (check != RESULT_WRONG_CREDENTIALS
                    and check != RESULT_LOGIN_BLOCKED
                ):
                    return await self.async_step_device(errors = errors)

            if not errors:
                await self.async_set_unique_id(self._unique_id)
                return await self.async_step_operation_mode()
                
        if not user_input:
            user_input = self._input.copy()

        return self.async_show_form(
            step_id = "credentials",
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default = user_input.get(
                            CONF_USERNAME, DEFAULT_USERNAME
                        )
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default = user_input.get(
                            CONF_PASSWORD, ""
                        )
                    ): str,
                    vol.Optional(
                        CONF_SSL,
                        default = user_input.get(
                            CONF_SSL, DEFAULT_SSL
                        )
                    ): bool,
                }
            ),
            errors = errors
        )


    # Step #2.2 (optional) - complete device setup
    async def async_step_device(self, user_input : dict[str, Any] | None = None, errors : dict[str, str] = dict()) -> FlowResult:
        """Step to completely setup the device"""

        if user_input:
            self._input.update(user_input)
            self._simple = False
            check = await self._async_check_connection(user_input)
            if check != RESULT_SUCCESS:
                errors["base"] = check

            if not errors:
                await self.async_set_unique_id(self._unique_id)
                return await self.async_step_operation_mode()
                
        if not user_input:
            user_input = self._input.copy()

        return self.async_show_form(
            step_id = "device",
            data_schema = vol.Schema (
                {
                    vol.Required(
                        CONF_USERNAME,
                        default = user_input.get(
                            CONF_USERNAME, DEFAULT_USERNAME
                        )
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default = user_input.get(
                            CONF_PASSWORD, ""
                        )
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
                }
            ),
            errors = errors
        )


    # Step #3 - operation mode
    async def async_step_operation_mode(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Step to select operation mode"""

        if not user_input:
            user_input = dict()
            return self.async_show_form(
                step_id = "operation_mode",
                data_schema = vol.Schema(
                    {
                        vol.Required(
                            CONF_ENABLE_MONITOR,
                            default = DEFAULT_ENABLE_MONITOR,
                        ): bool,
                        vol.Required(
                            CONF_ENABLE_CONTROL,
                            default = DEFAULT_ENABLE_CONTROL,
                        ): bool,
                    }
                ),
            )

        self._input[CONF_ENABLE_MONITOR] = user_input[CONF_ENABLE_MONITOR]
        self._input[CONF_ENABLE_CONTROL] = user_input[CONF_ENABLE_CONTROL]

        if self._input[CONF_ENABLE_MONITOR]:
            return await self.async_step_interfaces()
        if self._input[CONF_ENABLE_CONTROL]:
            return self.async_create_entry(
            title = self._host,
            data = self._input,
        )


    # Step #4 (optional if monitoring is enabled) - network interfaces to monitor
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

        self._options = user_input

        return await self.async_step_name()


    # Step #Last - select device name
    async def async_step_name(self, user_input : dict[str, Any] | None = None) -> FlowResult:
        """Name the device step"""

        if not user_input:
            user_input = dict()
            return self.async_show_form(
                step_id = "name",
                data_schema = vol.Schema(
                    {
                        vol.Optional(
                            CONF_NAME,
                            default = user_input.get(
                                CONF_NAME, ""
                            )
                        ): str,
                    }
                ),
            )

        self._input.update(user_input)

        return self.async_create_entry(
            title = self._host,
            data = self._input,
            options = self._options,
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


