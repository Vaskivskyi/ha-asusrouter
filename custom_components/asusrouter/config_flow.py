"""AsusRouter config flow."""

from __future__ import annotations

import logging
import socket
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from asusrouter import (
    AsusRouterConnectionError,
    AsusRouterLoginBlockError,
    AsusRouterLoginError,
)

from . import helpers
from .bridge import ARBridge
from .const import (
    ACCESS_POINT,
    CONF_CACHE_TIME,
    CONF_CONSIDER_HOME,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    CONF_HIDE_PASSWORDS,
    CONF_INTERFACES,
    CONF_INTERVAL,
    CONF_INTERVAL_DEVICES,
    CONF_INTERVALS,
    CONF_LABELS_INTERFACES,
    CONF_LABELS_MODE,
    CONF_LATEST_CONNECTED,
    CONF_MODE,
    CONF_SPLIT_INTERVALS,
    CONF_TRACK_DEVICES,
    CONF_UNITS_SPEED,
    CONF_UNITS_TRAFFIC,
    CONF_VALUES_DATA,
    CONF_VALUES_DATARATE,
    CONF_VALUES_MODE,
    DEFAULT_CACHE_TIME,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_ENABLE_MONITOR,
    DEFAULT_EVENT,
    DEFAULT_HIDE_PASSWORDS,
    DEFAULT_INTERVALS,
    DEFAULT_LATEST_CONNECTED,
    DEFAULT_MODE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SPLIT_INTERVALS,
    DEFAULT_SSL,
    DEFAULT_TRACK_DEVICES,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    DEFAULT_USERNAME,
    DELAULT_INTERFACES,
    DOMAIN,
    FIRMWARE,
    RESULT_CONNECTION_REFUSED,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_SUCCESS,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    ROUTER,
)

_LOGGER = logging.getLogger(__name__)


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

    bridge = ARBridge(hass, configs, options)

    try:
        if not bridge.is_connected:
            await bridge.async_connect()
        labels = helpers.list_from_dict(await bridge.api.async_get_network())
        await bridge.async_disconnect()
        _LOGGER.debug(labels)
        return labels
    except Exception as ex:
        _LOGGER.warning(
            f"Cannot get available network interfaces for {configs[CONF_HOST]}: {ex}"
        )
        return DELAULT_INTERFACES


async def _async_check_connection(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any] = dict(),
) -> dict[str, Any]:
    """Check connection to the device with provided configurations."""

    configs_to_use = configs.copy()
    configs_to_use.update(options)
    if not CONF_HOST in configs_to_use:
        return {
            "errors": RESULT_ERROR,
        }
    host = configs_to_use[CONF_HOST]

    result = dict()

    _LOGGER.debug(f"Setup initiated")

    bridge = ARBridge(hass, configs_to_use)

    try:
        await bridge.async_connect()
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
        _LOGGER.error(
            f"Connection refused by {host}. Check SSL and port settings. Original exception: {ex}"
        )
        return {
            "errors": RESULT_CONNECTION_REFUSED,
        }
    # Anything else
    except Exception as ex:
        _LOGGER.error(
            f"Unknown error of type '{type(ex)}' during connection to {host}: {ex}"
        )
        return {
            "errors": RESULT_UNKNOWN,
        }
    # Cleanup, so no unclosed sessions will be reported
    finally:
        await bridge.async_clean()

    result["unique_id"] = bridge.identity.serial
    await bridge.async_disconnect()
    for item in configs:
        configs_to_use.pop(item)

    result["configs"] = configs_to_use

    _LOGGER.debug(f"Setup successful")

    return result


### FORMS ->


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
    mode: str = ROUTER,
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
            CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)
        ): cv.positive_int,
        vol.Optional(
            CONF_SSL, default=user_input.get(CONF_SSL, DEFAULT_SSL)
        ): cv.boolean,
        vol.Required(CONF_MODE, default=user_input.get(CONF_MODE, mode)): vol.In(
            {mode: CONF_LABELS_MODE.get(mode, mode) for mode in CONF_VALUES_MODE}
        ),
    }

    return vol.Schema(schema)


