"""Tests for the DDNS module."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.ddns import (
    ARDdnsField,
    ARDdnsServer,
    ARDdnsSourceUniversal,
    ARDdnsStatus,
)
from asusrouter.tools.identifiers import Hostname, IpAddress
import pytest

from custom_components.asusrouter.modules.ddns import (
    BINARY_SENSORS,
    _is_router,
)

DESCRIPTION = BINARY_SENSORS[0]

DDNS: dict[ARDdnsField, Any] = {
    ARDdnsField.HOSTNAME: Hostname("example.asuscomm.com"),
    ARDdnsField.HOSTNAME_OLD: None,
    ARDdnsField.IP_ADDRESS: IpAddress.from_value_safe("192.0.2.10"),
    ARDdnsField.REPLACE_STATUS: False,
    ARDdnsField.SERVER: ARDdnsServer.ASUS,
    ARDdnsField.STATE: True,
    ARDdnsField.STATUS: ARDdnsStatus.SUCCESS,
    ARDdnsField.UPDATED: True,
}


def test_description() -> None:
    """Test that the DDNS keeps its unique_id and default."""

    assert DESCRIPTION.translation_key == "ddns"
    assert DESCRIPTION.unique_id_name == "DDNS"
    assert DESCRIPTION.entity_registry_enabled_default is False
    assert DESCRIPTION.source is ARDdnsSourceUniversal
    assert DESCRIPTION.supported_fn is _is_router


@pytest.mark.parametrize(
    ("data", "expected"),
    [(DDNS, DDNS), ({}, None), (None, None)],
)
def test_data(data: Any, expected: Any) -> None:
    """Test that nothing is read before the DDNS state is."""

    assert DESCRIPTION.data_fn is not None
    assert DESCRIPTION.data_fn(data) == expected


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (AROperationMode.ACCESS_POINT, False),
        (AROperationMode.AIMESH_NODE, False),
        (AROperationMode.ROUTER, True),
        (AROperationMode.UNKNOWN, False),
    ],
)
def test_is_router(mode: AROperationMode, expected: bool) -> None:
    """Test that only a router has the DDNS."""

    bridge = Mock()
    bridge.identity.operation_mode = mode

    assert _is_router(bridge) is expected


@pytest.mark.parametrize(
    ("state", "status", "expected"),
    [
        (True, ARDdnsStatus.REGISTERED_NEW, True),
        (True, ARDdnsStatus.REGISTERED_ORIGINAL, True),
        (True, ARDdnsStatus.SUCCESS, True),
        (True, ARDdnsStatus.AUTH_FAILED, False),
        (True, ARDdnsStatus.NONE, False),
        # Disabled with a registration left over
        (False, ARDdnsStatus.SUCCESS, False),
    ],
)
def test_value(state: bool, status: ARDdnsStatus, expected: bool) -> None:
    """Test that the DDNS is on only when enabled and registered."""

    data = {**DDNS, ARDdnsField.STATE: state, ARDdnsField.STATUS: status}

    assert DESCRIPTION.value_fn(data) is expected


def test_attributes() -> None:
    """Test that the DDNS reports its registration."""

    assert DESCRIPTION.attributes_fn is not None
    assert DESCRIPTION.attributes_fn(DDNS) == {
        "enabled": True,
        "hostname": "example.asuscomm.com",
        "ip_address": "192.0.2.10",
        "old_name": None,
        "replace_status": False,
        "server": "WWW.ASUS.COM",
        "status": "200",
        "updated": True,
    }


@pytest.mark.parametrize(
    ("server", "status"),
    [
        (None, ARDdnsStatus.NONE),
        (ARDdnsServer.UNKNOWN, ARDdnsStatus.UNKNOWN),
    ],
)
def test_attributes_unset(
    server: ARDdnsServer | None, status: ARDdnsStatus
) -> None:
    """Test that an unset or unknown server and status report nothing."""

    data = {**DDNS, ARDdnsField.SERVER: server, ARDdnsField.STATUS: status}

    assert DESCRIPTION.attributes_fn is not None
    attributes = DESCRIPTION.attributes_fn(data)
    assert attributes["server"] is None
    assert attributes["status"] is None
