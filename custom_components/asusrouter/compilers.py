"""AsusRouter compilers"""

from __future__ import annotations

from typing import Any

from .const import (
    KEY_SENSOR_ID,
    SENSORS_PARAM_NETWORK,
    SENSORS_TYPE_NETWORK_STAT,
)
from .dataclass import ARSensorDescription


def list_sensors_network(
    interfaces: list[str] | None = None,
) -> dict[str, Any]:
    """Compile a list of network sensors"""

    sensors = dict()

    if not interfaces:
        return sensors

    for interface in interfaces:
        for type in SENSORS_PARAM_NETWORK:
            data = SENSORS_PARAM_NETWORK[type]
            key = KEY_SENSOR_ID.format(interface, type)
            sensors.update({
                (SENSORS_TYPE_NETWORK_STAT, key): ARSensorDescription(
                    key = key,
                    key_group = SENSORS_TYPE_NETWORK_STAT,
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


