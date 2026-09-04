"""Tests for the config flow module."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import socket
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

from asusrouter.error import (
    AsusRouterAccessError,
    AsusRouterConnectionError,
    AsusRouterTimeoutError,
)
from asusrouter.modules.endpoint.error import ARAccessError
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
)
import pytest

from custom_components.asusrouter import config_flow
from custom_components.asusrouter.config_flow import (
    ARFlowHandler,
    AROptionsFlowHandler,
    _async_check_connection,
    _async_process_step,
    _check_errors,
    _check_host,
    _create_form_credentials,
    _create_form_events,
    _create_form_find,
    _create_form_intervals,
    _create_form_operation,
    _create_form_security,
)
from custom_components.asusrouter.const import (
    ACCESS_POINT,
    BASE,
    CONF_CACHE_TIME,
    CONF_DEFAULT_EVENT,
    CONF_HIDE_PASSWORDS,
    CONF_INTERVAL,
    CONF_INTERVALS,
    CONF_MODE,
    CONF_SPLIT_INTERVALS,
    CONFIGS,
    ERRORS,
    FIRMWARE,
    METHOD,
    NEXT,
    NODE,
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

pytestmark = pytest.mark.asyncio

HOST = "192.168.1.1"
SERIAL = "SERIAL123"
NEW_PORT = 1234

CONFIGS_DATA: dict[str, Any] = {CONF_HOST: HOST}
OPTIONS_DATA: dict[str, Any] = {
    CONF_USERNAME: "user",
    CONF_PASSWORD: "password",
    CONF_PORT: 8443,
    CONF_SSL: True,
}


def _mock_bridge(
    connect: Any = None, serial: str | None = SERIAL
) -> tuple[Mock, Mock]:
    """Create a patched bridge class and its instance."""

    bridge = Mock(
        async_connect=AsyncMock(side_effect=connect),
        async_disconnect=AsyncMock(),
        async_clean=AsyncMock(),
        identity=Mock(serial=serial),
    )

    return Mock(return_value=bridge), bridge


def _access_error(error: ARAccessError, **attributes: Any) -> Exception:
    """Create an access error as the library raises it."""

    return AsusRouterAccessError("Access error", error, attributes)


# HELPERS ->


async def test_check_host_resolves() -> None:
    """Test that a resolvable host returns its IP address."""

    with patch.object(socket, "gethostbyname", return_value=HOST):
        assert _check_host("router.local") == HOST


async def test_check_host_cannot_resolve() -> None:
    """Test that an unresolvable host returns nothing."""

    with patch.object(socket, "gethostbyname", side_effect=socket.gaierror):
        assert _check_host("router.local") is None


@pytest.mark.parametrize(
    ("errors", "expected"),
    [
        (None, False),
        ({}, False),
        ({"other": RESULT_ERROR}, False),
        ({BASE: RESULT_SUCCESS}, False),
        ({BASE: ""}, False),
        ({BASE: RESULT_ERROR}, True),
    ],
)
async def test_check_errors(
    errors: dict[str, Any] | None, expected: bool
) -> None:
    """Test the error check."""

    assert _check_errors(errors) is expected


# <- HELPERS

# CONNECTION CHECK ->


async def test_check_connection_no_host() -> None:
    """Test that a missing host is reported as an error."""

    assert await _async_check_connection(Mock(), {}) == {ERRORS: RESULT_ERROR}


async def test_check_connection_success() -> None:
    """Test a successful connection check."""

    bridge_class, bridge = _mock_bridge()

    with patch.object(config_flow, "ARBridge", bridge_class):
        result = await _async_check_connection(
            Mock(), CONFIGS_DATA, OPTIONS_DATA
        )

    assert result[UNIQUE_ID] == SERIAL
    # Only the options are returned, the configs are stripped
    assert result[CONFIGS] == OPTIONS_DATA
    bridge.async_clean.assert_awaited_once()
    bridge.async_disconnect.assert_awaited_once()


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (_access_error(ARAccessError.CREDENTIALS), RESULT_WRONG_CREDENTIALS),
        (
            _access_error(ARAccessError.TRY_AGAIN, timeout=60),
            (RESULT_LOGIN_BLOCKED),
        ),
        (_access_error(ARAccessError.RESET_REQUIRED), RESULT_LOGIN_BLOCKED),
        (_access_error(ARAccessError.CAPTCHA), RESULT_LOGIN_BLOCKED),
        (_access_error(ARAccessError.ANOTHER), RESULT_ERROR),
        (_access_error(ARAccessError.UNKNOWN), RESULT_UNKNOWN),
        (_access_error(ARAccessError.NO_TOKEN), RESULT_ACCESS_ERROR),
        (AsusRouterTimeoutError(), RESULT_TIMEOUT),
        (AsusRouterConnectionError(), RESULT_CONNECTION_ERROR),
        (ValueError("anything else"), RESULT_UNKNOWN),
    ],
)
async def test_check_connection_errors(
    exception: Exception, expected: str
) -> None:
    """Test that each connection failure maps to its own result."""

    bridge_class, bridge = _mock_bridge(connect=exception)

    with patch.object(config_flow, "ARBridge", bridge_class):
        result = await _async_check_connection(Mock(), CONFIGS_DATA)

    assert result == {ERRORS: expected}
    # The session is closed even when the connection fails
    bridge.async_clean.assert_awaited_once()


# <- CONNECTION CHECK

# STEP PROCESSING ->


async def test_process_step_unknown() -> None:
    """Test that an unknown step is rejected."""

    with pytest.raises(ValueError, match="cannot be found"):
        await _async_process_step({}, "missing")


async def test_process_step_next() -> None:
    """Test that the next step is initialized."""

    shown = cast("ConfigFlowResult", {"step_id": "second"})
    method = AsyncMock(return_value=shown)
    steps: dict[str, dict[str, Any]] = {
        "first": {NEXT: "second"},
        "second": {METHOD: method},
    }

    assert await _async_process_step(steps, "first") is shown
    method.assert_awaited_once()


async def test_process_step_repeats_on_error() -> None:
    """Test that a step with errors repeats itself."""

    shown = cast("ConfigFlowResult", {"step_id": "first"})
    method = AsyncMock(return_value=shown)
    steps: dict[str, dict[str, Any]] = {
        "first": {METHOD: method, NEXT: "second"}
    }

    result = await _async_process_step(steps, "first", {BASE: RESULT_ERROR})

    assert result is shown
    method.assert_awaited_once()


async def test_process_step_no_method_on_error() -> None:
    """Test that a step with errors and no method is rejected."""

    with pytest.raises(ValueError, match="not properly defined"):
        await _async_process_step(
            {"first": {NEXT: "second"}}, "first", {BASE: RESULT_ERROR}
        )


async def test_process_step_no_next() -> None:
    """Test that a step without a next step is rejected."""

    with pytest.raises(ValueError, match="not properly defined"):
        await _async_process_step({"first": {METHOD: AsyncMock()}}, "first")


# <- STEP PROCESSING

# FORMS ->


@pytest.mark.parametrize(
    ("creator", "user_input", "expected"),
    [
        (_create_form_find, None, [CONF_HOST]),
        (_create_form_find, {CONF_HOST: HOST}, [CONF_HOST]),
        (
            _create_form_credentials,
            None,
            [CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_SSL],
        ),
        (
            _create_form_operation,
            None,
            [CONF_MODE, CONF_SPLIT_INTERVALS],
        ),
        (
            _create_form_events,
            None,
            list(CONF_DEFAULT_EVENT),
        ),
        (_create_form_security, None, [CONF_HIDE_PASSWORDS]),
    ],
)
async def test_create_forms(
    creator: Any, user_input: dict[str, Any] | None, expected: list[str]
) -> None:
    """Test that each form offers the expected keys."""

    schema = creator(user_input)

    assert [str(key) for key in schema.schema] == expected


@pytest.mark.parametrize(
    ("split", "expected"),
    [
        (
            False,
            [CONF_CACHE_TIME, CONF_SCAN_INTERVAL, CONF_INTERVAL + FIRMWARE],
        ),
        (True, [CONF_CACHE_TIME, *CONF_INTERVALS]),
    ],
)
async def test_create_form_intervals(split: bool, expected: list[str]) -> None:
    """Test that splitting the intervals changes the form."""

    schema = _create_form_intervals({CONF_SPLIT_INTERVALS: split})

    assert [str(key) for key in schema.schema] == expected


async def test_create_form_intervals_no_input() -> None:
    """Test the intervals form with no previous input."""

    schema = _create_form_intervals()

    assert [str(key) for key in schema.schema] == [
        CONF_CACHE_TIME,
        CONF_SCAN_INTERVAL,
        CONF_INTERVAL + FIRMWARE,
    ]


# <- FORMS

# CONFIG FLOW ->


@dataclass
class FlowMocks:
    """The Home Assistant flow methods replaced for a test."""

    form: Mock
    menu: Mock
    entry: Mock


@dataclass
class ConfigFlowMocks(FlowMocks):
    """The flow methods only a config flow provides."""

    unique_id: AsyncMock
    abort: Mock


@contextmanager
def _patch_flow(handler: type) -> Iterator[FlowMocks]:
    """Replace the Home Assistant machinery of a flow handler."""

    with (
        patch.object(handler, "async_show_form") as form,
        patch.object(handler, "async_show_menu") as menu,
        patch.object(handler, "async_create_entry") as entry,
    ):
        yield FlowMocks(form, menu, entry)


@pytest.fixture(name="flow")
def mock_flow() -> Iterator[tuple[ARFlowHandler, ConfigFlowMocks]]:
    """Create a config flow with the HA machinery mocked out."""

    hass = Mock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=lambda target, *args: target(*args)
    )

    flow = ARFlowHandler()
    flow.hass = hass

    with (
        _patch_flow(ARFlowHandler) as mocks,
        patch.object(
            ARFlowHandler, "async_set_unique_id", AsyncMock()
        ) as unique_id,
        patch.object(ARFlowHandler, "_abort_if_unique_id_configured") as abort,
    ):
        yield (
            flow,
            ConfigFlowMocks(
                mocks.form, mocks.menu, mocks.entry, unique_id, abort
            ),
        )


async def test_flow_step_user(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that the user step opens the find step."""

    handler, mocks = flow

    await handler.async_step_user()

    assert mocks.form.call_args.kwargs["step_id"] == STEP_FIND


