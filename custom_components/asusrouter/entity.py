"""AsusRouter entity module."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ARCoordinator
from .helpers import to_unique_id


@dataclass(frozen=True, kw_only=True)
class AREntityDescription(EntityDescription):
    """AsusRouter entity description."""

    source: ARDataSource
    update_interval: timedelta
    # The i0 entity name, used only to keep the unique_id unchanged
    unique_id_name: str
    value_fn: Callable[[dict[Any, Any]], Any]
    # Source of an AiMesh node by its MAC, None when only the router has it
    node_source: Callable[[MacAddress], ARDataSource] | None = None


@dataclass(frozen=True, kw_only=True)
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """AsusRouter sensor description."""


class AREntity(CoordinatorEntity[ARCoordinator]):
    """AsusRouter entity of a single device."""

    _attr_has_entity_name = True

    entity_description: AREntityDescription

    def __init__(
        self,
        coordinator: ARCoordinator,
        description: AREntityDescription,
        mac: MacAddress,
    ) -> None:
        """Initialize the entity for the device with the given MAC."""

        super().__init__(coordinator)

        self.entity_description = description
        self._mac = mac

        device_mac = format_mac(str(mac))
        self._attr_unique_id = to_unique_id(
            f"{device_mac}_{description.unique_id_name}"
        )
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_mac)})

    @property
    def _device_data(self) -> dict[Any, Any]:
        """Return the data of this entity's device."""

        data: dict[Any, Any] = self.coordinator.data.get(self._mac, {})
        return data

    @property
    def available(self) -> bool:
        """Return whether the device is in the data."""

        return super().available and self._mac in self.coordinator.data