def _create_form_operation_mode(
    user_input: dict[str, Any] = dict(),
    mode: str = ROUTER,
) -> vol.Schema:
    """Create a form for the 'operation_mode' step."""

    schema = {
        vol.Required(
            CONF_ENABLE_CONTROL,
            default=user_input.get(CONF_ENABLE_CONTROL, DEFAULT_ENABLE_CONTROL),
        ): cv.boolean,
        vol.Required(
            CONF_SPLIT_INTERVALS,
            default=user_input.get(CONF_SPLIT_INTERVALS, DEFAULT_SPLIT_INTERVALS),
        ): cv.boolean,
    }

    # Only in router mode
    if mode == ROUTER:
        schema.update(
            {
                vol.Required(
                    CONF_TRACK_DEVICES,
                    default=user_input.get(CONF_TRACK_DEVICES, DEFAULT_TRACK_DEVICES),
                ): cv.boolean,
                vol.Required(
                    CONF_LATEST_CONNECTED,
                    default=user_input.get(
                        CONF_LATEST_CONNECTED, DEFAULT_LATEST_CONNECTED
                    ),
                ): cv.positive_int,
            }
        )

    return vol.Schema(schema)


def _create_form_intervals(
    user_input: dict[str, Any] = dict(),
    mode: str = ROUTER,
) -> vol.Schema:
    """Create a form for the 'intervals' step."""

    schema = {
        vol.Required(
            CONF_CACHE_TIME,
            default=user_input.get(CONF_CACHE_TIME, DEFAULT_CACHE_TIME),
        ): cv.positive_int,
    }

    # Only in router mode
    if mode == ROUTER:
        schema.update(
            {
                vol.Required(
                    CONF_INTERVAL_DEVICES,
                    default=user_input.get(
                        CONF_INTERVAL_DEVICES, DEFAULT_SCAN_INTERVAL
                    ),
                ): cv.positive_int,
            }
        )
        if user_input.get(CONF_TRACK_DEVICES, DEFAULT_TRACK_DEVICES):
            schema.update(
                {
                    vol.Required(
                        CONF_CONSIDER_HOME,
                        default=user_input.get(
                            CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME
                        ),
                    ): cv.positive_int,
                }
            )

    split = user_input.get(CONF_SPLIT_INTERVALS, DEFAULT_SPLIT_INTERVALS)
    conf_scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    if split == False:
        schema.update(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=conf_scan_interval,
                ): cv.positive_int,
                vol.Optional(
                    CONF_INTERVAL + FIRMWARE,
                    default=user_input.get(
                        CONF_INTERVAL + FIRMWARE,
                        DEFAULT_INTERVALS[CONF_INTERVAL + FIRMWARE],
                    ),
                ): cv.positive_int,
            }
        )
    elif split == True:
        schema.update(
            {
                vol.Required(
                    conf,
                    default=user_input.get(
                        conf, DEFAULT_INTERVALS.get(conf, conf_scan_interval)
                    ),
                ): cv.positive_int
                for conf in CONF_INTERVALS
            }
        )

    return vol.Schema(schema)


def _create_form_interfaces(
    user_input: dict[str, Any] = dict(),
    default: list[str] = list(),
) -> vol.Schema:
    """Create a form for the 'interfaces' step."""

    schema = {
        vol.Optional(CONF_INTERFACES, default=default,): cv.multi_select(
            {
                interface: CONF_LABELS_INTERFACES.get(interface, interface)
                for interface in user_input["interfaces"]
            }
        ),
        vol.Required(
            CONF_UNITS_SPEED,
            default=user_input.get(CONF_UNITS_SPEED, DEFAULT_UNITS_SPEED),
        ): vol.In({datarate: datarate for datarate in CONF_VALUES_DATARATE}),
        vol.Required(
            CONF_UNITS_TRAFFIC,
            default=user_input.get(CONF_UNITS_TRAFFIC, DEFAULT_UNITS_TRAFFIC),
        ): vol.In({data: data for data in CONF_VALUES_DATA}),
    }

    return vol.Schema(schema)


