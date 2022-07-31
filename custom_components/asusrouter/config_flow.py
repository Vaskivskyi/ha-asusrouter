"""AsusRouter config flow."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

import socket
from typing import Any

import voluptuous as vol
from asusrouter import (
    AsusRouterConnectionError,
    AsusRouterLoginBlockError,
    AsusRouterLoginError,
)
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DATA_BITS,
    DATA_BYTES,
    DATA_GIGABITS,
    DATA_GIGABYTES,
    DATA_KILOBITS,
    DATA_KILOBYTES,
    DATA_MEGABITS,
    DATA_MEGABYTES,
    DATA_RATE_BITS_PER_SECOND,
    DATA_RATE_BYTES_PER_SECOND,
    DATA_RATE_GIGABITS_PER_SECOND,
    DATA_RATE_GIGABYTES_PER_SECOND,
    DATA_RATE_KILOBITS_PER_SECOND,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_RATE_MEGABITS_PER_SECOND,
    DATA_RATE_MEGABYTES_PER_SECOND,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .bridge import ARBridge
from .const import (
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_CONFIRM,
    CONF_CONSIDER_HOME,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    CONF_INTERFACES,
    CONF_UNITS_SPEED,
    CONF_UNITS_TRAFFIC,
    DEFAULT_CACHE_TIME,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_ENABLE_MONITOR,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSL,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    DEFAULT_USERNAME,
    DEFAULT_VERIFY_SSL,
    DELAULT_INTERFACES,
    DOMAIN,
    RESULT_CONNECTION_REFUSED,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_SUCCESS,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    SIMPLE_SETUP_PARAMETERS,
    STEP_TYPE_COMPLETE,
    STEP_TYPE_SIMPLE,
)


def _check_host(
    host: str,
) -> str | None:
    """Get the IP address for the hostname."""

    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def _check_errors(
    errors: dict[str, Any],
) -> bool:
    """Check for errors."""

    if (
        "base" in errors
        and errors["base"] != RESULT_SUCCESS
        and errors["base"] != str()
    ):
        return True

    return False


async def _async_get_network_interfaces(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any] = dict(),
) -> list[str]:
    """Return list of possible to monitor network interfaces."""

    api = ARBridge(hass, configs, options)

    try:
        if not api.is_connected:
            await api.async_connect()
        labels = await api.async_get_network_interfaces()
        await api.async_disconnect()
        return labels
    except Exception as ex:
        _LOGGER.warning(
            f"Cannot get available network stat sensors for {configs[CONF_HOST]}: {ex}"
        )
        return DELAULT_INTERFACES


async def _async_check_connection(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any] = dict(),
    simple: bool = False,
) -> dict[str, Any]:
    """Check connection to the device with provided configurations."""

    step_type = STEP_TYPE_COMPLETE

    configs_to_use = configs.copy()
    configs_to_use.update(options)
    if not CONF_HOST in configs_to_use:
        return {
            "errors": RESULT_ERROR,
        }
    host = configs_to_use[CONF_HOST]

    result = dict()

    if simple:
        configs_to_use.update(
            SIMPLE_SETUP_PARAMETERS["ssl"]
            if configs_to_use[CONF_SSL]
            else SIMPLE_SETUP_PARAMETERS["no_ssl"]
        )
        step_type = STEP_TYPE_SIMPLE

        _LOGGER.debug(f"Setup ({step_type}) initiated")

    api = ARBridge(hass, configs_to_use)

    try:
        await api.async_connect()
    # Credentials error
    except AsusRouterLoginError:
        _LOGGER.error(f"Error during connection to '{host}'. Wrong credentials")
        return {
            "errors": RESULT_WRONG_CREDENTIALS,
        }
    # Login blocked by the device
    except AsusRouterLoginBlockError as ex:
        _LOGGER.error(
            f"Device '{host}' has reported block for the login (to many wrong attempts were made). Please try again in {ex.timeout} seconds"
        )
        return {
            "errors": RESULT_LOGIN_BLOCKED,
        }
    # Connection refused
    except AsusRouterConnectionError as ex:
        if simple:
            _LOGGER.debug(
                f"Simplified setup failed for {host}. Switching to the complete mode. Original exception of type {type(ex)}: {ex}"
            )
        else:
            _LOGGER.error(
                f"Connection refused by {host}. Check SSL and port settings. Original exception: {ex}"
            )
        return {
            "errors": RESULT_CONNECTION_REFUSED,
        }
    # Anything else
    except Exception as ex:
        if simple:
            _LOGGER.debug(
                f"Simplified setup failed for {host}. Switching to the complete mode. Original exception of type {type(ex)}: {ex}"
            )
        else:
            _LOGGER.error(
                f"Unknown error of type '{type(ex)}' during connection to {host}: {ex}"
            )
        return {
            "errors": RESULT_UNKNOWN,
        }
    # Cleanup, so no unclosed sessions will be reported
    finally:
        await api.async_clean()

    result["unique_id"] = await api.get_serial()
    await api.async_disconnect()
    for item in configs:
        configs_to_use.pop(item)

    result["configs"] = configs_to_use

    _LOGGER.debug(f"Setup ({step_type}) successful")

    return result


def _create_form_discovery(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'discovery' step."""

    schema = {
        vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): cv.string,
    }

    return vol.Schema(schema)


