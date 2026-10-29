"""Tests for the WAN module."""

from __future__ import annotations

from typing import Any

from asusrouter.modules.common.connection import (
    ARConnectionMethod,
    ARConnectionStatus,
)
from asusrouter.modules.wan import (
    ARDualWan,
    ARDualWanMode,
    ARWan,
    ARWanAddress,
    ARWanAggregation,
    ARWanSourceUniversal,
    ARWanUnit,
)
from asusrouter.tools.identifiers.ip import IpAddress
import pytest

from custom_components.asusrouter.entity import AREntityDescription
from custom_components.asusrouter.modules.wan import BINARY_SENSORS, SENSORS


def _get_ip(value: str) -> IpAddress:
    """Create an IP address."""

    ip = IpAddress.from_value_safe(value)
    assert ip is not None
    return ip


def _get_address(prefix: str) -> ARWanAddress:
    """Create a WAN address in the given network."""

    return ARWanAddress(
        ip=_get_ip(f"{prefix}.10"),
        gateway=_get_ip(f"{prefix}.1"),
        mask=_get_ip("255.255.255.0"),
        dns=[_get_ip(f"{prefix}.53")],
        lease=86400,
        expires=3600,
    )


WAN = ARWan(
    active_unit=0,
    units={
        0: ARWanUnit(
            index=0,
            enable=True,
            primary=True,
            protocol=ARConnectionMethod.PPPOE,
            status=ARConnectionStatus.CONNECTED,
            link=True,
            main=_get_address("192.0.2"),
            extra=_get_address("198.51.100"),
        ),
        1: ARWanUnit(index=1, status=ARConnectionStatus.DISCONNECTED),
    },
    dualwan=ARDualWan(
        mode=ARDualWanMode.LOAD_BALANCE, priority=["wan", "usb"], state=True
    ),
    aggregation=ARWanAggregation(state=False, ports=["wan", "lan1"]),
    internet_status=ARConnectionStatus.CONNECTED,
)

DESCRIPTIONS: dict[str, AREntityDescription] = {
    description.key: description for description in (*BINARY_SENSORS, *SENSORS)
}


def _get_description(key: str) -> AREntityDescription:
    """Get a description, checking that it reads the whole WAN state."""

    description = DESCRIPTIONS[key]
    assert description.data_fn is not None
    assert description.data_fn(WAN) is WAN

    return description


@pytest.mark.parametrize("data", [None, {}])
def test_data_unread(data: Any) -> None:
    """Test that nothing is read before the WAN state is."""

    for description in DESCRIPTIONS.values():
        assert description.data_fn is not None
        assert description.data_fn(data) is None


@pytest.mark.parametrize(
    ("key", "unique_id_name", "enabled"),
    [
        ("dual_wan", "Dual WAN", False),
        ("internet", "Internet", True),
        ("wan", "WAN", False),
        ("wan_aggregation", "WAN Aggregation", False),
        ("wan_ip", "WAN IP", False),
        ("wan_ip_extra", "WAN IP (Extra)", False),
        ("wan_ip_secondary", "WAN IP (Secondary)", False),
        ("wan_ip_secondary_extra", "WAN IP (Secondary) (Extra)", False),
        ("wan_secondary", "WAN (Secondary)", False),
    ],
)
def test_description(key: str, unique_id_name: str, enabled: bool) -> None:
    """Test that every entity keeps its i0 unique_id and default."""

    description = _get_description(key)

    assert description.translation_key == key
    assert description.unique_id_name == unique_id_name
    assert description.entity_registry_enabled_default is enabled
    assert description.source is ARWanSourceUniversal


@pytest.mark.parametrize(
    ("status", "value", "available"),
    [
        (ARConnectionStatus.CONNECTED, True, True),
        (ARConnectionStatus.CONNECTING, False, True),
        (ARConnectionStatus.DISCONNECTED, False, True),
        (ARConnectionStatus.UNKNOWN, False, False),
    ],
)
def test_internet(
    status: ARConnectionStatus, value: bool, available: bool
) -> None:
    """Test that the internet connection reports its status."""

    description = _get_description("internet")
    wan = ARWan(internet_status=status)

    assert description.value_fn(wan) is value
    assert description.available_fn is not None
    assert description.available_fn(wan) is available


@pytest.mark.parametrize(
    ("active_unit", "attributes"),
    [
        (0, {"ip_address": "192.0.2.10", "wan_unit": 0}),
        (1, {"ip_address": None, "wan_unit": 1}),
        (None, {"ip_address": None, "wan_unit": None}),
    ],
)
def test_internet_attributes(
    active_unit: int | None, attributes: dict[str, Any]
) -> None:
    """Test that the internet connection reports its WAN unit."""

    description = _get_description("internet")
    wan = ARWan(active_unit=active_unit, units=WAN.units)

    assert description.attributes_fn is not None
    assert description.attributes_fn(wan) == attributes


