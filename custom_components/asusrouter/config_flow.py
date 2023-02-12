"""AsusRouter config flow module."""

from __future__ import annotations

import logging
import socket
from typing import Any

from asusrouter import (
    AsusRouterConnectionError,
    AsusRouterLoginBlockError,
    AsusRouterLoginError,
)
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
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

from . import helpers
from .bridge import ARBridge
from .const import (
    BASE,
    CONF_CACHE_TIME,
    CONF_CONSIDER_HOME,
    CONF_DEFAULT_CACHE_TIME,
    CONF_DEFAULT_CONSIDER_HOME,
    CONF_DEFAULT_ENABLE_CONTROL,
    CONF_DEFAULT_EVENT,
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_DEFAULT_INTERFACES,
    CONF_DEFAULT_INTERVALS,
    CONF_DEFAULT_LATEST_CONNECTED,
    CONF_DEFAULT_MODE,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_SCAN_INTERVAL,
    CONF_DEFAULT_SPLIT_INTERVALS,
    CONF_DEFAULT_SSL,
    CONF_DEFAULT_TRACK_DEVICES,
    CONF_DEFAULT_UNITS_SPEED,
    CONF_DEFAULT_UNITS_TRAFFIC,
    CONF_DEFAULT_USERNAME,
    CONF_ENABLE_CONTROL,
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
    CONFIGS,
    DOMAIN,
    ERRORS,
    FIRMWARE,
    INTERFACES,
    METHOD,
    NEXT,
    RESULT_CANNOT_RESOLVE,
    RESULT_CONNECTION_REFUSED,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_SUCCESS,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    ROUTER,
    STEP_CREDENTIALS,
    STEP_EVENTS,
    STEP_FIND,
    STEP_FINISH,
    STEP_INTERFACES,
    STEP_INTERVALS,
    STEP_NAME,
    STEP_OPERATION,
    STEP_OPTIONS,
    STEP_SECURITY,
    UNIQUE_ID,
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
    errors: dict[str, Any] | None = None,
) -> bool:
    """Check for errors."""

    if errors is None:
        return False

    if BASE in errors and errors[BASE] != RESULT_SUCCESS and errors[BASE] != "":
        return True

    return False


async def _async_get_network_interfaces(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any],
) -> list[str]:
    """Return list of possible to monitor network interfaces."""

    bridge = ARBridge(hass, configs, options)

    try:
        if not bridge.connected:
            await bridge.async_connect()
        labels = helpers.list_from_dict(await bridge.api.async_get_network())
        await bridge.async_disconnect()
        _LOGGER.debug("Found network interfaces: %s", labels)
        return labels
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.warning(
            "Cannot get available network interfaces for %s: %s", configs[CONF_HOST], ex
        )
        return CONF_DEFAULT_INTERFACES


