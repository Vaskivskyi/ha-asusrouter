"""AsusRouter compilers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    GWLAN,
    KEY_GWLAN,
    KEY_OVPN_CLIENT,
    KEY_OVPN_SERVER,
    KEY_SENSOR_ID,
    KEY_WLAN,
    LABEL_SPEED,
    NAME,
    NAME_GWLAN,
    NAME_OVPN_CLIENT,
    NAME_OVPN_SERVER,
    NAME_WLAN,
    NETWORK_STAT,
    SENSORS_GWLAN,
    SENSORS_PARAM_NETWORK,
    SENSORS_VPN,
    SENSORS_VPN_SERVER,
    SENSORS_WLAN,
    VPN,
    WLAN,
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
            if LABEL_SPEED in data[NAME]:
                units = units_speed
            sensors.update(
                {
                    (NETWORK_STAT, key): ARSensorDescription(
                        key=key,
                        key_group=NETWORK_STAT,
                        name=f"{interface} {data[NAME]}" or None,
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
                (VPN, f"{vpn}_state"): ARBinarySensorDescription(
                    key=f"{vpn}_state",
                    key_group=VPN,
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
                (VPN, f"{vpn}_state"): ARSwitchDescription(
                    key=f"{vpn}_state",
                    key_group=VPN,
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


def list_sensors_vpn_servers(number: int | None = None) -> dict[str, Any]:
    """Compile a list of vpn sensors."""

    sensors = dict()

    if not number:
        return sensors

    for num in range(1, number + 1):
        vpn = f"{KEY_OVPN_SERVER}{num}"
        extra_state_attributes = dict()
        for key in SENSORS_VPN_SERVER:
            extra_state_attributes[f"{vpn}_{key}"] = SENSORS_VPN_SERVER[key]
        sensors.update(
            {
                (VPN, f"{vpn}_state"): ARBinarySensorDescription(
                    key=f"{vpn}_state",
                    key_group=VPN,
                    name=f"{NAME_OVPN_SERVER} {num}",
                    device_class=DEVICE_CLASS_CONNECTIVITY,
                    entity_registry_enabled_default=False,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_switches_vpn_servers(number: int | None = None) -> dict[str, Any]:
    """Compile a list of vpn switches."""

    sensors = dict()

    if not number:
        return sensors

    for num in range(1, number + 1):
        vpn = f"{KEY_OVPN_SERVER}{num}"
        extra_state_attributes = dict()
        for key in SENSORS_VPN_SERVER:
            extra_state_attributes[f"{vpn}_{key}"] = SENSORS_VPN_SERVER[key]
        sensors.update(
            {
                (VPN, f"{vpn}_state"): ARSwitchDescription(
                    key=f"{vpn}_state",
                    key_group=VPN,
                    name=f"{NAME_OVPN_SERVER} {num}",
                    icon="mdi:network-outline",
                    icon_on="mdi:check-network-outline",
                    icon_off="mdi:close-network-outline",
                    service_on=f"start_vpnserver{num}",
                    service_off=f"stop_vpnserver{num}",
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_sensors_wlan(
    number: int | None = None, hide: list[str] = list()
) -> dict[str, Any]:
    """Compile a list of wlan sensors."""

    sensors = dict()

    if not number:
        return sensors

    for id in range(0, number + 1):
        wlan = f"{KEY_WLAN}{id}"
        extra_state_attributes = dict()
        for key in SENSORS_WLAN:
            if not key in hide and not SENSORS_WLAN[key] in hide:
                extra_state_attributes[f"{wlan}_{key}"] = SENSORS_WLAN[key]
        sensors.update(
            {
                (WLAN, f"{wlan}_radio"): ARBinarySensorDescription(
                    key=f"{wlan}_radio",
                    key_group=WLAN,
                    name=f"{NAME_WLAN[id]}",
                    device_class=DEVICE_CLASS_CONNECTIVITY,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_switches_wlan(
    number: int | None = None, hide: list[str] = list()
) -> dict[str, Any]:
    """Compile a list of wlan switches."""

    sensors = dict()

    if not number:
        return sensors

    for id in range(0, number + 1):
        wlan = f"{KEY_WLAN}{id}"
        extra_state_attributes = dict()
        for key in SENSORS_WLAN:
            if not key in hide and not SENSORS_WLAN[key] in hide:
                extra_state_attributes[f"{wlan}_{key}"] = SENSORS_WLAN[key]
        sensors.update(
            {
                (WLAN, f"{wlan}_radio"): ARSwitchDescription(
                    key=f"{wlan}_radio",
                    key_group=WLAN,
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
                    device_class="wlan",
                    capabilities={
                        "api_type": WLAN,
                        "api_id": id,
                    },
                    service_expect_modify=True,
                    entity_category=EntityCategory.CONFIG,
                    entity_registry_enabled_default=True,
                    extra_state_attributes=extra_state_attributes,
                )
            }
        )

    return sensors


def list_sensors_gwlan(
    number: int | None = None, hide: list[str] = list()
) -> dict[str, Any]:
    """Compile a list of gwlan sensors."""

    sensors = dict()

    if not number:
        return sensors

    for idm in range(0, number + 1):
        for ida in range(1, number + 2):
            wlan_name = f"{idm}.{ida}"
            wlan = f"{KEY_GWLAN}{idm}.{ida}"
            extra_state_attributes = dict()
            for key in SENSORS_GWLAN:
                if not key in hide and not SENSORS_GWLAN[key] in hide:
                    extra_state_attributes[f"{wlan}_{key}"] = SENSORS_GWLAN[key]
            sensors.update(
                {
                    (
                        GWLAN,
                        f"{wlan}_bss_enabled",
                    ): ARBinarySensorDescription(
                        key=f"{wlan}_bss_enabled",
                        key_group=GWLAN,
                        name=f"{NAME_GWLAN[wlan_name]}",
                        device_class=DEVICE_CLASS_CONNECTIVITY,
                        entity_registry_enabled_default=True,
                        extra_state_attributes=extra_state_attributes,
                    )
                }
            )

    return sensors


def list_switches_gwlan(
    number: int | None = None, hide: list[str] = list()
) -> dict[str, Any]:
    """Compile a list of gwlan switches."""

    sensors = dict()

    if not number:
        return sensors

    for idm in range(0, number + 1):
        for ida in range(1, number + 2):
            wlan_name = f"{idm}.{ida}"
            wlan = f"{KEY_GWLAN}{idm}.{ida}"
            extra_state_attributes = dict()
            for key in SENSORS_GWLAN:
                if not key in hide and not SENSORS_GWLAN[key] in hide:
                    extra_state_attributes[f"{wlan}_{key}"] = SENSORS_GWLAN[key]
            sensors.update(
                {
                    (GWLAN, f"{wlan}_bss_enabled"): ARSwitchDescription(
                        key=f"{wlan}_bss_enabled",
                        key_group=GWLAN,
                        name=f"{NAME_GWLAN[wlan_name]}",
                        icon="mdi:wifi",
                        icon_on="mdi:wifi",
                        icon_off="mdi:wifi-off",
                        service_on="restart_wireless;restart_firewall",
                        service_on_args={
                            "action_mode": "apply",
                            f"wl{wlan_name}_bss_enabled": 1,
                            f"wl{wlan_name}_expire": 0,
                        },
                        service_off="restart_wireless;restart_firewall",
                        service_off_args={
                            "action_mode": "apply",
                            f"wl{wlan_name}_bss_enabled": 0,
                        },
                        device_class="wlan",
                        capabilities={
                            "api_type": GWLAN,
                            "api_id": wlan_name,
                        },
                        service_expect_modify=True,
                        entity_category=EntityCategory.CONFIG,
                        entity_registry_enabled_default=True,
                        extra_state_attributes=extra_state_attributes,
                    )
                }
            )

    return sensors
