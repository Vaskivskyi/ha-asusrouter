"""AsusRouter dataclasses"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Callable

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.helpers.entity import EntityDescription


@dataclass
class AREntityDescription(EntityDescription):
    """Describe AsusRouter entity"""

    key_group: Callable[[dict], str] | None = None
    value: Callable[[Any], Any] = lambda val: val
    factor: int | None = None
    precision: int = 3
    extra_state_attributes: dict[str, Any] | None = None


@dataclass
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """Describe AsusRouter sensor"""


@dataclass
class ARBinarySensorDescription(AREntityDescription, BinarySensorEntityDescription):
    """Describe AsusRouter sensor"""


@dataclass
class ARLightDescription(AREntityDescription, LightEntityDescription):
    """Describe AsusRouter light"""

    icon_on: str | None = None
    icon_off: str | None = None


