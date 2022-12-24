"""AsusRouter compilers."""

from __future__ import annotations

from typing import Any

from .const import (
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    KEY_SENSOR_ID,
    LABEL_SPEED,
    NAME,
    NETWORK_STAT,
    SENSORS_PARAM_NETWORK,
)
from .dataclass import (
    ARSensorDescription,
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
