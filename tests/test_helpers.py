"""Tests for the helpers module."""

from __future__ import annotations

from typing import Any

from asusrouter.tools.identifiers import Hostname, IpAddress, MacAddress
import pytest

from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.helpers import (
    to_identifier,
    to_str,
    to_unique_id,
)


def test_to_identifier() -> None:
    """Test that a MAC is converted to a device identifier."""

    mac = MacAddress.from_value("AA:BB:CC:DD:EE:01")

    assert to_identifier(mac) == (DOMAIN, "aa:bb:cc:dd:ee:01")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (Hostname("example.com"), "example.com"),
        (IpAddress.from_value("192.0.2.10"), "192.0.2.10"),
    ],
)
def test_to_str(value: Any, expected: str | None) -> None:
    """Test that a value is converted to string."""

    assert to_str(value) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Unique ids of i0 entities, which must never change
        ("aa:bb:cc:dd:ee:01_CPU", "aa:bb:cc:dd:ee:01_cpu"),
        ("aa:bb:cc:dd:ee:01_RAM", "aa:bb:cc:dd:ee:01_ram"),
        (
            "aa:bb:cc:dd:ee:01_DSL Datarate Up",
            "aa:bb:cc:dd:ee:01_dsl_datarate_up",
        ),
        # A capital after a lower case letter starts a new word
        ("aa:bb:cc:dd:ee:01_WireGuard", "aa:bb:cc:dd:ee:01_wire_guard"),
        # Separators collapse into a single underscore
        ("aa:bb:cc:dd:ee:01_A - B", "aa:bb:cc:dd:ee:01_a_b"),
    ],
)
def test_to_unique_id(raw: str, expected: str) -> None:
    """Test that a raw name is converted the same way as in i0."""

    assert to_unique_id(raw) == expected
