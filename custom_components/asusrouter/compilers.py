"""AsusRouter compilers."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_LABELS_INTERFACES,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TRAFFIC,
    LABEL_SPEED,
    MAP_NETWORK_TEMP,
    NAME,
    NETWORK,
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

    for intf in interfaces:
        interface = MAP_NETWORK_TEMP.get(intf, intf)
        for type in SENSORS_PARAM_NETWORK:
            data = SENSORS_PARAM_NETWORK[type]
            key = f"{interface}_{type}"
            units = units_traffic
            if LABEL_SPEED in data[NAME]:
                units = units_speed
            sensors.update(
                {
                    (NETWORK, key): ARSensorDescription(
                        key=key,
                        key_group=NETWORK,
                        name=f"{CONF_LABELS_INTERFACES.get(interface, interface)} {data[NAME]}"
                        or None,
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
