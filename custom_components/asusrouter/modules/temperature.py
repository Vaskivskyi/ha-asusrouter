"""AsusRouter temperature module."""

from __future__ import annotations

from datetime import timedelta

from asusrouter.modules.temperature import (
    ARTemperatureSourceUniversal,
    ARTemperatureType,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTemperature

from ..entity import ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_temperature_sensor(
    temperature_type: ARTemperatureType, unique_id_name: str
) -> ARSensorDescription:
    """Get the description of a temperature sensor."""

    key = f"temperature_{temperature_type.value}"

    return ARSensorDescription(
        key=key,
        translation_key=key,
        source=ARTemperatureSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        # The device reports its temperatures, not keyed by its MAC
        data_fn=lambda data: data,
        value_fn=lambda data: data.get(temperature_type),
        exists_fn=lambda data: temperature_type in data,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    _get_temperature_sensor(ARTemperatureType.CPU, "Temperature CPU"),
    _get_temperature_sensor(
        ARTemperatureType.RADIO_2G1, "Temperature 2.4 GHz"
    ),
    _get_temperature_sensor(
        ARTemperatureType.RADIO_2G2, "Temperature 2.4 GHz-2"
    ),
    _get_temperature_sensor(ARTemperatureType.RADIO_5G1, "Temperature 5 GHz"),
    _get_temperature_sensor(
        ARTemperatureType.RADIO_5G2, "Temperature 5 GHz-2"
    ),
    _get_temperature_sensor(ARTemperatureType.RADIO_6G1, "Temperature 6 GHz"),
    _get_temperature_sensor(
        ARTemperatureType.RADIO_6G2, "Temperature 6 GHz-2"
    ),
)
