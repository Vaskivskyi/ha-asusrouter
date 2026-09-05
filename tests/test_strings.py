"""Tests keeping the translations in step with the code."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import pytest

COMPONENT = Path("custom_components/asusrouter")
CONST = COMPONENT / "const.py"
STRINGS = COMPONENT / "strings.json"

# `RESULT_X = "value"` / `STEP_X = "value"`
CONSTANTS = re.compile(r'^(RESULT|STEP)_\w+ = "([^"]+)"', re.MULTILINE)


def _get_constants(prefix: str) -> set[str]:
    """Get the values of every constant with the given prefix."""

    source = CONST.read_text(encoding="utf-8")

    return {
        value for name, value in CONSTANTS.findall(source) if name == prefix
    }


def _get_strings() -> dict[str, Any]:
    """Get the config section of the source strings."""

    config: dict[str, Any] = json.loads(STRINGS.read_text(encoding="utf-8"))[
        "config"
    ]

    return config


@pytest.mark.parametrize(
    ("prefix", "section"),
    [
        ("RESULT", "error"),
        ("STEP", "step"),
    ],
)
def test_constants_have_strings(prefix: str, section: str) -> None:
    """Test that every constant shown to the user can be translated."""

    assert _get_constants(prefix) <= set(_get_strings()[section])


@pytest.mark.parametrize(
    ("prefix", "section"),
    [
        ("RESULT", "error"),
        ("STEP", "step"),
    ],
)
def test_strings_are_used(prefix: str, section: str) -> None:
    """Test that no string is kept for a constant which no longer exists."""

    assert set(_get_strings()[section]) <= _get_constants(prefix)


def test_locales_match_the_source() -> None:
    """Test that every locale offers the same keys as the source strings."""

    def flatten(data: Any, prefix: str = "") -> set[str]:
        """Return every leaf path of a nested mapping."""

        if not isinstance(data, dict):
            return {prefix}

        return {
            key
            for name, value in data.items()
            for key in flatten(value, f"{prefix}.{name}")
        }

    expected = flatten(_get_strings())

    for locale in sorted((COMPONENT / "translations").iterdir()):
        content = json.loads(locale.read_text(encoding="utf-8"))
        assert flatten(content["config"]) <= expected, locale.name