async def _async_check_connection(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check connection to the device with provided configurations."""

    configs_to_use = configs.copy()
    if options:
        configs_to_use.update(options)
    if CONF_HOST not in configs_to_use:
        return {
            ERRORS: RESULT_ERROR,
        }
    host = configs_to_use[CONF_HOST]

    result = {}
    _LOGGER.debug("Setup initiated")

    # Initialize bridge
    bridge = ARBridge(hass, configs_to_use)

    # Connect
    try:
        await bridge.async_connect()
    # Credentials error
    except AsusRouterLoginError:
        _LOGGER.error("Error during connection to '%s'. Wrong credentials", host)
        return {
            ERRORS: RESULT_WRONG_CREDENTIALS,
        }
    # Login blocked by the device
    except AsusRouterLoginBlockError as ex:
        _LOGGER.error(
            "Device '%s' has reported block for the login (to many wrong attempts were made). \
                Please try again in %s seconds",
            host,
            ex.timeout,
        )
        return {
            ERRORS: RESULT_LOGIN_BLOCKED,
        }
    # Connection refused
    except AsusRouterConnectionError as ex:
        _LOGGER.error(
            "Connection refused by `%s`. Check SSL and port settings. Original exception: %s",
            host,
            ex,
        )
        return {
            ERRORS: RESULT_CONNECTION_REFUSED,
        }
    # Anything else
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.error(
            "Unknown error of type '%s' during connection to `%s`: %s",
            type(ex),
            host,
            ex,
        )
        return {
            ERRORS: RESULT_UNKNOWN,
        }
    # Cleanup, so no unclosed sessions will be reported
    finally:
        await bridge.async_clean()

    # Serial number of the device is the best unique_id
    # API provides it all the time for all the devices.
    # MAC as an alternative might not be used / found on some
    # older devices and some Merlin-builds of FW
    result[UNIQUE_ID] = bridge.identity.serial
    await bridge.async_disconnect()
    for item in configs:
        configs_to_use.pop(item)

    result[CONFIGS] = configs_to_use

    _LOGGER.debug("Setup successful")

    return result


async def _async_process_step(
    steps: dict[str, dict[str, Any]],
    step: str | None = None,
    errors: dict[str, Any] | None = None,
    redirect: bool = False,
) -> FlowResult:
    """Universal step selector.

    When the name of the last step is provided, the next step is initialized.
    On errors the same step will repeat.
    """

    if step and step in steps:
        # Method description
        description = steps[step]
        # On errors or redirect, run the step method
        if _check_errors(errors) or redirect:
            if METHOD in description:
                return await description[METHOD]()
            raise ValueError(f"Step `{step}` is not properly defined")
        # If the next step is defined, move to it
        if NEXT in description and description[NEXT]:
            return await _async_process_step(steps, description[NEXT], redirect=True)
        raise ValueError(f"Step `{step}` is not properly defined")
    raise ValueError(f"Step `{step}` cannot be found")


# FORMS ->


def _create_form_find(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the 'find' step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): cv.string,
    }

    return vol.Schema(schema)


def _create_form_credentials(
    user_input: dict[str, Any] | None = None,
    mode: str = CONF_DEFAULT_MODE,
) -> vol.Schema:
    """Create a form for the 'credentials' step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Required(
            CONF_USERNAME, default=user_input.get(CONF_USERNAME, CONF_DEFAULT_USERNAME)
        ): cv.string,
        vol.Required(
            CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
        ): cv.string,
        vol.Optional(
            CONF_PORT, default=user_input.get(CONF_PORT, CONF_DEFAULT_PORT)
        ): cv.positive_int,
        vol.Optional(
            CONF_SSL, default=user_input.get(CONF_SSL, CONF_DEFAULT_SSL)
        ): cv.boolean,
        vol.Required(CONF_MODE, default=user_input.get(CONF_MODE, mode)): vol.In(
            {mode: CONF_LABELS_MODE.get(mode, mode) for mode in CONF_VALUES_MODE}
        ),
    }

    return vol.Schema(schema)


def _create_form_operation(
    user_input: dict[str, Any] | None = None,
    mode: str = CONF_DEFAULT_MODE,
) -> vol.Schema:
    """Create a form for the 'operation' step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Required(
            CONF_ENABLE_CONTROL,
            default=user_input.get(CONF_ENABLE_CONTROL, CONF_DEFAULT_ENABLE_CONTROL),
        ): cv.boolean,
        vol.Required(
            CONF_SPLIT_INTERVALS,
            default=user_input.get(CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS),
        ): cv.boolean,
    }

    # Only in router mode
    if mode == ROUTER:
        schema.update(
            {
                vol.Required(
                    CONF_TRACK_DEVICES,
                    default=user_input.get(
                        CONF_TRACK_DEVICES, CONF_DEFAULT_TRACK_DEVICES
                    ),
                ): cv.boolean,
                vol.Required(
                    CONF_LATEST_CONNECTED,
                    default=user_input.get(
                        CONF_LATEST_CONNECTED, CONF_DEFAULT_LATEST_CONNECTED
                    ),
                ): cv.positive_int,
            }
        )

    return vol.Schema(schema)


def _create_form_intervals(
    user_input: dict[str, Any] | None = None,
    mode: str = ROUTER,
) -> vol.Schema:
    """Create a form for the 'intervals' step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Required(
            CONF_CACHE_TIME,
            default=user_input.get(CONF_CACHE_TIME, CONF_DEFAULT_CACHE_TIME),
        ): cv.positive_int,
    }

    # Only in router mode
    if mode == ROUTER:
        schema.update(
            {
                vol.Required(
                    CONF_INTERVAL_DEVICES,
                    default=user_input.get(
                        CONF_INTERVAL_DEVICES, CONF_DEFAULT_SCAN_INTERVAL
                    ),
                ): cv.positive_int,
            }
        )
        if user_input.get(CONF_TRACK_DEVICES, CONF_DEFAULT_TRACK_DEVICES):
            schema.update(
                {
                    vol.Required(
                        CONF_CONSIDER_HOME,
                        default=user_input.get(
                            CONF_CONSIDER_HOME, CONF_DEFAULT_CONSIDER_HOME
                        ),
                    ): cv.positive_int,
                }
            )

    split = user_input.get(CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS)
    conf_scan_interval = user_input.get(CONF_SCAN_INTERVAL, CONF_DEFAULT_SCAN_INTERVAL)

    if split is False:
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
                        CONF_DEFAULT_INTERVALS[CONF_INTERVAL + FIRMWARE],
                    ),
                ): cv.positive_int,
            }
        )
    elif split is True:
        schema.update(
            {
                vol.Required(
                    conf,
                    default=user_input.get(
                        conf, CONF_DEFAULT_INTERVALS.get(conf, conf_scan_interval)
                    ),
                ): cv.positive_int
                for conf in CONF_INTERVALS
            }
        )

    return vol.Schema(schema)


