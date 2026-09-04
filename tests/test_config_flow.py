"""Tests for the config flow module."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import socket
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter.error import (
    AsusRouterAccessError,
    AsusRouterConnectionError,
    AsusRouterTimeoutError,
)
from asusrouter.modules.endpoint.error import ARAccessError
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
import pytest

from custom_components.asusrouter import config_flow
from custom_components.asusrouter.config_flow import (
    ARFlowHandler,
    _async_check_connection,
    _check_host,
    _create_form_credentials,
    _create_form_find,
    _create_form_reconfigure,
)
from custom_components.asusrouter.const import (
    BASE,
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

pytestmark = pytest.mark.asyncio

HOST = "192.168.1.1"
SERIAL = "SERIAL123"

HOST_DATA: dict[str, Any] = {CONF_HOST: HOST}
CREDENTIALS_DATA: dict[str, Any] = {
    CONF_USERNAME: "user",
    CONF_PASSWORD: "password",
    CONF_PORT: 8443,
    CONF_SSL: True,
}
ENTRY_DATA: dict[str, Any] = {**HOST_DATA, **CREDENTIALS_DATA}


def _mock_bridge(
    connect: Any = None, serial: str | None = SERIAL
) -> tuple[Mock, Mock]:
    """Create a patched bridge class and its instance."""

    bridge = Mock(
        async_connect=AsyncMock(side_effect=connect),
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


# <- HELPERS

# CONNECTION CHECK ->


async def test_check_connection_success() -> None:
    """Test that a successful check returns the device serial."""

    bridge_class, bridge = _mock_bridge()

    with patch.object(config_flow, "ARBridge", bridge_class):
        assert await _async_check_connection(Mock(), ENTRY_DATA) == (
            SERIAL,
            None,
        )

    bridge.async_clean.assert_awaited_once()


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (_access_error(ARAccessError.CREDENTIALS), RESULT_WRONG_CREDENTIALS),
        (_access_error(ARAccessError.TRY_AGAIN), RESULT_LOGIN_BLOCKED),
        (_access_error(ARAccessError.RESET_REQUIRED), RESULT_LOGIN_BLOCKED),
        (_access_error(ARAccessError.CAPTCHA), RESULT_LOGIN_BLOCKED),
        (_access_error(ARAccessError.ANOTHER), RESULT_ERROR),
        (_access_error(ARAccessError.UNKNOWN), RESULT_UNKNOWN),
        # An access error with no mapping of its own
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
        assert await _async_check_connection(Mock(), ENTRY_DATA) == (
            None,
            expected,
        )

    # The session is closed even when the connection fails
    bridge.async_clean.assert_awaited_once()


# <- CONNECTION CHECK

# FORMS ->


@pytest.mark.parametrize(
    ("creator", "expected"),
    [
        (_create_form_find, [CONF_HOST]),
        (
            _create_form_credentials,
            [CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_SSL],
        ),
        (
            _create_form_reconfigure,
            [CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_PORT, CONF_SSL],
        ),
    ],
)
async def test_create_forms(creator: Any, expected: list[str]) -> None:
    """Test that each form offers the expected keys."""

    assert [str(key) for key in creator().schema] == expected


@pytest.mark.parametrize(
    ("creator", "user_input", "key"),
    [
        (_create_form_find, HOST_DATA, CONF_HOST),
        (_create_form_credentials, CREDENTIALS_DATA, CONF_USERNAME),
        (_create_form_reconfigure, ENTRY_DATA, CONF_HOST),
    ],
)
async def test_create_forms_prefilled(
    creator: Any, user_input: dict[str, Any], key: str
) -> None:
    """Test that a form is prefilled with the known values."""

    schema = creator(user_input).schema
    defaults = {str(item): item.default() for item in schema}

    assert defaults[key] == user_input[key]


# <- FORMS

# CONFIG FLOW ->


@dataclass
class FlowMocks:
    """The Home Assistant flow methods replaced for a test."""

    form: Mock
    entry: Mock
    unique_id: AsyncMock
    abort_configured: Mock
    abort_mismatch: Mock
    reload_and_abort: Mock


@contextmanager
def _patch_flow() -> Iterator[FlowMocks]:
    """Replace the Home Assistant machinery of the flow handler."""

    with (
        patch.object(ARFlowHandler, "async_show_form") as form,
        patch.object(ARFlowHandler, "async_create_entry") as entry,
        patch.object(
            ARFlowHandler, "async_set_unique_id", AsyncMock()
        ) as unique_id,
        patch.object(
            ARFlowHandler, "_abort_if_unique_id_configured"
        ) as abort_configured,
        patch.object(
            ARFlowHandler, "_abort_if_unique_id_mismatch"
        ) as abort_mismatch,
        patch.object(
            ARFlowHandler, "async_update_reload_and_abort"
        ) as reload_and_abort,
    ):
        yield FlowMocks(
            form,
            entry,
            unique_id,
            abort_configured,
            abort_mismatch,
            reload_and_abort,
        )


@pytest.fixture(name="flow")
def mock_flow() -> Iterator[tuple[ARFlowHandler, FlowMocks]]:
    """Create a config flow with the HA machinery mocked out."""

    hass = Mock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=lambda target, *args: target(*args)
    )

    flow = ARFlowHandler()
    flow.hass = hass

    with _patch_flow() as mocks:
        yield flow, mocks


async def test_flow_step_user(flow: tuple[ARFlowHandler, FlowMocks]) -> None:
    """Test that the user step opens the find step."""

    handler, mocks = flow

    await handler.async_step_user()

    assert mocks.form.call_args.kwargs["step_id"] == STEP_FIND


async def test_flow_step_find_cannot_resolve(
    flow: tuple[ARFlowHandler, FlowMocks],
) -> None:
    """Test that an unresolvable host repeats the find step."""

    handler, mocks = flow

    with patch.object(socket, "gethostbyname", side_effect=socket.gaierror):
        await handler.async_step_find(HOST_DATA)

    assert mocks.form.call_args.kwargs["step_id"] == STEP_FIND
    assert mocks.form.call_args.kwargs["errors"] == {
        BASE: RESULT_CANNOT_RESOLVE
    }
    assert handler._configs == {}


async def test_flow_step_find_success(
    flow: tuple[ARFlowHandler, FlowMocks],
) -> None:
    """Test that a resolvable host moves to the credentials step."""

    handler, mocks = flow

    with patch.object(socket, "gethostbyname", return_value=HOST):
        await handler.async_step_find(HOST_DATA)

    assert handler._configs == HOST_DATA
    assert mocks.form.call_args.kwargs["step_id"] == STEP_CREDENTIALS


async def test_flow_step_credentials_error(
    flow: tuple[ARFlowHandler, FlowMocks],
) -> None:
    """Test that a failed connection repeats the credentials step."""

    handler, mocks = flow
    handler._configs = HOST_DATA.copy()

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value=(None, RESULT_WRONG_CREDENTIALS)),
    ):
        await handler.async_step_credentials(CREDENTIALS_DATA)

    assert mocks.form.call_args.kwargs["errors"] == {
        BASE: RESULT_WRONG_CREDENTIALS
    }
    mocks.entry.assert_not_called()


async def test_flow_step_credentials_success(
    flow: tuple[ARFlowHandler, FlowMocks],
) -> None:
    """Test that a successful connection creates the entry."""

    handler, mocks = flow
    handler._configs = HOST_DATA.copy()

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value=(SERIAL, None)),
    ):
        await handler.async_step_credentials(CREDENTIALS_DATA)

    mocks.unique_id.assert_awaited_once_with(SERIAL)
    mocks.abort_configured.assert_called_once_with(updates={CONF_HOST: HOST})
    mocks.entry.assert_called_once_with(title=HOST, data=ENTRY_DATA)


# <- CONFIG FLOW

# RECONFIGURE ->


@pytest.fixture(name="reconfigure_flow")
def mock_reconfigure_flow(
    flow: tuple[ARFlowHandler, FlowMocks],
) -> Iterator[tuple[ARFlowHandler, FlowMocks, Mock]]:
    """Create a config flow reconfiguring a known entry."""

    handler, mocks = flow
    entry = Mock(data=ENTRY_DATA.copy())

    with patch.object(
        ARFlowHandler, "_get_reconfigure_entry", Mock(return_value=entry)
    ):
        yield handler, mocks, entry


async def test_flow_step_reconfigure_form(
    reconfigure_flow: tuple[ARFlowHandler, FlowMocks, Mock],
) -> None:
    """Test that the reconfigure step is prefilled from the entry."""

    handler, mocks, _ = reconfigure_flow

    await handler.async_step_reconfigure()

    schema = mocks.form.call_args.kwargs["data_schema"].schema
    defaults = {str(item): item.default() for item in schema}

    assert mocks.form.call_args.kwargs["step_id"] == STEP_RECONFIGURE
    assert defaults[CONF_HOST] == HOST
    assert defaults[CONF_USERNAME] == CREDENTIALS_DATA[CONF_USERNAME]


async def test_flow_step_reconfigure_error(
    reconfigure_flow: tuple[ARFlowHandler, FlowMocks, Mock],
) -> None:
    """Test that a failed connection repeats the reconfigure step."""

    handler, mocks, _ = reconfigure_flow

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value=(None, RESULT_TIMEOUT)),
    ):
        await handler.async_step_reconfigure(ENTRY_DATA)

    assert mocks.form.call_args.kwargs["errors"] == {BASE: RESULT_TIMEOUT}
    mocks.reload_and_abort.assert_not_called()


async def test_flow_step_reconfigure_success(
    reconfigure_flow: tuple[ARFlowHandler, FlowMocks, Mock],
) -> None:
    """Test that reconfiguring updates and reloads the entry."""

    handler, mocks, entry = reconfigure_flow
    user_input = {**ENTRY_DATA, CONF_PASSWORD: "new"}

    with patch.object(
        config_flow,
        "_async_check_connection",
        AsyncMock(return_value=(SERIAL, None)),
    ):
        await handler.async_step_reconfigure(user_input)

    mocks.unique_id.assert_awaited_once_with(SERIAL)
    # A different device must not overwrite this entry
    mocks.abort_mismatch.assert_called_once()
    mocks.reload_and_abort.assert_called_once_with(entry, data=user_input)


# <- RECONFIGURE