def _create_form_events(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the `events` step."""

    schema = {
        vol.Optional(
            conf,
            default=user_input.get(conf, DEFAULT_EVENT[conf]),
        ): cv.boolean
        for conf in DEFAULT_EVENT
    }

    return vol.Schema(schema)


def _create_form_security(
    user_input: dict[str, Any] = dict(),
) -> vol.Schema:
    """Create a form for the `security` step."""

    schema = {
        vol.Required(
            CONF_HIDE_PASSWORDS,
            default=user_input.get(CONF_HIDE_PASSWORDS, DEFAULT_HIDE_PASSWORDS),
        ): cv.boolean,
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


### <- FORMS


class ASUSRouterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for AsusRouter."""

    VERSION = 4

    def __init__(self):
        """Initialise config flow."""

        self._configs = dict()
        self._options = dict()
        self._unique_id: str | None = None
        self._simple = False
        self._mode = DEFAULT_MODE

        # Dictionary last_step: next_step
        self._steps = {
            "discovery": self.async_step_credentials,
            "credentials": self.async_step_operation_mode,
            "credentials_error": self.async_step_credentials,
            "operation_mode": self.async_step_intervals,
            "intervals": self.async_step_interfaces,
            "interfaces": self.async_step_security,
            "security": self.async_step_name,
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

    # Step #2 - credentials
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] = dict(),
    ) -> FlowResult:
        """Credentials step."""

        step_id = "credentials"

        if user_input:
            self._options.update(user_input)
            self._mode = user_input.get(CONF_MODE, DEFAULT_MODE)
            result = await _async_check_connection(
                self.hass, self._configs, self._options
            )
            if "errors" in result:
                errors["base"] = result["errors"]
            else:
                errors = {}
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
                data_schema=_create_form_operation_mode(user_input, self._mode),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step #4 - intervals
    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select intervals."""

        step_id = "intervals"

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_intervals(user_input, self._mode),
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

    # Step #6 - security options
    async def async_step_security(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Security step."""

        step_id = "security"

        if not user_input:
            user_input = dict()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_security(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    # Step #7 - select device name
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
        self._mode = self._options.get(CONF_MODE, DEFAULT_MODE)

        # Dictionary last_step: next_step
        self._steps = {
            "options": self.async_step_credentials,
            "credentials": self.async_step_operation_mode,
            "operation_mode": self.async_step_intervals,
            "intervals": self.async_step_interfaces,
            "interfaces": self.async_step_events,
            "events": self.async_step_security,
            "security": self.async_step_finish,
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
            if el != step_id:
                schema_dict.update({vol.Optional(el, default=False): bool})

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select credentials."""

        step_id = "credentials"

        errors = dict()

        if self._selection.get(step_id, False) == False:
            return await self.async_select_step(step_id)

        if user_input:
            self._options.update(user_input)
            self._mode = user_input.get(CONF_MODE, DEFAULT_MODE)
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
            data_schema=_create_form_credentials(user_input, self._mode),
            errors=errors,
        )

    async def async_step_operation_mode(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select operation mode."""

        step_id = "operation_mode"

        if self._selection.get(step_id, False) == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation_mode(user_input, self._mode),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select intervals."""

        step_id = "intervals"

        if self._selection.get(step_id, False) == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_intervals(user_input, self._mode),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        step_id = "interfaces"

        if self._selection.get(step_id, False) == False:
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

    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Events step."""

        step_id = "events"

        if self._selection.get(step_id, False) == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_events(user_input),
            )

        self._options.update(user_input)

        return await self.async_select_step(step_id)

    async def async_step_security(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Security step."""

        step_id = "security"

        if self._selection.get(step_id, False) == False:
            return await self.async_select_step(step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_security(user_input),
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
            title=self.config_entry.title,
            data=self._options,
        )
