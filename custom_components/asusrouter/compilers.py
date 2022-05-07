"""Compilers module for AsusRouter"""

from __future__ import annotations

from typing import Any

from .dataclass import AsusRouterSensorDescription
from .const import SENSORS_PARAM_NETWORK, KEY_SENSOR_ID

KEY_SENSORS_NETWORK_STAT = "network_stat"


def list_sensors_network(interfaces : list[str] | None = None) -> dict[str, Any]:
    """Compile a list of network sensors"""

    sensors = dict()

    if not interfaces:
        return sensors

    for interface in interfaces:
        for type in SENSORS_PARAM_NETWORK:
            data = SENSORS_PARAM_NETWORK[type]
            key = KEY_SENSOR_ID.format(interface, type)
            sensors.update({
                (KEY_SENSORS_NETWORK_STAT, key): AsusRouterSensorDescription(
                    key = key,
                    key_group = KEY_SENSORS_NETWORK_STAT,
                    name = data["name"].format(interface) or None,
                    icon = data["icon"] or None,
                    state_class = data["state_class"] or None,
                    native_unit_of_measurement = data["native_unit_of_measurement"] or None,
                    factor = data["factor"] or None,
                    entity_registry_enabled_default = data["entity_registry_enabled_default"] or None,
                    extra_state_attributes = {
                        key: data["raw_attribute"] or None,
                    }
                )
            })

    return sensors


