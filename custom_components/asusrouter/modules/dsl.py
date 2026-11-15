"""AsusRouter DSL module."""

from __future__ import annotations

from datetime import timedelta

from asusrouter.modules.common.metrics import ARMetricType
from asusrouter.modules.dsl import ARDSLSourceUniversal
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfDataRate

from ..entity import ARSensorDescription

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_rate_sensor(
    key: str, metric: ARMetricType, unique_id_name: str
) -> ARSensorDescription:
    """Get the description of a DSL data rate sensor."""

    return ARSensorDescription(
        key=key,
        translation_key=key,
        source=ARDSLSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        # The device reports its DSL, not keyed by its MAC
        data_fn=lambda data: data,
        value_fn=lambda data: data.get(metric),
        # Only a DSL device reports its rates
        exists_fn=lambda data: metric in data,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        suggested_display_precision=0,
    )


SENSORS: tuple[ARSensorDescription, ...] = (
    _get_rate_sensor(
        "dsl_datarate_down",
        ARMetricType.DOWNLOAD_SPEED,
        "DSL Datarate Down",
    ),
    _get_rate_sensor(
        "dsl_datarate_up", ARMetricType.UPLOAD_SPEED, "DSL Datarate Up"
    ),
)
