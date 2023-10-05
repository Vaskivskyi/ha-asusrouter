"""AsusRouter compilers module."""

from __future__ import annotations

from .const import (
    CONF_DEFAULT_UNITS_SPEED,
    CONF_DEFAULT_UNITS_TRAFFIC,
    CONF_LABELS_INTERFACES,
    LABEL_SPEED,
    MAP_NETWORK_TEMP,
    NAME,
    NETWORK,
    SENSORS_PARAM_NETWORK,
)
from .dataclass import ARSensorDescription


def list_sensors_network(
    interfaces: list[str] | None = None,
) -> list[ARSensorDescription]:
    """Compile a list of network sensors."""

    sensors: list[ARSensorDescription] = []

    if not interfaces or len(interfaces) < 1:
        return sensors

    for intf in interfaces:
        interface = MAP_NETWORK_TEMP.get(intf, intf)
        for sensor_type, data in SENSORS_PARAM_NETWORK.items():
            key = f"{interface}_{sensor_type}"
            sensors.append(
                ARSensorDescription(
                    key=key,
                    key_group=NETWORK,
                    name=f"{CONF_LABELS_INTERFACES.get(interface, interface)} {data[NAME]}"
                    or None,
                    icon=data["icon"] or None,
                    state_class=data["state_class"] or None,
                    device_class=data["device_class"] or None,
                    native_unit_of_measurement=data["native_unit_of_measurement"]
                    or None,
                    suggested_unit_of_measurement=data["suggested_unit_of_measurement"]
                    or None,
                    suggested_display_precision=data["suggested_display_precision"]
                    or None,
                    entity_registry_enabled_default=data[
                        "entity_registry_enabled_default"
                    ]
                    or True,
                    extra_state_attributes={
                        key: data["raw_attribute"] or None,
                    },
                )
            )

    return sensors