def _create_form_interfaces(
    user_input: dict[str, Any] | None = None,
    default: list[str] | None = None,
) -> vol.Schema:
    """Create a form for the 'interfaces' step."""

    if not user_input:
        user_input = {}

    if not default:
        default = []

    schema = {
        vol.Optional(
            CONF_INTERFACES,
            default=default,
        ): cv.multi_select(
            {
                interface: CONF_LABELS_INTERFACES.get(interface, interface)
                for interface in user_input[INTERFACES]
            }
        ),
        vol.Required(
            CONF_UNITS_SPEED,
            default=user_input.get(CONF_UNITS_SPEED, CONF_DEFAULT_UNITS_SPEED),
        ): vol.In({datarate: datarate for datarate in CONF_VALUES_DATARATE}),
        vol.Required(
            CONF_UNITS_TRAFFIC,
            default=user_input.get(CONF_UNITS_TRAFFIC, CONF_DEFAULT_UNITS_TRAFFIC),
        ): vol.In({data: data for data in CONF_VALUES_DATA}),
    }

    return vol.Schema(schema)


def _create_form_events(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the `events` step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Optional(
            event,
            default=user_input.get(event, default_state),
        ): cv.boolean
        for event, default_state in CONF_DEFAULT_EVENT.items()
    }

    return vol.Schema(schema)


def _create_form_security(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the `security` step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Required(
            CONF_HIDE_PASSWORDS,
            default=user_input.get(CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS),
        ): cv.boolean,
    }

    return vol.Schema(schema)


