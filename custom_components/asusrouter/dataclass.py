"""AsusRouter dataclasses."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.helpers.entity import EntityDescription


@dataclass
class AREntityDescription(EntityDescription):
    """Describe AsusRouter entity."""

    key_group: Callable[[dict], str] | None = None
    value: Callable[[Any], Any] = lambda val: val
    factor: int | None = None
    precision: int = 3
    extra_state_attributes: dict[str, Any] | None = None


@dataclass
class ARBinaryDescription(AREntityDescription, BinarySensorEntityDescription):
    """Describe AsusRouter binary entity."""

    icon_on: str | None = None
    icon_off: str | None = None


@dataclass
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """Describe AsusRouter sensor."""


@dataclass
class ARBinarySensorDescription(ARBinaryDescription, BinarySensorEntityDescription):
    """Describe AsusRouter sensor."""


@dataclass
class ARLightDescription(ARBinaryDescription, LightEntityDescription):
    """Describe AsusRouter light."""


@dataclass
class ARSwitchDescription(ARBinaryDescription, SwitchEntityDescription):
    """Describe AsusRouter switch."""

    service_on: str | None = None
    service_on_args: dict[str, Any] | None = None
    service_off: str | None = None
    service_off_args: dict[str, Any] | None = None
    service_expect_modify: bool = False
