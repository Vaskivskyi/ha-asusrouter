"""AsusRouter compilers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    KEY_OVPN_CLIENT,
    KEY_SENSOR_ID,
    KEY_WLAN,
    NAME_OVPN_CLIENT,
    NAME_WLAN,
    SENSORS_PARAM_NETWORK,
    SENSORS_TYPE_NETWORK_STAT,
    SENSORS_TYPE_VPN,
    SENSORS_TYPE_WLAN,
    SENSORS_VPN,
    SENSORS_WLAN,
)
from .dataclass import (
    ARBinarySensorDescription,
    ARSensorDescription,
    ARSwitchDescription,
)


def list_sensors_network(
    interfaces: list[str] | None = None,
    units_speed: str = DEFAULT_UNITS_SPEED,
    units_traffic: str = DEFAULT_UNITS_TRAFFIC,
) -> dict[str, Any]:
    """Compile a list of network sensors."""

    sensors = dict()

    if not interfaces:
        return sensors

    for interface in interfaces:
        for type in SENSORS_PARAM_NETWORK:
            data = SENSORS_PARAM_NETWORK[type]
            key = KEY_SENSOR_ID.format(interface, type)
            units = units_traffic
            if "Speed" in data["name"]:
                units = units_speed
            sensors.update(
                {
                    (SENSORS_TYPE_NETWORK_STAT, key): ARSensorDescription(
                        key=key,
                        key_group=SENSORS_TYPE_NETWORK_STAT,
                        name=data["name"].format(interface) or None,
                        icon=data["icon"] or None,
                        state_class=data["state_class"] or None,
                        native_unit_of_measurement=units or None,
                        factor=data["factor"][units] or None,
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


def list_sensors_wlan(number: int | None = None) -> dict[str, Any]:
    """Compile a list of wlan sensors."""

    sensors = dict()

    if not number:
        return sensors

    for id in range(0, number + 1):
        wlan = f"{KEY_WLAN}{id}"
        extra_state_attributes = dict()
        for key in SENSORS_WLAN:
            extra_state_attributes[f"{wlan}_{key}"] = SENSORS_WLAN[key]
        sensors.update(
            {
                (SENSORS_TYPE_WLAN, f"{wlan}_radio"): ARBinarySensorDescription(
                    key=f"{wlan}_radio",
                    key_group=SENSORS_TYPE_WLAN,
                    name=f"{NAME_WLAN[id]}",
                    device_class=DEVICE_CLASS_CONNECTIVITY,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_switches_wlan(number: int | None = None) -> dict[str, Any]:
    """Compile a list of wlan switches."""

    sensors = dict()

    if not number:
        return sensors

    for id in range(0, number + 1):
        wlan = f"{KEY_WLAN}{id}"
        extra_state_attributes = dict()
        for key in SENSORS_WLAN:
            extra_state_attributes[f"{wlan}_{key}"] = SENSORS_WLAN[key]
        sensors.update(
            {
                (SENSORS_TYPE_WLAN, f"{wlan}_radio"): ARSwitchDescription(
                    key=f"{wlan}_radio",
                    key_group=SENSORS_TYPE_WLAN,
                    name=f"{NAME_WLAN[id]}",
                    icon="mdi:wifi",
                    icon_on="mdi:wifi",
                    icon_off="mdi:wifi-off",
                    service_on="restart_wireless",
                    service_on_args={
                        "action_mode": "apply",
                        f"wl{id}_radio": 1,
                    },
                    service_off="restart_wireless",
                    service_off_args={
                        "action_mode": "apply",
                        f"wl{id}_radio": 0,
                    },
                    service_expect_modify=True,
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors
