"""AsusRouter config flow module."""

from __future__ import annotations

import logging
import socket
from typing import Any

from asusrouter.error import (
    AsusRouterAccessError,
    AsusRouterConnectionError,
    AsusRouterTimeoutError,
)
from asusrouter.modules.endpoint.error import ARAccessError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .bridge import ARBridge
from .const import (
    BASE,
    CONF_CACHE_TIME,
    CONF_DEFAULT_CACHE_TIME,
    CONF_DEFAULT_EVENT,
    CONF_DEFAULT_HIDE_PASSWORDS,
    CONF_DEFAULT_INTERVALS,
    CONF_DEFAULT_MODE,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_SCAN_INTERVAL,
    CONF_DEFAULT_SPLIT_INTERVALS,
    CONF_DEFAULT_SSL,
    CONF_DEFAULT_USERNAME,
    CONF_HIDE_PASSWORDS,
    CONF_INTERVAL,
    CONF_INTERVALS,
    CONF_LABELS_MODE,
    CONF_MODE,
    CONF_SPLIT_INTERVALS,
    CONF_VALUES_MODE,
    CONFIGS,
    DOMAIN,
    ERRORS,
    FIRMWARE,
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
    STEP_CREDENTIALS,
    STEP_EVENTS,
    STEP_FIND,
    STEP_FINISH,
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

    return bool(
        BASE in errors
        and errors[BASE] != RESULT_SUCCESS
        and errors[BASE] != ""
    )


async def _async_check_connection(  # noqa: C901, PLR0911, PLR0912
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

    result: dict[str, Any] = {}
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
        if args[1] == ARAccessError.CREDENTIALS:
            _LOGGER.error(
                "Error during connection to `%s`. Wrong credentials", host
            )
            return {
                ERRORS: RESULT_WRONG_CREDENTIALS,
            }
        # Try again later / too many attempts
        if args[1] == ARAccessError.TRY_AGAIN:
            timeout = args[2].get("timeout")
            _LOGGER.error(
                "Device `%s` has reported block for the login "
                "(to many wrong attempts were made). Please try again "
                "in `%s` seconds",
                host,
                timeout,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Reset required
        if args[1] == ARAccessError.RESET_REQUIRED:
            _LOGGER.error(
                "Device `%s` requires a reset. Please reset the device. "
                "You won't be able to login to the device until the reset "
                "is done.",
                host,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Captcha required
        if args[1] == ARAccessError.CAPTCHA:
            _LOGGER.error(
                "Device `%s` requires a captcha. Please login to the device "
                "and complete the captcha. Integration cannot proceed with "
                "the captcha request. You need either to disable captcha or "
                "login via Web UI from the HA IP address, complete it and try "
                "again. Sometimes, you can also reboot the device to fix this "
                "issue.",
                host,
            )
            return {
                ERRORS: RESULT_LOGIN_BLOCKED,
            }
        # Another error
        if args[1] == ARAccessError.ANOTHER:
            _LOGGER.error("Device `%s` has reported `another` error.", host)
            return {
                ERRORS: RESULT_ERROR,
            }
        # Unknown error
        if args[1] == ARAccessError.UNKNOWN:
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
            "Connection error during connection to `%s`: "
            "Original exception: %s",
            host,
            ex,
        )
        return {
            ERRORS: RESULT_CONNECTION_ERROR,
        }

    # Anything else
    except Exception as ex:  # noqa: BLE001
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
) -> ConfigFlowResult:
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
                step_result: ConfigFlowResult = await description[METHOD]()
                return step_result
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

    schema: dict[Any, Any] = {
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


def _create_form_intervals(
    user_input: dict[str, Any] | None = None,
    mode: str = CONF_DEFAULT_MODE,
) -> vol.Schema:
    """Create a form for the 'intervals' step."""

    if not user_input:
        user_input = {}

    schema: dict[Any, Any] = {
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
    ) -> ConfigFlowResult:
        """Flow initiated by user."""

        return await self.async_step_find(user_input)

    # Find the device
    async def async_step_find(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
        """Step to select options to change."""

        return self.async_show_menu(
            step_id=STEP_OPTIONS,
            menu_options=[
                STEP_INTERVALS,
                STEP_EVENTS,
                STEP_SECURITY,
                STEP_FINISH,
            ],
        )

    # Time intervals
    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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

    # HA events
    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
        """Step to select options to change."""

        return self.async_show_menu(
            step_id=STEP_OPTIONS,
            menu_options=[
                STEP_CREDENTIALS,
                STEP_OPERATION,
                STEP_INTERVALS,
                STEP_EVENTS,
                STEP_SECURITY,
                STEP_FINISH,
            ],
        )

    # Credentials
    async def async_step_credentials(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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
            # On errors the step repeats, so the user can see them
            if not errors:
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
    ) -> ConfigFlowResult:
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

    # Update intervals
    async def async_step_intervals(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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

    # HA events
    async def async_step_events(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
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
    ) -> ConfigFlowResult:
        """Finish setup."""

        return self.async_create_entry(
            title=self.config_entry.title,
            data=self._options,
        )
