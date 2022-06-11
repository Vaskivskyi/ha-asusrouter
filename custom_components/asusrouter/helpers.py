"""AsusRouter helpers."""

from __future__ import annotations

from typing import Any


def flatten_dict(obj: Any, keystring: str = "", delimiter: str = "_"):
    """Flatten dictionary"""

    if type(obj) == dict:
        keystring = keystring + delimiter if keystring else keystring
        for key in obj:
            yield from flatten_dict(obj[key], keystring + str(key))
    else:
        yield keystring, obj


def as_dict(pyobj):
    """Return generator object as dictionary."""

    return {key: value for key, value in pyobj}
