"""AsusRouter config flow module."""

from __future__ import annotations

import logging
import socket
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import format_mac

from asusrouter import AsusData
from asusrouter.error import (
    AsusRouterAccessError,
    AsusRouterConnectionError,
    AsusRouterTimeoutError,
)
from asusrouter.modules.endpoint.error import AccessError
from asusrouter.modules.homeassistant import convert_to_ha_sensors_group

from .bridge import ARBridge
from .const import (
    ACCESS_POINT,
    ALL_CLIENTS,
    BASE,
    CONF_CACHE_TIME,
    CONF_CLIENT_DEVICE,
    CONF_CLIENT_FILTER,
    CONF_CLIENT_FILTER_LIST,
    CONF_CLIENTS_IN_ATTR,
    CONF_CONSIDER_HOME,
    CONF_CREATE_DEVICES,
    CONF_DEFAULT_CACHE_TIME,
    CONF_DEFAULT_CLIENT_DEVICE,
    CONF_DEFAULT_CLIENT_FILTER,
    CONF_DEFAULT_CLIENTS_IN_ATTR,
    CONF_DEFAULT_CONSIDER_HOME,
    CONF_DEFAULT_CREATE_DEVICES,
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
    CONF_DEFAULT_USERNAME,
    CONF_HIDE_PASSWORDS,
    CONF_INTERFACES,
    CONF_INTERVAL,
    CONF_INTERVAL_DEVICES,
    CONF_INTERVALS,
    CONF_LABELS_CLIENT_FILTER,
    CONF_LABELS_INTERFACES,
    CONF_LABELS_MODE,
    CONF_LATEST_CONNECTED,
    CONF_MODE,
    CONF_SPLIT_INTERVALS,
    CONF_TRACK_DEVICES,
    CONF_VALUES_MODE,
    CONFIGS,
    DOMAIN,
    ERRORS,
    FIRMWARE,
    INTERFACES,
    MEDIA_BRIDGE,
    METHOD,
    NEXT,
    RESULT_ACCESS_ERROR,
    RESULT_CANNOT_RESOLVE,
    RESULT_CONNECTION_ERROR,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_SUCCESS,
    RESULT_TIMEOUT,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
    ROUTER,
    STEP_CONNECTED_DEVICES,
    STEP_CREDENTIALS,
    STEP_EVENTS,
    STEP_FIND,
    STEP_FINISH,
    STEP_INTERFACES,
    STEP_INTERVALS,
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

    if (
        BASE in errors
        and errors[BASE] != RESULT_SUCCESS
        and errors[BASE] != ""
    ):
        return True

    return False


async def _async_get_clients(
    hass: HomeAssistant,
    configs: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    """Return list of all the known clients."""

    bridge = ARBridge(hass, configs, options)

    try:
        if not bridge.connected:
            await bridge.async_connect()
        clients = await bridge.api.async_get_data(AsusData.CLIENTS)
        await bridge.async_disconnect()

        result = {
            format_mac(mac): client.description.name
            for mac, client in clients.items()
            if client.description.name
        }
        return result
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.warning(
            "Cannot get clients for %s: %s", configs[CONF_HOST], ex
        )
        return {}


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
        labels = convert_to_ha_sensors_group(
            await bridge.api.async_get_data(AsusData.NETWORK)
        )
        await bridge.async_disconnect()
        _LOGGER.debug("Found network interfaces: %s", labels)
        return labels
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.warning(
            "Cannot get available network interfaces for %s: %s",
            configs[CONF_HOST],
            ex,
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
    # Access error
    except AsusRouterAccessError as ex:
        args = ex.args
        # Wrong credentials
        if args[1] == AccessError.CREDENTIALS:
            _LOGGER.error(
                "Error during connection to `%s`. Wrong credentials", host
            )
            return {
                ERRORS: RESULT_WRONG_CREDENTIALS,
            }
        # Try again later / too many attempts
        if args[1] == AccessError.TRY_AGAIN:
            timeout = args[2].get("timeout")
            _LOGGER.error(
                "Device `%s` has reported block for the login (to many wrong attempts were made). \
                    Please try again in `%s` seconds",
                host,
                timeout,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Reset required
        if args[1] == AccessError.RESET_REQUIRED:
            _LOGGER.error(
                "Device `%s` requires a reset. Please reset the device. You won't be able to \
                    login to the device until the reset is done.",
                host,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Captcha required
        if args[1] == AccessError.CAPTCHA:
            _LOGGER.error(
                "Device `%s` requires a captcha. Please login to the device and complete the captcha. \
                    Integration cannot proceed with the captcha request. You need either to disable \
                    captcha or login via Web UI from the HA IP address, complete it and try again. \
                    Sometimes, you can also reboot the device to fix this issue.",
                host,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Another error
        if args[1] == AccessError.ANOTHER:
            _LOGGER.error("Device `%s` has reported `another` error.", host)
            return {
                ERRORS: RESULT_ERROR,
            }
        # Unknown error
        if args[1] == AccessError.UNKNOWN:
            _LOGGER.error("Device `%s` has reported `unknown` error.", host)
            return {
                ERRORS: RESULT_UNKNOWN,
            }
        # Anything else
        _LOGGER.error(
            "Error during connection to `%s`. Original exception: %s", host, ex
        )
        return {
            ERRORS: RESULT_ACCESS_ERROR,
        }

    # Timeout error
    except AsusRouterTimeoutError as ex:
        _LOGGER.error(
            "Timeout error during connection to `%s`: Original exception: %s",
            host,
            ex,
        )
        return {
            ERRORS: RESULT_TIMEOUT,
        }

    # Connection error
    except AsusRouterConnectionError as ex:
        _LOGGER.error(
            "Connection error during connection to `%s`: Original exception: %s",
            host,
            ex,
        )
        return {
            ERRORS: RESULT_CONNECTION_ERROR,
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
            return await _async_process_step(
                steps, description[NEXT], redirect=True
            )
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
        vol.Required(
            CONF_HOST, default=user_input.get(CONF_HOST, "")
        ): cv.string,
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
            CONF_USERNAME,
            default=user_input.get(CONF_USERNAME, CONF_DEFAULT_USERNAME),
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
            CONF_MODE, default=user_input.get(CONF_MODE, mode)
        ): vol.In(
            {
                mode: CONF_LABELS_MODE.get(mode, mode)
                for mode in CONF_VALUES_MODE
            }
        ),
        vol.Required(
            CONF_SPLIT_INTERVALS,
            default=user_input.get(
                CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS
            ),
        ): cv.boolean,
    }

    return vol.Schema(schema)


def _create_form_connected_devices(
    user_input: dict[str, Any] | None = None,
    mode: str = CONF_DEFAULT_MODE,
    default: list[str] | None = None,
) -> vol.Schema:
    """Create a form for the `connected_devices` step."""

    if not user_input:
        user_input = {}

    if not default:
        default = []

    schema = {
        vol.Required(
            CONF_TRACK_DEVICES,
            default=user_input.get(
                CONF_TRACK_DEVICES, CONF_DEFAULT_TRACK_DEVICES
            ),
        ): cv.boolean,
        vol.Required(
            CONF_CLIENT_DEVICE,
            default=user_input.get(
                CONF_CLIENT_DEVICE, CONF_DEFAULT_CLIENT_DEVICE
            ),
        ): cv.boolean,
        vol.Required(
            CONF_CLIENTS_IN_ATTR,
            default=user_input.get(
                CONF_CLIENTS_IN_ATTR, CONF_DEFAULT_CLIENTS_IN_ATTR
            ),
        ): cv.boolean,
        vol.Required(
            CONF_CLIENT_FILTER,
            default=user_input.get(
                CONF_CLIENT_FILTER, CONF_DEFAULT_CLIENT_FILTER
            ),
        ): vol.In(CONF_LABELS_CLIENT_FILTER),
        vol.Optional(
            CONF_CLIENT_FILTER_LIST,
            default=default,
        ): cv.multi_select(
            dict(
                sorted(
                    user_input[ALL_CLIENTS].items(), key=lambda item: item[1]
                )
            )
        ),
        vol.Required(
            CONF_LATEST_CONNECTED,
            default=user_input.get(
                CONF_LATEST_CONNECTED, CONF_DEFAULT_LATEST_CONNECTED
            ),
        ): cv.positive_int,
        vol.Required(
            CONF_INTERVAL_DEVICES,
            default=user_input.get(
                CONF_INTERVAL_DEVICES, CONF_DEFAULT_SCAN_INTERVAL
            ),
        ): cv.positive_int,
    }

    if mode in (ACCESS_POINT, ROUTER):
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

    if mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
        schema.update(
            {
                vol.Required(
                    CONF_CREATE_DEVICES,
                    default=user_input.get(
                        CONF_CREATE_DEVICES, CONF_DEFAULT_CREATE_DEVICES
                    ),
                ): cv.boolean,
            }
        )

    return vol.Schema(schema)


def _create_form_intervals(
    user_input: dict[str, Any] | None = None,
    mode: str = CONF_DEFAULT_MODE,
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

    split = user_input.get(CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS)
    conf_scan_interval = user_input.get(
        CONF_SCAN_INTERVAL, CONF_DEFAULT_SCAN_INTERVAL
    )

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
                        conf,
                        CONF_DEFAULT_INTERVALS.get(conf, conf_scan_interval),
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
            default=user_input.get(
                CONF_HIDE_PASSWORDS, CONF_DEFAULT_HIDE_PASSWORDS
            ),
        ): cv.boolean,
    }

    return vol.Schema(schema)


# <- FORMS


class ARFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for AsusRouter."""

    VERSION = 5

    def __init__(self) -> None:
        """Initialise config flow."""

        self._configs: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
        self._unique_id: str | None = None
        self._mode = CONF_DEFAULT_MODE
        self.description_placeholders: dict[str, Any] = {}

        # Steps description
        self._steps: dict[str, dict[str, Any]] = {
            STEP_FIND: {METHOD: self.async_step_find, NEXT: STEP_CREDENTIALS},
            STEP_CREDENTIALS: {
                METHOD: self.async_step_credentials,
                NEXT: STEP_OPERATION,
            },
            STEP_OPERATION: {
                METHOD: self.async_step_operation,
                NEXT: STEP_OPTIONS,
            },
            STEP_OPTIONS: {METHOD: self.async_step_options},
        }

    # User setup
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Flow initiated by user."""

        return await self.async_step_find(user_input)

    # Find the device
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

    # Credentials & connection
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Credentials step."""

        step_id = STEP_CREDENTIALS

        errors = {}

        if user_input:
            # Check credentials and connection
            result = await _async_check_connection(
                self.hass, self._configs, user_input
            )
            # Show errors if any
            if ERRORS in result:
                errors[BASE] = result[ERRORS]
            else:
                # Save the checked settings to the options
                self._options.update(result[CONFIGS])
                # Set unique ID obtained from the device during the check
                await self.async_set_unique_id(result[UNIQUE_ID])
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: self._configs[CONF_HOST]}
                )
                # Proceed to the next step
                return await _async_process_step(self._steps, step_id)

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_credentials(user_input),
            errors=errors,
        )

    # Operation settings
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
        # Save the operation mode
        self._mode = user_input.get(CONF_MODE, CONF_DEFAULT_MODE)

        # Proceed to the next step
        return await _async_process_step(self._steps, step_id)

    # Options
    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        menu_options = [
            STEP_INTERVALS,
            STEP_INTERFACES,
            STEP_EVENTS,
            STEP_SECURITY,
            STEP_FINISH,
        ]

        # Mode-specific
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            menu_options.insert(0, STEP_CONNECTED_DEVICES)

        return self.async_show_menu(
            step_id=STEP_OPTIONS,
            menu_options=menu_options,
        )

    # Connected devices
    async def async_step_connected_devices(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select connected devices settings."""

        step_id = STEP_CONNECTED_DEVICES

        if not user_input:
            user_input = self._options.copy()
            user_input[ALL_CLIENTS] = await _async_get_clients(
                self.hass, self._configs, self._options
            )
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_connected_devices(
                    user_input, self._mode
                ),
            )
        self._options.update(user_input)

        return await self.async_step_options()

    # Time intervals
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

        return await self.async_step_options()

    # Network monitoring
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

        return await self.async_step_options()

    # HA events
    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Events step."""

        step_id = STEP_EVENTS

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_events(user_input),
            )

        self._options.update(user_input)

        return await self.async_step_options()

    # Security
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

        return await self.async_step_options()

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
    ) -> AROptionsFlowHandler:
        """Get the options flow."""

        return AROptionsFlowHandler()


class AROptionsFlowHandler(OptionsFlow):
    """Options flow for AsusRouter."""

    def __init__(
        self,
    ) -> None:
        """Initialize options flow."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Options flow."""

        self._selection: dict[str, Any] = {}
        self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._host: str = self._configs[CONF_HOST]
        self._options: dict[str, Any] = self.config_entry.options.copy()
        self._mode = self._options.get(CONF_MODE, CONF_DEFAULT_MODE)

        return await self.async_step_options(user_input)

    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select options to change."""

        menu_options = [
            STEP_CREDENTIALS,
            STEP_OPERATION,
            STEP_INTERVALS,
            STEP_INTERFACES,
            STEP_EVENTS,
            STEP_SECURITY,
            STEP_FINISH,
        ]

        # Mode-specific
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            menu_options.insert(2, STEP_CONNECTED_DEVICES)

        return self.async_show_menu(
            step_id=STEP_OPTIONS,
            menu_options=menu_options,
        )

    # Credentials
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select credentials."""

        step_id = STEP_CREDENTIALS

        errors = {}

        if user_input:
            if (
                user_input[CONF_USERNAME] != self._options[CONF_USERNAME]
                or user_input[CONF_PASSWORD] != self._options[CONF_PASSWORD]
                or user_input[CONF_PORT] != self._options[CONF_PORT]
                or user_input[CONF_SSL] != self._options[CONF_SSL]
            ):
                self._options.update(user_input)
                result = await _async_check_connection(
                    self.hass, self._configs, self._options
                )
                if ERRORS in result:
                    errors[BASE] = result[ERRORS]
                else:
                    self._options.update(result[CONFIGS])
                    return await self.async_step_options()
            return await self.async_step_options()

        if not user_input:
            user_input = self._options.copy()

        return self.async_show_form(
            step_id=step_id,
            data_schema=_create_form_credentials(user_input, self._mode),
            errors=errors,
        )

    # Operation mode
    async def async_step_operation(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select operation mode."""

        step_id = STEP_OPERATION

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_operation(user_input, self._mode),
            )

        self._options.update(user_input)
        # Save the operation mode
        self._mode = user_input.get(CONF_MODE, CONF_DEFAULT_MODE)

        return await self.async_step_options()

    # Connected devices
    async def async_step_connected_devices(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select connected devices settings."""

        step_id = STEP_CONNECTED_DEVICES

        if not user_input:
            user_input = self._options.copy()
            # Get the selected clients
            selected = user_input.get(CONF_CLIENT_FILTER_LIST, []).copy()
            # Get all the clients
            all_clients = await _async_get_clients(
                self.hass, self._configs, self._options
            )
            # If client was in the list, but cannot be found now, still add it
            for client in selected:
                if client not in all_clients:
                    all_clients[client] = client.upper()
            # Save the clients as options
            user_input[ALL_CLIENTS] = all_clients
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_connected_devices(
                    user_input, self._mode, default=selected
                ),
            )
        self._options.update(user_input)

        return await self.async_step_options()

    # Update intervals
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

        return await self.async_step_options()

    # Interfaces to monitor
    async def async_step_interfaces(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Step to select network interfaces."""

        step_id = STEP_INTERFACES

        if not user_input:
            user_input = self._options.copy()
            if user_input.get(INTERFACES) is None:
                user_input[INTERFACES] = []
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
                data_schema=_create_form_interfaces(
                    user_input, default=selected
                ),
            )

        self._options.update(user_input)

        return await self.async_step_options()

    # HA events
    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Events step."""

        step_id = STEP_EVENTS

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_events(user_input),
            )

        self._options.update(user_input)

        return await self.async_step_options()

    # Security options
    async def async_step_security(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Security step."""

        step_id = STEP_SECURITY

        if not user_input:
            user_input = self._options.copy()
            return self.async_show_form(
                step_id=step_id,
                data_schema=_create_form_security(user_input),
            )

        self._options.update(user_input)

        return await self.async_step_options()

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
