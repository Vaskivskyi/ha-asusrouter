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
LOCALES = sorted((COMPONENT / "translations").iterdir())
ENGLISH = COMPONENT / "translations" / "en.json"

# `RESULT_X = "value"` / `STEP_X = "value"`
CONSTANTS = re.compile(r'^(RESULT|STEP)_\w+ = "([^"]+)"', re.MULTILINE)

# `{placeholder}` of a translation string
PLACEHOLDERS = re.compile(r"\{(\w+)\}")

# A reference to the Home Assistant common strings
REFERENCE = "[%key:"

# Home Assistant titles a reauth flow with the entry title and nothing else,
# and the integration has no discovery step adding placeholders of its own
FLOW_TITLE_PLACEHOLDERS = {"name"}

# The placeholders the flow passes to each step, by step id
STEP_PLACEHOLDERS: dict[str, set[str]] = {
    "reauth_confirm": {"host"},
}


def _get_constants(prefix: str) -> set[str]:
    """Get the values of every constant with the given prefix."""

    source = CONST.read_text(encoding="utf-8")

    return {
        value for name, value in CONSTANTS.findall(source) if name == prefix
    }


def _get_config(source: Path = STRINGS) -> dict[str, Any]:
    """Get the config section of a translation source."""

    config: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))[
        "config"
    ]

    return config


def _flatten(data: Any, prefix: str = "") -> set[str]:
    """Return every leaf path of a nested mapping."""

    if not isinstance(data, dict):
        return {prefix}

    return {
        key
        for name, value in data.items()
        for key in _flatten(value, f"{prefix}.{name}")
    }


def _get_placeholders(data: Any) -> set[str]:
    """Return every placeholder used by a translation subtree."""

    if not isinstance(data, dict):
        return set(PLACEHOLDERS.findall(str(data)))

    return {key for value in data.values() for key in _get_placeholders(value)}


@pytest.mark.parametrize(
    ("prefix", "section"),
    [
        ("RESULT", "error"),
        ("STEP", "step"),
    ],
)
def test_constants_have_strings(prefix: str, section: str) -> None:
    """Test that every constant shown to the user can be translated."""

    assert _get_constants(prefix) <= set(_get_config()[section])


@pytest.mark.parametrize(
    ("prefix", "section"),
    [
        ("RESULT", "error"),
        ("STEP", "step"),
    ],
)
def test_strings_are_used(prefix: str, section: str) -> None:
    """Test that no string is kept for a constant which no longer exists."""

    assert set(_get_config()[section]) <= _get_constants(prefix)


@pytest.mark.parametrize("source", [STRINGS, *LOCALES], ids=lambda p: p.name)
def test_flow_title_placeholders(source: Path) -> None:
    """Test that the flow title only uses provided placeholders."""

    title = _get_config(source).get("flow_title", "")

    assert set(PLACEHOLDERS.findall(title)) <= FLOW_TITLE_PLACEHOLDERS


@pytest.mark.parametrize("source", [STRINGS, *LOCALES], ids=lambda p: p.name)
def test_step_placeholders(source: Path) -> None:
    """Test that each step only uses the placeholders the flow passes."""

    for step, content in _get_config(source).get("step", {}).items():
        expected = STEP_PLACEHOLDERS.get(step, set())

        assert _get_placeholders(content) <= expected, step


@pytest.mark.parametrize("locale", LOCALES, ids=lambda p: p.name)
def test_locales_have_no_references(locale: Path) -> None:
    """Test that no locale ships an unresolved reference."""

    assert REFERENCE not in locale.read_text(encoding="utf-8")


def test_english_matches_the_source() -> None:
    """Test that the English locale offers every string of the source."""

    assert _flatten(_get_config(ENGLISH)) == _flatten(_get_config())


@pytest.mark.parametrize("locale", LOCALES, ids=lambda p: p.name)
def test_locales_match_the_source(locale: Path) -> None:
    """Test that no locale offers a string the source does not have."""

    assert _flatten(_get_config(locale)) <= _flatten(_get_config())