def _create_form_name(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for the 'name' step."""

    if not user_input:
        user_input = {}

    schema = {
        vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "")): cv.string,
    }

    return vol.Schema(schema)


# <- FORMS


class ARFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for AsusRouter."""

    VERSION = 4

    def __init__(self) -> None:
        """Initialise config flow."""

        self._configs: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
        self._unique_id: str | None = None
        self._mode = CONF_DEFAULT_MODE

        # Steps description
        self._steps: dict[str, dict[str, Any]] = {
            STEP_FIND: {METHOD: self.async_step_find, NEXT: STEP_CREDENTIALS},
            STEP_CREDENTIALS: {
                METHOD: self.async_step_credentials,
                NEXT: STEP_OPERATION,
            },
            STEP_OPERATION: {
                METHOD: self.async_step_operation,
                NEXT: STEP_INTERVALS,
            },
            STEP_INTERVALS: {METHOD: self.async_step_intervals, NEXT: STEP_INTERFACES},
            STEP_INTERFACES: {METHOD: self.async_step_interfaces, NEXT: STEP_SECURITY},
            STEP_SECURITY: {METHOD: self.async_step_security, NEXT: STEP_NAME},
            STEP_NAME: {METHOD: self.async_step_name, NEXT: STEP_FINISH},
            STEP_FINISH: {METHOD: self.async_step_finish},
        }

    # User setup

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Flow initiated by user."""

        return await self.async_step_find(user_input)

    # Step #1 - find the device
    async def async_step_find(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Find the device step."""

        step_id = STEP_FIND

        errors = {}

        if user_input:
            # Check if host can be resolved
            ip = await self.hass.async_add_executor_job(
                _check_host, user_input[CONF_HOST]
            )
            if not ip:
                errors[BASE] = RESULT_CANNOT_RESOLVE

            if not errors:
                # Save host to configs
                self._configs.update(user_input)
                # Proceed to the next step
                return await _async_process_step(self._steps, step_id, errors)

        if not user_input:
            user_input = {}

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_find(user_input),
            errors=errors,
        )

    # Step #2 - credentials, SSL and operation mode
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Credentials step."""

        step_id = STEP_CREDENTIALS

        errors = {}

        if user_input:
            # Save the operation mode
            self._mode = user_input.get(CONF_MODE, CONF_DEFAULT_MODE)
            # Check credentials and connection
            result = await _async_check_connection(self.hass, self._configs, user_input)
            # Show errors if any
            if ERRORS in result:
                errors[BASE] = result[ERRORS]
            else:
                # Save the checked settings to the options
                self._options.update(result[CONFIGS])
                # Set unique ID obtained from the device during the check
                await self.async_set_unique_id(result[UNIQUE_ID])
                # Proceed to the next step
                return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_credentials(user_input),
            errors=errors,
        )

    # Step #3 - operation settings
    async def async_step_operation(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select operation settings."""

        step_id = STEP_OPERATION

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation(user_input, self._mode),
            )

        self._options.update(user_input)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

    # Step #4 - time intervals
    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select intervals."""

        step_id = STEP_INTERVALS

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_intervals(user_input, self._mode),
            )

        self._options.update(user_input)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

    # Step #5 - network interfaces to monitor
    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select interfaces for traffic monitoring."""

        step_id = STEP_INTERFACES

        if not user_input:
            user_input = self._options.copy()
            user_input[INTERFACES] = await _async_get_network_interfaces(
                self.hass, self._configs, self._options
            )
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_interfaces(user_input),
            )

        self._options.update(user_input)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

    # Step #6 - security options
    async def async_step_security(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Security step."""

        step_id = STEP_SECURITY

        if not user_input:
            user_input = {}
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_security(user_input),
            )

        self._options.update(user_input)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

    # Step #7 - select device name
    async def async_step_name(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Name the device step."""

        step_id = STEP_NAME

        if not user_input:
            user_input = {}
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_name(user_input),
            )

        self._options.update(user_input)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

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
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow."""

        return AROptionsFlowHandler(config_entry)


class AROptionsFlowHandler(OptionsFlow):
    """Options flow for AsusRouter."""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

        self._selection: dict[str, Any] = {}
        self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._host: str = self._configs[CONF_HOST]
        self._options: dict[str, Any] = self.config_entry.options.copy()
        self._mode = self._options.get(CONF_MODE, CONF_DEFAULT_MODE)

        # Steps description
        self._steps: dict[str, dict[str, Any]] = {
            STEP_OPTIONS: {METHOD: self.async_step_options, NEXT: STEP_CREDENTIALS},
            STEP_CREDENTIALS: {
                METHOD: self.async_step_credentials,
                NEXT: STEP_OPERATION,
            },
            STEP_OPERATION: {
                METHOD: self.async_step_operation,
                NEXT: STEP_INTERVALS,
            },
            STEP_INTERVALS: {METHOD: self.async_step_intervals, NEXT: STEP_INTERFACES},
            STEP_INTERFACES: {METHOD: self.async_step_interfaces, NEXT: STEP_EVENTS},
            STEP_EVENTS: {METHOD: self.async_step_events, NEXT: STEP_SECURITY},
            STEP_SECURITY: {METHOD: self.async_step_security, NEXT: STEP_FINISH},
            STEP_FINISH: {METHOD: self.async_step_finish},
        }

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

        step_id = STEP_OPTIONS

        if user_input:
            self._selection.update(user_input)
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._selection.copy()

        schema_dict = {}
        for step in self._steps:
            if step not in (step_id, STEP_FINISH):
                schema_dict.update({vol.Optional(step, default=False): bool})

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select credentials."""

        step_id = STEP_CREDENTIALS

        errors = {}

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if user_input:
            self._options.update(user_input)
            self._mode = user_input.get(CONF_MODE, CONF_DEFAULT_MODE)
            result = await _async_check_connection(
                self.hass, self._configs, self._options
            )
            if ERRORS in result:
                errors[BASE] = result[ERRORS]
            else:
                self._options.update(result[CONFIGS])
                return await _async_process_step(self._steps, step_id, errors)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_credentials(user_input, self._mode),
            errors=errors,
        )

    async def async_step_operation(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select operation mode."""

        step_id = STEP_OPERATION

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation(user_input, self._mode),
            )

        self._options.update(user_input)

        return await _async_process_step(self._steps, step_id)

    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select intervals."""

        step_id = STEP_INTERVALS

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_intervals(user_input, self._mode),
            )

        self._options.update(user_input)

        return await _async_process_step(self._steps, step_id)

    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select network interfaces."""

        step_id = STEP_INTERFACES

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()
            selected = user_input[INTERFACES].copy()
            interfaces = await _async_get_network_interfaces(
                self.hass, self._configs, self._options
            )
            # If interface was tracked, but cannot be found now, still add it
            for interface in interfaces:
                if interface not in user_input[INTERFACES]:
                    user_input[INTERFACES].append(interface)
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_interfaces(user_input, default=selected),
            )

        self._options.update(user_input)

        return await _async_process_step(self._steps, step_id)

    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Events step."""

        step_id = STEP_EVENTS

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_events(user_input),
            )

        self._options.update(user_input)

        return await _async_process_step(self._steps, step_id)

    async def async_step_security(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Security step."""

        step_id = STEP_SECURITY

        if self._selection.get(step_id, False) is False:
            return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_security(user_input),
            )

        self._options.update(user_input)

        return await _async_process_step(self._steps, step_id)

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