def _create_form_credentials(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'credentials' step."""

    schema = {
        vol.Required(
            CONF_USERNAME, default=user_input.get(CONF_USERNAME, DEFAULT_USERNAME)
        ): cv.string,
        vol.Required(
            CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
        ): cv.string,
        vol.Optional(
            CONF_SSL, default=user_input.get(CONF_SSL, DEFAULT_SSL)
        ): cv.boolean,
    }

    return vol.Schema(schema)


def _create_form_device(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'device' step."""

    schema = {
        vol.Required(
            CONF_USERNAME, default=user_input.get(CONF_USERNAME, DEFAULT_USERNAME)
        ): cv.string,
        vol.Required(
            CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
        ): cv.string,
        vol.Optional(
            CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)
        ): cv.positive_int,
        vol.Optional(
            CONF_SSL, default=user_input.get(CONF_SSL, DEFAULT_SSL)
        ): cv.boolean,
        vol.Optional(
            CONF_VERIFY_SSL, default=user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        ): cv.boolean,
        vol.Optional(
            CONF_CERT_PATH,
            default=user_input.get(CONF_CERT_PATH, ""),
        ): cv.string,
    }

    return vol.Schema(schema)


def _create_form_operation_mode(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'operation_mode' step."""

    schema = {
        # vol.Required(
        #     CONF_ENABLE_MONITOR,
        #     default = user_input.get(
        #         CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR
        #     ),
        # ): bool,
        vol.Required(
            CONF_ENABLE_CONTROL,
            default=user_input.get(CONF_ENABLE_CONTROL, DEFAULT_ENABLE_CONTROL),
        ): cv.boolean,
    }

    return vol.Schema(schema)


def _create_form_times(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'times' step."""

    schema = {
        vol.Required(
            CONF_CACHE_TIME,
            default=user_input.get(CONF_CACHE_TIME, DEFAULT_CACHE_TIME),
        ): cv.positive_int,
        vol.Required(
            CONF_SCAN_INTERVAL,
            default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        ): cv.positive_int,
        vol.Required(
            CONF_CONSIDER_HOME,
            default=user_input.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME),
        ): cv.positive_int,
    }

    return vol.Schema(schema)


def _create_form_interfaces(
    user_input: dict[str, Any] = dict(),
    default: list[str] = list(),
) -> vol.Schema:
    """Create a form for the 'interfaces' step."""

    schema = {
        vol.Required(
            CONF_INTERFACES,
            default=default,
        ): cv.multi_select({k: k for k in user_input["interfaces"]}),
        vol.Required(
            CONF_UNITS_SPEED,
            default=user_input.get(CONF_UNITS_SPEED, DEFAULT_UNITS_SPEED),
        ): vol.In(
            {
                DATA_RATE_BITS_PER_SECOND: DATA_RATE_BITS_PER_SECOND,
                DATA_RATE_KILOBITS_PER_SECOND: DATA_RATE_KILOBITS_PER_SECOND,
                DATA_RATE_MEGABITS_PER_SECOND: DATA_RATE_MEGABITS_PER_SECOND,
                DATA_RATE_GIGABITS_PER_SECOND: DATA_RATE_GIGABITS_PER_SECOND,
                DATA_RATE_BYTES_PER_SECOND: DATA_RATE_BYTES_PER_SECOND,
                DATA_RATE_KILOBYTES_PER_SECOND: DATA_RATE_KILOBYTES_PER_SECOND,
                DATA_RATE_MEGABYTES_PER_SECOND: DATA_RATE_MEGABYTES_PER_SECOND,
                DATA_RATE_GIGABYTES_PER_SECOND: DATA_RATE_GIGABYTES_PER_SECOND,
            }
        ),
        vol.Required(
            CONF_UNITS_TRAFFIC,
            default=user_input.get(CONF_UNITS_TRAFFIC, DEFAULT_UNITS_TRAFFIC),
        ): vol.In(
            {
                DATA_BITS: DATA_BITS,
                DATA_KILOBITS: DATA_KILOBITS,
                DATA_MEGABITS: DATA_MEGABITS,
                DATA_GIGABITS: DATA_GIGABITS,
                DATA_BYTES: DATA_BYTES,
                DATA_KILOBYTES: DATA_KILOBYTES,
                DATA_MEGABYTES: DATA_MEGABYTES,
                DATA_GIGABYTES: DATA_GIGABYTES,
            }
        ),
    }

    return vol.Schema(schema)


