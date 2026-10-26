"""AsusRouter system status module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.common.metrics import ARMetricType
from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
    ARSystemType,
)
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory

from ..entity import ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_usage(data: dict[Any, Any], system_type: ARSystemType) -> Any:
    """Get the usage of a system component."""

    return data.get(system_type, {}).get(ARMetricType.USAGE)


def _get_usage_sensor(
    key: str, unique_id_name: str, system_type: ARSystemType
) -> ARSensorDescription:
    """Get the description of a system component usage sensor."""

    return ARSensorDescription(
        key=key,
        translation_key=key,
        source=ARSystemStatusSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        value_fn=lambda data: _get_usage(data, system_type),
        node_source=ARSystemStatusSource,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    _get_usage_sensor("cpu", "CPU", ARSystemType.CPU),
    _get_usage_sensor("ram", "RAM", ARSystemType.RAM),
)
