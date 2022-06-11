"""AsusRouter compilers."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from typing import Any

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from homeassistant.helpers.entity import EntityCategory

from .const import (
    KEY_OVPN_CLIENT,
    KEY_SENSOR_ID,
    NAME_OVPN_CLIENT,
    SENSORS_PARAM_NETWORK,
    SENSORS_TYPE_NETWORK_STAT,
    SENSORS_TYPE_VPN,
    SENSORS_VPN,
)
from .dataclass import (
    ARBinarySensorDescription,
    ARSensorDescription,
    ARSwitchDescription,
)


def list_sensors_network(
    interfaces: list[str] | None = None,
) -> dict[str, Any]:
    """Compile a list of network sensors."""

    sensors = dict()

    if not interfaces:
        return sensors

    for interface in interfaces:
        for type in SENSORS_PARAM_NETWORK:
            data = SENSORS_PARAM_NETWORK[type]
            key = KEY_SENSOR_ID.format(interface, type)
            sensors.update(
                {
                    (SENSORS_TYPE_NETWORK_STAT, key): ARSensorDescription(
                        key=key,
                        key_group=SENSORS_TYPE_NETWORK_STAT,
                        name=data["name"].format(interface) or None,
                        icon=data["icon"] or None,
                        state_class=data["state_class"] or None,
                        native_unit_of_measurement=data["native_unit_of_measurement"]
                        or None,
                        factor=data["factor"] or None,
                        entity_registry_enabled_default=data[
                            "entity_registry_enabled_default"
                        ]
                        or None,
                        extra_state_attributes={
                            key: data["raw_attribute"] or None,
                        },
                    )
                }
            )

    return sensors


def list_sensors_vpn_clients(number: int | None = None) -> dict[str, Any]:
    """Compile a list of vpn sensors."""

    sensors = dict()

    if not number:
        return sensors

    for num in range(1, number + 1):
        vpn = f"{KEY_OVPN_CLIENT}{num}"
        extra_state_attributes = dict()
        for key in SENSORS_VPN:
            extra_state_attributes[f"{vpn}_{key}"] = SENSORS_VPN[key]
        sensors.update(
            {
                (SENSORS_TYPE_VPN, f"{vpn}_state"): ARBinarySensorDescription(
                    key=f"{vpn}_state",
                    key_group=SENSORS_TYPE_VPN,
                    name=f"{NAME_OVPN_CLIENT} {num}",
                    device_class=DEVICE_CLASS_CONNECTIVITY,
                    entity_registry_enabled_default=False,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_switches_vpn_clients(number: int | None = None) -> dict[str, Any]:
    """Compile a list of vpn switches."""

    sensors = dict()

    if not number:
        return sensors

    for num in range(1, number + 1):
        vpn = f"{KEY_OVPN_CLIENT}{num}"
        extra_state_attributes = dict()
        for key in SENSORS_VPN:
            extra_state_attributes[f"{vpn}_{key}"] = SENSORS_VPN[key]
        sensors.update(
            {
                (SENSORS_TYPE_VPN, f"{vpn}_state"): ARSwitchDescription(
                    key=f"{vpn}_state",
                    key_group=SENSORS_TYPE_VPN,
                    name=f"{NAME_OVPN_CLIENT} {num}",
                    icon="mdi:network-outline",
                    icon_on="mdi:check-network-outline",
                    icon_off="mdi:close-network-outline",
                    service_on=f"start_vpnclient{num}",
                    service_off=f"stop_vpnclient{num}",
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors
