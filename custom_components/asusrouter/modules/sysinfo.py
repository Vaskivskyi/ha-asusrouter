"""AsusRouter sysinfo module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from asusrouter.modules.sysinfo import ARSysInfoSourceUniversal, ARSysInfoType
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import EntityCategory

from ..entity import ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)

# Load average windows in minutes
_LOAD_AVERAGE_WINDOWS = (1, 5, 15)


def _get_load_average(data: dict[Any, Any], window: int) -> Any:
    """Get the load average over a window."""

    return data.get(ARSysInfoType.LOAD_AVERAGE, {}).get(window)


def _get_load_average_sensor(window: int) -> ARSensorDescription:
    """Get the description of a load average sensor."""

    key = f"load_average_{window}"

    return ARSensorDescription(
        key=key,
        translation_key=key,
        source=ARSysInfoSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=f"Load Average ({window} min)",
        # The device reports its sysinfo, not keyed by its MAC
        data_fn=lambda data: data,
        value_fn=lambda data: _get_load_average(data, window),
        # Only Merlin firmware reports it
        exists_fn=lambda data: _get_load_average(data, window) is not None,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


SENSORS: tuple[ARSensorDescription, ...] = tuple(
    _get_load_average_sensor(window) for window in _LOAD_AVERAGE_WINDOWS
)
