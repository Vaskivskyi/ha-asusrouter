"""Tests for the errors module."""

from __future__ import annotations

from typing import Any

from asusrouter.error import AsusRouterAccessError, AsusRouterConnectionError
from asusrouter.modules.endpoint.error import ARAccessError
import pytest

from custom_components.asusrouter.const import (
    RESULT_ACCESS_ERROR,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
)
from custom_components.asusrouter.errors import (
    get_access_error,
    get_error_result,
    is_auth_error,
)


def _access_error(
    error: ARAccessError | None = None, **attributes: Any
) -> AsusRouterAccessError:
    """Create an access error as the library raises it."""

    if error is None:
        # The library omits the code for a plain HTTP error status
        return AsusRouterAccessError("Access error")

    return AsusRouterAccessError("Access error", error, attributes)


# ---------------------------
# ACCESS ERROR -->
# ---------------------------


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_access_error(ARAccessError.CREDENTIALS), ARAccessError.CREDENTIALS),
        (
            _access_error(ARAccessError.TRY_AGAIN, timeout=60),
            ARAccessError.TRY_AGAIN,
        ),
        # An access error the library raises without a code
        (_access_error(), ARAccessError.UNKNOWN),
    ],
)
def test_get_access_error(
    error: AsusRouterAccessError, expected: ARAccessError
) -> None:
    """Test that the error code is read from any argument position."""

    assert get_access_error(error) is expected


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ARAccessError.CREDENTIALS, RESULT_WRONG_CREDENTIALS),
        (ARAccessError.TRY_AGAIN, RESULT_LOGIN_BLOCKED),
        (ARAccessError.RESET_REQUIRED, RESULT_LOGIN_BLOCKED),
        (ARAccessError.CAPTCHA, RESULT_LOGIN_BLOCKED),
        (ARAccessError.ANOTHER, RESULT_ERROR),
        (ARAccessError.UNKNOWN, RESULT_UNKNOWN),
        # An access error without a mapping of its own
        (ARAccessError.NO_TOKEN, RESULT_ACCESS_ERROR),
    ],
)
def test_get_error_result(error: ARAccessError, expected: str) -> None:
    """Test that each access error maps to its own result."""

    assert get_error_result(_access_error(error)) == expected


# ---------------------------
# <-- ACCESS ERROR
# ---------------------------

# ---------------------------
# AUTHENTICATION -->
# ---------------------------


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_access_error(ARAccessError.CREDENTIALS), True),
        (_access_error(ARAccessError.CAPTCHA), True),
        (_access_error(ARAccessError.RESET_REQUIRED), True),
        # The device lifts this lock on its own
        (_access_error(ARAccessError.TRY_AGAIN, timeout=60), False),
        (_access_error(ARAccessError.ANOTHER), False),
        (_access_error(), False),
        # Not an access error at all
        (AsusRouterConnectionError(), False),
    ],
)
def test_is_auth_error(error: Exception, expected: bool) -> None:
    """Test that only the errors needing new credentials are recognised."""

    assert is_auth_error(error) is expected


# ---------------------------
# <-- AUTHENTICATION
# ---------------------------