async def test_flow_step_find_cannot_resolve(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that an unresolvable host repeats the find step."""

    handler, mocks = flow

    with patch.object(socket, "gethostbyname", side_effect=socket.gaierror):
        await handler.async_step_find({CONF_HOST: HOST})

    assert mocks.form.call_args.kwargs["errors"] == {
        BASE: RESULT_CANNOT_RESOLVE
    }


async def test_flow_step_find_success(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that a resolvable host moves to the credentials step."""

    handler, mocks = flow

    await handler.async_step_find({CONF_HOST: HOST})

    assert handler._configs == {CONF_HOST: HOST}
    assert mocks.form.call_args.kwargs["step_id"] == STEP_CREDENTIALS


async def test_flow_step_credentials_error(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that a failed connection repeats the credentials step."""

    handler, mocks = flow
    handler._configs = CONFIGS_DATA.copy()

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value={ERRORS: RESULT_WRONG_CREDENTIALS}),
    ):
        await handler.async_step_credentials(OPTIONS_DATA)

    assert mocks.form.call_args.kwargs["errors"] == {
        BASE: RESULT_WRONG_CREDENTIALS
    }


async def test_flow_step_credentials_success(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that a successful connection moves to the operation step."""

    handler, mocks = flow
    handler._configs = CONFIGS_DATA.copy()

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(
            return_value={UNIQUE_ID: SERIAL, CONFIGS: OPTIONS_DATA.copy()}
        ),
    ):
        await handler.async_step_credentials(OPTIONS_DATA)

    mocks.unique_id.assert_awaited_once_with(SERIAL)
    mocks.abort.assert_called_once_with(updates={CONF_HOST: HOST})
    assert handler._options == OPTIONS_DATA
    assert mocks.form.call_args.kwargs["step_id"] == STEP_OPERATION


async def test_flow_step_operation_form(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that the operation step shows its form."""

    handler, mocks = flow

    await handler.async_step_operation()

    assert mocks.form.call_args.kwargs["step_id"] == STEP_OPERATION


async def test_flow_step_operation_saves_mode(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that the operation step stores the mode and moves on."""

    handler, mocks = flow

    await handler.async_step_operation({CONF_MODE: ACCESS_POINT})

    assert handler._mode == ACCESS_POINT
    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS


async def test_flow_step_options_menu(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test the options menu of the config flow."""

    handler, mocks = flow

    await handler.async_step_options()

    assert mocks.menu.call_args.kwargs["menu_options"] == [
        STEP_INTERVALS,
        STEP_EVENTS,
        STEP_SECURITY,
        STEP_FINISH,
    ]


@pytest.mark.parametrize(
    ("step", "step_id", "user_input"),
    [
        ("async_step_intervals", STEP_INTERVALS, {CONF_CACHE_TIME: 10}),
        ("async_step_events", STEP_EVENTS, {"device_connected": False}),
        ("async_step_security", STEP_SECURITY, {CONF_HIDE_PASSWORDS: True}),
    ],
)
async def test_flow_option_steps(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
    step: str,
    step_id: str,
    user_input: dict[str, Any],
) -> None:
    """Test that each option step shows a form, then returns to the menu."""

    handler, mocks = flow

    await getattr(handler, step)()

    assert mocks.form.call_args.kwargs["step_id"] == step_id

    await getattr(handler, step)(user_input)

    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS
    assert handler._options.items() >= user_input.items()


async def test_flow_step_finish(
    flow: tuple[ARFlowHandler, ConfigFlowMocks],
) -> None:
    """Test that finishing creates the config entry."""

    handler, mocks = flow
    handler._configs = CONFIGS_DATA.copy()
    handler._options = OPTIONS_DATA.copy()

    await handler.async_step_finish()

    mocks.entry.assert_called_once_with(
        title=HOST, data=CONFIGS_DATA, options=OPTIONS_DATA
    )


async def test_flow_get_options_flow() -> None:
    """Test that the options flow handler is served."""

    assert isinstance(
        ARFlowHandler.async_get_options_flow(Mock()), AROptionsFlowHandler
    )


# <- CONFIG FLOW

# OPTIONS FLOW ->


@pytest.fixture(name="options_flow")
def mock_options_flow() -> Iterator[tuple[AROptionsFlowHandler, FlowMocks]]:
    """Create an options flow with the HA machinery mocked out."""

    flow = AROptionsFlowHandler()
    flow.hass = Mock()

    entry = Mock(
        data=CONFIGS_DATA.copy(),
        options=OPTIONS_DATA.copy(),
        title=HOST,
    )

    with (
        patch.object(
            AROptionsFlowHandler,
            "config_entry",
            new_callable=PropertyMock,
            return_value=entry,
        ),
        _patch_flow(AROptionsFlowHandler) as mocks,
    ):
        yield flow, mocks


async def test_options_flow_init(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that the options flow reads the config entry."""

    handler, mocks = options_flow

    await handler.async_step_init()

    assert handler._configs == CONFIGS_DATA
    assert handler._options == OPTIONS_DATA
    assert handler._host == HOST
    assert mocks.menu.call_args.kwargs["menu_options"] == [
        STEP_CREDENTIALS,
        STEP_OPERATION,
        STEP_INTERVALS,
        STEP_EVENTS,
        STEP_SECURITY,
        STEP_FINISH,
    ]


async def test_options_flow_credentials_form(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that the credentials step shows its form."""

    handler, mocks = options_flow
    await handler.async_step_init()

    await handler.async_step_credentials()

    assert mocks.form.call_args.kwargs["step_id"] == STEP_CREDENTIALS


async def test_options_flow_credentials_unchanged(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that unchanged credentials are not re-checked."""

    handler, mocks = options_flow
    await handler.async_step_init()

    with patch.object(
        config_flow, "_async_check_connection", AsyncMock()
    ) as check:
        await handler.async_step_credentials(OPTIONS_DATA.copy())

    check.assert_not_awaited()
    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS


async def test_options_flow_credentials_changed(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that changed credentials are checked and stored."""

    handler, mocks = options_flow
    await handler.async_step_init()

    user_input = {**OPTIONS_DATA, CONF_PASSWORD: "new"}

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value={CONFIGS: {CONF_PORT: NEW_PORT}}),
    ):
        await handler.async_step_credentials(user_input)

    assert handler._options[CONF_PASSWORD] == "new"
    assert handler._options[CONF_PORT] == NEW_PORT
    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS


async def test_options_flow_credentials_error(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that a failed check repeats the credentials step."""

    handler, mocks = options_flow
    await handler.async_step_init()

    user_input = {**OPTIONS_DATA, CONF_PASSWORD: "new"}

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value={ERRORS: RESULT_WRONG_CREDENTIALS}),
    ):
        await handler.async_step_credentials(user_input)

    assert mocks.form.call_args.kwargs["errors"] == {
        BASE: RESULT_WRONG_CREDENTIALS
    }


async def test_options_flow_operation(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that the operation step stores the mode."""

    handler, mocks = options_flow
    await handler.async_step_init()

    await handler.async_step_operation()

    assert mocks.form.call_args.kwargs["step_id"] == STEP_OPERATION

    await handler.async_step_operation({CONF_MODE: NODE})

    assert handler._mode == NODE
    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS


@pytest.mark.parametrize(
    ("step", "step_id", "user_input"),
    [
        ("async_step_intervals", STEP_INTERVALS, {CONF_CACHE_TIME: 10}),
        ("async_step_events", STEP_EVENTS, {"device_connected": False}),
        ("async_step_security", STEP_SECURITY, {CONF_HIDE_PASSWORDS: True}),
    ],
)
async def test_options_flow_steps(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
    step: str,
    step_id: str,
    user_input: dict[str, Any],
) -> None:
    """Test that each option step shows a form, then returns to the menu."""

    handler, mocks = options_flow
    await handler.async_step_init()

    await getattr(handler, step)()

    assert mocks.form.call_args.kwargs["step_id"] == step_id

    await getattr(handler, step)(user_input)

    assert mocks.menu.call_args.kwargs["step_id"] == STEP_OPTIONS
    assert handler._options.items() >= user_input.items()


async def test_options_flow_finish(
    options_flow: tuple[AROptionsFlowHandler, FlowMocks],
) -> None:
    """Test that finishing stores the options."""

    handler, mocks = options_flow
    await handler.async_step_init()

    await handler.async_step_finish()

    mocks.entry.assert_called_once_with(title=HOST, data=OPTIONS_DATA)


# <- OPTIONS FLOW
