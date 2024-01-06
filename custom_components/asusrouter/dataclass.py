"""AsusRouter dataclass module."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from asusrouter.modules.state import AsusState, AsusStateNone
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.components.update import UpdateEntityDescription
from homeassistant.helpers.entity import EntityDescription


@dataclass
class AREntityDescription(EntityDescription):
    """Describe AsusRouter entity."""

    capabilities: Optional[dict[str, Any]] = None
    key_group: str = ""
    value: Callable[[Any], Any] = lambda val: val
    extra_state_attributes: Optional[dict[str, Any]] = None


@dataclass
class ARBinaryDescription(AREntityDescription, BinarySensorEntityDescription):
    """Describe AsusRouter binary entity."""

    icon_on: Optional[str] = None
    icon_off: Optional[str] = None


@dataclass
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """Describe AsusRouter sensor."""

    factor: Optional[int] = None
    precision: int = 3


@dataclass
class ARBinarySensorDescription(ARBinaryDescription, BinarySensorEntityDescription):
    """Describe AsusRouter sensor."""


@dataclass
class ARLightDescription(ARBinaryDescription, LightEntityDescription):
    """Describe AsusRouter light."""


@dataclass
class ARSwitchDescription(AREntityDescription, SwitchEntityDescription):
    """Describe AsusRouter switch."""

    icon_on: Optional[str] = None
    icon_off: Optional[str] = None

    state_on: AsusState = AsusStateNone.NONE
    state_on_args: Optional[dict[str, Any]] = None
    state_off: AsusState = AsusStateNone.NONE
    state_off_args: Optional[dict[str, Any]] = None

    state_expect_modify: bool = False


@dataclass
class ARButtonDescription(AREntityDescription, ButtonEntityDescription):
    """Describe AsusRouter button."""

    state: AsusState = AsusStateNone.NONE
    state_args: Optional[dict[str, Any]] = None
    state_expect_modify: bool = False


@dataclass
class ARUpdateDescription(AREntityDescription, UpdateEntityDescription):
    """Describe AsusRouter update."""
