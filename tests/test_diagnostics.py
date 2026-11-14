"""Tests for the diagnostics module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock

from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.led import ARLedField, ARLedSourceUniversal
from asusrouter.modules.wifi import ARWiFiBand
from asusrouter.tools.identifiers import MacAddress, Password, Ssid
from asusrouter.tools.security import REDACTED_STR
from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
import pytest

from custom_components.asusrouter.diagnostics import (
    _to_plain,
    async_get_config_entry_diagnostics,
)

pytestmark = pytest.mark.asyncio

MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")


@dataclass
class _Data:
    """Data of a source."""

    mac: MacAddress
    when: datetime


class _Object:
    """An object without plain data."""

    def __str__(self) -> str:
        """Return the object as a string."""

        return "object"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (True, True),
        (1.5, 1.5),
        ("text", "text"),
        (ARLedField.STATE, "state"),
        (ARWiFiBand.BAND_2G1, "2g1"),
        (AROperationMode.AIMESH_NODE, "aimesh_node"),
        ((1, 2), [1, 2]),
        (frozenset({3}), [3]),
        ({ARLedField.STATE: [True]}, {"state": [True]}),
        (datetime(2026, 1, 2, 3, 4, tzinfo=UTC), "2026-01-02T03:04:00+00:00"),
        (timedelta(minutes=1), 60.0),
        (_Object(), "object"),
        (Password("secret"), REDACTED_STR),
        (Ssid("Example"), REDACTED_STR),
        # A dataclass type is no data
        (_Data, str(_Data)),
    ],
)
async def test_to_plain(value: Any, expected: Any) -> None:
    """Test that every value is converted to plain data."""

    assert _to_plain(value) == expected


async def test_to_plain_masked() -> None:
    """Test that identifiers are masked, as keys and in dataclasses."""

    masked = str(MAC.mask())
    when = datetime(2026, 1, 2, tzinfo=UTC)

    assert masked != str(MAC)
    assert _to_plain({MAC: _Data(mac=MAC, when=when)}) == {
        masked: {"mac": masked, "when": when.isoformat()}
    }


async def test_diagnostics() -> None:
    """Test that the diagnostics report the device and its data redacted."""

    identity = Mock(
        brand="ASUSTek",
        firmware="3.0.0.4.388.24000_0",
        model="RT-AX88U",
        model_original="RT-AX88U",
        operation_mode=AROperationMode.ROUTER,
        support={"led": True},
        wifi={ARWiFiBand.BAND_2G1: 0},
    )
    coordinator = Mock(
        last_update_success=True,
        data={
            ARLedField.STATE: True,
            "name": "Example",
            "ssid": "Example",
        },
    )
    entry = Mock()
    entry.as_dict.return_value = {
        "data": {
            CONF_HOST: "192.0.2.1",
            CONF_PASSWORD: "secret",
            CONF_USERNAME: "admin",
        },
        "title": "Example",
        "unique_id": "example",
    }
    entry.runtime_data.bridge.identity = identity
    entry.runtime_data.coordinators = {ARLedSourceUniversal: coordinator}
    entry.runtime_data.nodes = [MAC]

    assert await async_get_config_entry_diagnostics(Mock(), entry) == {
        "entry": {
            "data": {
                CONF_HOST: REDACTED,
                CONF_PASSWORD: REDACTED,
                CONF_USERNAME: REDACTED,
            },
            "title": REDACTED,
            "unique_id": REDACTED,
        },
        "device": {
            "brand": "ASUSTek",
            "firmware": "3.0.0.4.388.24000_0",
            "model": "RT-AX88U",
            "model_original": "RT-AX88U",
            "operation_mode": "router",
            "support": {"led": True},
            "wifi": {"2g1": 0},
        },
        "nodes": 1,
        "sources": [
            {
                "source": "ARLedSource",
                "last_update_success": True,
                "data": {"name": REDACTED, "ssid": REDACTED, "state": True},
            }
        ],
    }
