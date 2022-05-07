"""Dataclass module for AsusRouter"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Callable, Mapping

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory, DeviceInfo, EntityDescription, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


@dataclass
class AsusRouterEntityDescription(EntityDescription):
    """"""

    key_group: Callable[[dict], str] | None = None
    value: Callable[[Any], Any] = lambda val: val
    factor: int | None = None
    precision: int = 3
    extra_state_attributes: dict[str, AsusRouterAttributeDescription] | None = None


@dataclass
class AsusRouterSensorDescription(AsusRouterEntityDescription, SensorEntityDescription):
    """Describe AsusRouter sensor"""


@dataclass
class AsusRouterAttributeDescription(AsusRouterEntityDescription, SensorEntityDescription):
    """Describe AsusRouter attribute"""