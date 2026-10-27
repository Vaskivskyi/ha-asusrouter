"""AsusRouter entity module."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ARCoordinator
from .helpers import to_unique_id

if TYPE_CHECKING:
    from . import ARRuntimeData
    from .bridge import ARBridge


@dataclass(frozen=True, kw_only=True)
class AREntityDescription(EntityDescription):
    """AsusRouter entity description."""

    source: ARDataSource
    update_interval: timedelta
    # The i0 entity name, used only to keep the unique_id unchanged
    unique_id_name: str
    # Reads the entity data, the device's own when None
    data_fn: Callable[[Any], Any] | None = None
    value_fn: Callable[[Any], Any]
    attributes_fn: Callable[[Any], dict[str, Any]] | None = None
    # Whether the data has a live value, always when None
    available_fn: Callable[[Any], bool] | None = None
    # Whether the device of the entry has the entity, not only its nodes
    on_device: bool = True
    # Source of an AiMesh node by its MAC, None when only the router has it
    node_source: Callable[[MacAddress], ARDataSource] | None = None
    # The node source reports the nodes other entries serve as well
    covers_mesh: bool = False
    # None when every device supports the entity
    supported_fn: Callable[[ARBridge], bool] | None = None


@dataclass(frozen=True, kw_only=True)
class ARBinarySensorDescription(
    AREntityDescription, BinarySensorEntityDescription
):
    """AsusRouter binary sensor description."""


@dataclass(frozen=True, kw_only=True)
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """AsusRouter sensor description."""


class AREntity(CoordinatorEntity[ARCoordinator[Any]]):
    """AsusRouter entity of a single device."""

    _attr_has_entity_name = True

    entity_description: AREntityDescription

    def __init__(
        self,
        coordinator: ARCoordinator[Any],
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
    def _device_data(self) -> Any:
        """Return the data of this entity's device."""

        data_fn = self.entity_description.data_fn
        if data_fn is not None:
            return data_fn(self.coordinator.data)

        return self.coordinator.get_device(self._mac)

    @property
    def available(self) -> bool:
        """Return whether the device is in the data with a live value."""

        if not super().available:
            return False

        data = self._device_data
        if data is None:
            return False

        available_fn = self.entity_description.available_fn
        return available_fn is None or available_fn(data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the attributes from the device data."""

        attributes_fn = self.entity_description.attributes_fn
        return (
            None if attributes_fn is None else attributes_fn(self._device_data)
        )


def get_supported[DescriptionT: AREntityDescription](
    descriptions: Iterable[DescriptionT], bridge: ARBridge
) -> list[DescriptionT]:
    """Get the descriptions the device supports."""

    return [
        description
        for description in descriptions
        if description.supported_fn is None or description.supported_fn(bridge)
    ]


def get_entities[DescriptionT: AREntityDescription, EntityT: AREntity](
    runtime_data: ARRuntimeData,
    descriptions: Iterable[DescriptionT],
    entity_type: Callable[
        [ARCoordinator[Any], DescriptionT, MacAddress], EntityT
    ],
) -> list[EntityT]:
    """Get the entities of the device and its AiMesh nodes."""

    mac = runtime_data.bridge.identity.mac
    # Entities are tied to the device MAC, nothing to attach them to
    if mac is None:
        return []

    coordinators = runtime_data.coordinators
    entities: list[EntityT] = []

    for description in get_supported(descriptions, runtime_data.bridge):
        if description.on_device:
            entities.append(
                entity_type(coordinators[description.source], description, mac)
            )
        if description.node_source is None:
            continue
        entities.extend(
            entity_type(
                coordinators[description.node_source(node)], description, node
            )
            for node in runtime_data.get_node_macs(description)
        )

    return entities
