"""AsusRouter WAN module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.common.connection import (
    ARConnectionMethod,
    ARConnectionStatus,
)
from asusrouter.modules.wan import (
    ARDualWanMode,
    ARWan,
    ARWanAddress,
    ARWanSourceUniversal,
    ARWanUnit,
)
from asusrouter.tools.identifiers.ip import IpAddress
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from ..entity import ARBinarySensorDescription, ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)

# Index of the unit, its key and its i0 label
_UNITS = ((0, "", ""), (1, "_secondary", " (Secondary)"))


def _get_wan(data: Any) -> ARWan | None:
    """Get the WAN state, None when nothing was read."""

    return data if isinstance(data, ARWan) else None


# The device reports its WAN, not keyed by its MAC
_WAN: dict[str, Any] = {
    "source": ARWanSourceUniversal,
    "update_interval": UPDATE_INTERVAL,
    "data_fn": _get_wan,
    "entity_category": EntityCategory.DIAGNOSTIC,
}


def _has_aggregation(wan: ARWan) -> bool:
    """Get whether the device reports WAN aggregation."""

    return wan.aggregation is not None


def _has_dual_wan(wan: ARWan) -> bool:
    """Get whether the device reports dual WAN."""

    return wan.dualwan is not None


def _to_str(ip: IpAddress | None) -> str | None:
    """Get an IP address as a string."""

    return None if ip is None else str(ip)


def _get_internet_attributes(wan: ARWan) -> dict[str, Any]:
    """Get the attributes of the internet connection."""

    unit = None if wan.active_unit is None else wan.units.get(wan.active_unit)

    return {
        "ip_address": None if unit is None else _to_str(unit.main.ip),
        "wan_unit": wan.active_unit,
    }


def _get_unit_attributes(unit: ARWanUnit) -> dict[str, Any]:
    """Get the attributes of a WAN unit."""

    protocol = unit.protocol

    return {
        "link": unit.link,
        "primary": unit.primary,
        "protocol": (
            None if protocol is ARConnectionMethod.UNKNOWN else protocol.value
        ),
    }


def _get_address_attributes(address: ARWanAddress) -> dict[str, Any]:
    """Get the attributes of a WAN address."""

    return {
        "dns": [str(dns) for dns in address.dns],
        "expires": address.expires,
        "gateway": _to_str(address.gateway),
        "lease": address.lease,
        "mask": _to_str(address.mask),
    }


def _get_unit_sensor(
    index: int, key: str, label: str
) -> ARBinarySensorDescription:
    """Get the description of the binary sensor of a WAN unit."""

    return ARBinarySensorDescription(
        key=f"wan{key}",
        translation_key=f"wan{key}",
        unique_id_name=f"WAN{label}",
        value_fn=lambda wan: (
            wan.units[index].status is ARConnectionStatus.CONNECTED
        ),
        attributes_fn=lambda wan: _get_unit_attributes(wan.units[index]),
        available_fn=lambda wan: (
            index in wan.units
            and wan.units[index].status is not ARConnectionStatus.UNKNOWN
        ),
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_registry_enabled_default=False,
        **_WAN,
    )


def _get_address_sensor(
    index: int, key: str, label: str, *, extra: bool
) -> ARSensorDescription:
    """Get the description of the sensor of a WAN unit address."""

    def _get_address(wan: ARWan) -> ARWanAddress:
        """Get the address of the unit."""

        unit = wan.units[index]
        return unit.extra if extra else unit.main

    suffix = "_extra" if extra else ""

    return ARSensorDescription(
        key=f"wan_ip{key}{suffix}",
        translation_key=f"wan_ip{key}{suffix}",
        unique_id_name=f"WAN IP{label}{' (Extra)' if extra else ''}",
        value_fn=lambda wan: _to_str(_get_address(wan).ip),
        attributes_fn=lambda wan: _get_address_attributes(_get_address(wan)),
        available_fn=lambda wan: index in wan.units,
        entity_registry_enabled_default=False,
        **_WAN,
    )


BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    ARBinarySensorDescription(
        key="dual_wan",
        translation_key="dual_wan",
        unique_id_name="Dual WAN",
        value_fn=lambda wan: wan.dualwan.state,
        attributes_fn=lambda wan: {
            "mode": (
                None
                if wan.dualwan.mode is ARDualWanMode.UNKNOWN
                else wan.dualwan.mode.name.lower()
            ),
            "priority": wan.dualwan.priority,
        },
        available_fn=_has_dual_wan,
        exists_fn=_has_dual_wan,
        entity_registry_enabled_default=False,
        **_WAN,
    ),
    ARBinarySensorDescription(
        key="internet",
        translation_key="internet",
        unique_id_name="Internet",
        value_fn=lambda wan: (
            wan.internet_status is ARConnectionStatus.CONNECTED
        ),
        attributes_fn=_get_internet_attributes,
        available_fn=lambda wan: (
            wan.internet_status is not ARConnectionStatus.UNKNOWN
        ),
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        **_WAN,
    ),
    *(_get_unit_sensor(*unit) for unit in _UNITS),
    ARBinarySensorDescription(
        key="wan_aggregation",
        translation_key="wan_aggregation",
        unique_id_name="WAN Aggregation",
        value_fn=lambda wan: wan.aggregation.state,
        attributes_fn=lambda wan: {"ports": wan.aggregation.ports},
        available_fn=_has_aggregation,
        exists_fn=_has_aggregation,
        entity_registry_enabled_default=False,
        **_WAN,
    ),
)

SENSORS: tuple[ARSensorDescription, ...] = tuple(
    _get_address_sensor(*unit, extra=extra)
    for extra in (False, True)
    for unit in _UNITS
)
