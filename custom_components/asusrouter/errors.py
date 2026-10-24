"""AsusRouter errors module."""

from __future__ import annotations

from asusrouter.error import AsusRouterAccessError
from asusrouter.modules.endpoint.error import ARAccessError

from .const import (
    RESULT_ACCESS_ERROR,
    RESULT_ERROR,
    RESULT_LOGIN_BLOCKED,
    RESULT_UNKNOWN,
    RESULT_WRONG_CREDENTIALS,
)

# Maps a library access error onto the string shown to the user
ACCESS_ERRORS: dict[ARAccessError, str] = {
    ARAccessError.CREDENTIALS: RESULT_WRONG_CREDENTIALS,
    ARAccessError.TRY_AGAIN: RESULT_LOGIN_BLOCKED,
    ARAccessError.RESET_REQUIRED: RESULT_LOGIN_BLOCKED,
    ARAccessError.CAPTCHA: RESULT_LOGIN_BLOCKED,
    ARAccessError.ANOTHER: RESULT_ERROR,
    ARAccessError.UNKNOWN: RESULT_UNKNOWN,
}

# Access errors which only the user can clear
AUTH_ERRORS: frozenset[ARAccessError] = frozenset(
    {
        ARAccessError.CAPTCHA,
        ARAccessError.CREDENTIALS,
        ARAccessError.RESET_REQUIRED,
    }
)


def get_access_error(error: AsusRouterAccessError) -> ARAccessError:
    """Read the access error code the exception carries."""

    for arg in error.args:
        if isinstance(arg, ARAccessError):
            return arg

    return ARAccessError.UNKNOWN


def get_error_result(error: AsusRouterAccessError) -> str:
    """Get the string shown to the user for an access error."""

    return ACCESS_ERRORS.get(get_access_error(error), RESULT_ACCESS_ERROR)


def is_auth_error(error: Exception) -> bool:
    """Check whether an error can only be cleared by new credentials."""

    return (
        isinstance(error, AsusRouterAccessError)
        and get_access_error(error) in AUTH_ERRORS
    )