def _create_form_name(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'name' step."""

    schema = {
        vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "")): cv.string,
    }

    return vol.Schema(schema)


def _create_form_confirmation(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the 'confirmation' step."""

    schema = {
        vol.Optional(
            CONF_CONFIRM, default=user_input.get(CONF_CONFIRM, False)
        ): cv.boolean,
    }

    return vol.Schema(schema)


class ASUSRouterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for AsusRouter."""

    VERSION = 4

    def __init__(self):
        """Initialise config flow."""

        self._configs = dict()
        self._options = dict()
        self._unique_id: str | None = None
        self._simple = False

        # Dictionary last_step: next_step
        self._steps = {
            "discovery": self.async_step_credentials,
            "credentials": self.async_step_operation_mode,
            "credentials_error": self.async_step_device,
            "device": self.async_step_operation_mode,
            "device_error": self.async_step_device,
            "operation_mode": self.async_step_times,
            "times": self.async_step_interfaces,
            "interfaces": self.async_step_name,
            "name": self.async_step_finish,
        }

    async def async_select_step(
        self,
        last_step: str | None = None,
        errors: dict[str, Any] = dict(),
    ) -> FlowResult:
        """Step selector."""

        if last_step:
            if last_step in self._steps:
                if _check_errors(errors):
                    return await self._steps[f"{last_step}_error"](errors=errors)
                else:
                    return await self._steps[last_step]()
            else:
                raise ValueError(f"Unknown value of last_step: {last_step}")
        else:
            raise ValueError("Step name was not provided")

    ### USER SETUP -->

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Flow initiated by user."""

        return await self.async_step_discovery(user_input)

    # Step #1 - discover the device
    async def async_step_discovery(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Device discovery step."""

        step_id = "discovery"

        errors = dict()

        if user_input:
            # Check if host can be resolved
            ip = await self.hass.async_add_executor_job(
                _check_host, user_input[CONF_HOST]
            )
            if not ip:
                errors["base"] = "cannot_resolve_host"

            if not errors:
                self._configs.update(user_input)
                return await self.async_select_step(step_id, errors)

        if not user_input:
            user_input = dict()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_discovery(user_input),
            errors=errors,
        )

    # Step #2 - credentials and SSL (simplified setup)
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Credentials step."""

        step_id = "credentials"

        errors = dict()

        if user_input:
            self._options.update(user_input)
            result = await _async_check_connection(
                self.hass, self._configs, self._options, simple=True
            )
            if "errors" in result:
                errors["base"] = result["errors"]
                if (
                    errors["base"] != RESULT_WRONG_CREDENTIALS
                    and errors["base"] != RESULT_LOGIN_BLOCKED
                ):
                    return await self.async_select_step(step_id, errors)
            else:
                self._options.update(result["configs"])
                await self.async_set_unique_id(result["unique_id"])
                return await self.async_select_step(step_id, errors)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_credentials(user_input),
            errors=errors,
        )

    # Step #2b (optional) - complete device setup
    async def async_step_device(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] = dict(),
    ) -> FlowResult:
        """Step to completely setup the device."""

        step_id = "device"

        if user_input:
            self._options.update(user_input)
            result = await _async_check_connection(
                self.hass, self._configs, self._options
            )
            if "errors" in result:
                errors["base"] = result["errors"]
            else:
                self._options.update(result["configs"])
                await self.async_set_unique_id(result["unique_id"])
                return await self.async_select_step(step_id, errors)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_device(user_input),
            errors=errors,
        )

    # Step #3 - operation mode
    async def async_step_operation_mode(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select operation mode."""

        step_id = "operation_mode"

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation_mode(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step #4 - times
    async def async_step_times(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select times."""

        step_id = "times"

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_times(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step #5 (optional if monitoring is enabled) - network interfaces to monitor
    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select interfaces for traffic monitoring."""

        step_id = "interfaces"

        if self._options.get(CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR):
            if not user_input:
                user_input = self._options.copy()
                user_input["interfaces"] = await _async_get_network_interfaces(
                    self.hass, self._configs, self._options
                )
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=_create_form_interfaces(user_input),
                )

            self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step #6 - select device name
    async def async_step_name(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Name the device step."""

        step_id = "name"

        if not user_input:
            user_input = dict()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_name(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step Finish
    async def async_step_finish(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Finish setup."""

        return self.async_create_entry(
            title=self._configs[CONF_HOST],
            data=self._configs,
            options=self._options,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for AsusRouter."""

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

        self._selection = dict()
        self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._host: str = self._configs[CONF_HOST]
        self._options: dict[str, Any] = self.config_entry.options.copy()

        # Dictionary last_step: next_step
        self._steps = {
            "options": self.async_step_device,
            "device": self.async_step_operation_mode,
            "operation_mode": self.async_step_times,
            "times": self.async_step_interfaces,
            "interfaces": self.async_step_confirmation,
            "confirmation": self.async_step_finish,
        }

    async def async_select_step(
        self,
        last_step: str | None = None,
        errors: dict[str, Any] = dict(),
    ) -> FlowResult:
        """Step selector."""

        if last_step:
            if last_step in self._steps:
                if _check_errors(errors):
                    return await self._steps[f"{last_step}_error"](errors=errors)
                else:
                    return await self._steps[last_step]()
            else:
                raise ValueError(f"Unknown value of last_step: {last_step}")
        else:
            raise ValueError("Step name was not provided")

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Options flow."""

        return await self.async_step_options(user_input)

    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        step_id = "options"

        if user_input:
            self._selection.update(user_input)
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._selection.copy()

        schema_dict = dict()
        for el in self._steps:
            if el != step_id and el != "confirmation":
                schema_dict.update({vol.Optional(el, default=False): bool})

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        step_id = "device"

        errors = dict()

        if not step_id in self._selection or self._selection[step_id] == False:
            return await self.async_select_step(step_id)

        if user_input:
            self._options.update(user_input)
            result = await _async_check_connection(
                self.hass, self._configs, self._options
            )
            if "errors" in result:
                errors["base"] = result["errors"]
            else:
                self._options.update(result["configs"])
                return await self.async_select_step(step_id, errors)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_device(user_input),
            errors=errors,
        )

    async def async_step_operation_mode(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        step_id = "operation_mode"

        if not step_id in self._selection or self._selection[step_id] == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation_mode(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_times(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select times."""

        step_id = "times"

        if not step_id in self._selection or self._selection[step_id] == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_times(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        step_id = "interfaces"

        if not step_id in self._selection or self._selection[step_id] == False:
            return await self.async_select_step(step_id)

        if self._options.get(CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR):
            if not user_input:
                user_input = self._options.copy()
                selected = user_input["interfaces"].copy()
                interfaces = await _async_get_network_interfaces(
                    self.hass, self._configs, self._options
                )
                # If interface was tracked, but cannot be found now, still add it
                for interface in interfaces:
                    if not interface in user_input["interfaces"]:
                        user_input["interfaces"].append(interface)
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=_create_form_interfaces(user_input, default=selected),
                )

            self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_confirmation(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to confirm changes."""

        step_id = "confirmation"

        errors = dict()

        if user_input:
            if CONF_CONFIRM in user_input and user_input[CONF_CONFIRM] == True:
                return await self.async_select_step(step_id)
            else:
                errors["base"] = "not_confirmed"

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_confirmation(user_input),
            errors=errors,
        )

    # Step Finish
    async def async_step_finish(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Finish setup."""

        return self.async_create_entry(
            title=self.config_entry.title,
            data=self._options,
        )