@pytest.mark.parametrize(
    ("key", "value", "available", "attributes"),
    [
        (
            "wan",
            True,
            True,
            {"link": True, "primary": True, "protocol": "pppoe"},
        ),
        (
            "wan_secondary",
            False,
            True,
            {"link": False, "primary": False, "protocol": None},
        ),
    ],
)
def test_unit(
    key: str, value: bool, available: bool, attributes: dict[str, Any]
) -> None:
    """Test that every WAN unit reports its connection."""

    description = _get_description(key)

    assert description.value_fn(WAN) is value
    assert description.available_fn is not None
    assert description.available_fn(WAN) is available
    assert description.attributes_fn is not None
    assert description.attributes_fn(WAN) == attributes


def test_unit_unknown() -> None:
    """Test that a WAN unit with an unknown status is unavailable."""

    description = _get_description("wan")
    wan = ARWan(units={0: ARWanUnit(index=0)})

    assert description.available_fn is not None
    assert description.available_fn(wan) is False


@pytest.mark.parametrize(
    "key",
    [
        "wan",
        "wan_ip",
        "wan_ip_extra",
        "wan_ip_secondary",
        "wan_ip_secondary_extra",
        "wan_secondary",
    ],
)
def test_unit_missing(key: str) -> None:
    """Test that an entity of a unit missing from the data is unavailable."""

    description = _get_description(key)

    assert description.available_fn is not None
    assert description.available_fn(ARWan()) is False


@pytest.mark.parametrize(
    ("key", "value", "attributes"),
    [
        (
            "wan_ip",
            "192.0.2.10",
            {
                "dns": ["192.0.2.53"],
                "expires": 3600,
                "gateway": "192.0.2.1",
                "lease": 86400,
                "mask": "255.255.255.0",
            },
        ),
        (
            "wan_ip_extra",
            "198.51.100.10",
            {
                "dns": ["198.51.100.53"],
                "expires": 3600,
                "gateway": "198.51.100.1",
                "lease": 86400,
                "mask": "255.255.255.0",
            },
        ),
        # Nothing reported for the unit
        (
            "wan_ip_secondary",
            None,
            {
                "dns": [],
                "expires": None,
                "gateway": None,
                "lease": None,
                "mask": None,
            },
        ),
        (
            "wan_ip_secondary_extra",
            None,
            {
                "dns": [],
                "expires": None,
                "gateway": None,
                "lease": None,
                "mask": None,
            },
        ),
    ],
)
def test_address(
    key: str, value: str | None, attributes: dict[str, Any]
) -> None:
    """Test that every WAN address reports its IP and its network."""

    description = _get_description(key)

    assert description.value_fn(WAN) == value
    assert description.attributes_fn is not None
    assert description.attributes_fn(WAN) == attributes


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (ARDualWanMode.FAILOVER, "failover"),
        (ARDualWanMode.FALLBACK, "fallback"),
        (ARDualWanMode.LOAD_BALANCE, "load_balance"),
        (ARDualWanMode.UNKNOWN, None),
    ],
)
def test_dual_wan(mode: ARDualWanMode, expected: str | None) -> None:
    """Test that the dual WAN reports its state and its mode."""

    description = _get_description("dual_wan")
    wan = ARWan(dualwan=ARDualWan(mode=mode, priority=["wan"], state=True))

    assert description.value_fn(wan) is True
    assert description.attributes_fn is not None
    assert description.attributes_fn(wan) == {
        "mode": expected,
        "priority": ["wan"],
    }


def test_wan_aggregation() -> None:
    """Test that the WAN aggregation reports its state and its ports."""

    description = _get_description("wan_aggregation")

    assert description.value_fn(WAN) is False
    assert description.attributes_fn is not None
    assert description.attributes_fn(WAN) == {"ports": ["wan", "lan1"]}


@pytest.mark.parametrize("key", ["dual_wan", "wan_aggregation"])
@pytest.mark.parametrize(("wan", "expected"), [(WAN, True), (ARWan(), False)])
def test_reported(key: str, wan: ARWan, expected: bool) -> None:
    """Test that a feature exists only when the device reports it."""

    description = _get_description(key)

    assert description.exists_fn is not None
    assert description.exists_fn(wan) is expected
    assert description.available_fn is not None
    assert description.available_fn(wan) is expected
