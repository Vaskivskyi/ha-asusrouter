"""AsusRouter entity module."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asusrouter import AsusRouterError
from asusrouter.modules.action import ARAction
from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
)
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ARCoordinator
from .helpers import to_unique_id

if TYPE_CHECKING:
    from . import ARConfigEntry, ARRuntimeData
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
    # Whether the device reports the entity, always when None
    exists_fn: Callable[[Any], bool] | None = None
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
class ARButtonDescription(AREntityDescription, ButtonEntityDescription):
    """AsusRouter button description."""

    # A button has no state, its source only follows the device
    value_fn: Callable[[Any], Any] = lambda _: None
    # Builds the action the button runs
    action_fn: Callable[[], ARAction]


@dataclass(frozen=True, kw_only=True)
class ARLightDescription(AREntityDescription, LightEntityDescription):
    """AsusRouter light description."""

    # Builds the action turning the light on or off
    action_fn: Callable[[bool], ARAction]


@dataclass(frozen=True, kw_only=True)
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """AsusRouter sensor description."""


def _get_data(
    coordinator: ARCoordinator[Any],
    description: AREntityDescription,
    mac: MacAddress,
) -> Any:
    """Get the data of an entity of the device with the given MAC."""

    if description.data_fn is not None:
        return description.data_fn(coordinator.data)

    return coordinator.get_device(mac)


def _get_targets[DescriptionT: AREntityDescription](
    runtime_data: ARRuntimeData,
    descriptions: Iterable[DescriptionT],
) -> list[tuple[ARCoordinator[Any], DescriptionT, MacAddress]]:
    """Get the coordinator and the MAC of every supported entity."""

    mac = runtime_data.bridge.identity.mac
    # Entities are tied to the device MAC, nothing to attach them to
    if mac is None:
        return []

    coordinators = runtime_data.coordinators
    targets: list[tuple[ARCoordinator[Any], DescriptionT, MacAddress]] = []

    for description in get_supported(descriptions, runtime_data.bridge):
        if description.on_device:
            targets.append(
                (coordinators[description.source], description, mac)
            )
        if description.node_source is None:
            continue
        targets.extend(
            (coordinators[description.node_source(node)], description, node)
            for node in runtime_data.get_node_macs(description)
        )

    return targets


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

        return _get_data(self.coordinator, self.entity_description, self._mac)

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

    async def _async_run_action(
        self, action: ARAction, *, refresh: bool = True
    ) -> None:
        """Run an action on the device."""

        api = self.coordinator.config_entry.runtime_data.bridge.api
        placeholders = {"entity": self.entity_id}

        try:
            result = await api.async_run_action(action)
        except AsusRouterError as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_failed",
                translation_placeholders=placeholders,
            ) from ex
        if not result:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="action_not_applied",
                translation_placeholders=placeholders,
            )

        # Otherwise the new state waits for the next poll
        if refresh:
            await self.coordinator.async_refresh()


def get_supported[DescriptionT: AREntityDescription](
    descriptions: Iterable[DescriptionT], bridge: ARBridge
) -> list[DescriptionT]:
    """Get the descriptions the device supports."""

    return [
        description
        for description in descriptions
        if description.supported_fn is None or description.supported_fn(bridge)
    ]


def _exists(
    coordinator: ARCoordinator[Any],
    description: AREntityDescription,
    mac: MacAddress,
    device_mac: MacAddress | None,
) -> bool | None:
    """Get whether the device with the given MAC has the entity.

    None while not known yet.
    """

    exists_fn = description.exists_fn
    if exists_fn is None:
        return True
    # Nothing was read yet
    if coordinator.data is None:
        return None

    data = _get_data(coordinator, description, mac)
    if data is None:
        # A node missing from the data is offline, while the device itself
        # does not report the entity
        return None if mac != device_mac else False

    return exists_fn(data)


@callback
def async_setup_entities[DescriptionT: AREntityDescription, EntityT: AREntity](
    config_entry: ARConfigEntry,
    descriptions: Iterable[DescriptionT],
    entity_type: Callable[
        [ARCoordinator[Any], DescriptionT, MacAddress], EntityT
    ],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the entities of the device and its AiMesh nodes as they appear."""

    runtime_data = config_entry.runtime_data
    device_mac = runtime_data.bridge.identity.mac
    pending = _get_targets(runtime_data, descriptions)
    listeners: dict[ARCoordinator[Any], CALLBACK_TYPE] = {}

    @callback
    def _async_add_entities() -> None:
        """Add the entities known to exist by now."""

        nonlocal pending

        entities: list[EntityT] = []
        waiting: list[tuple[ARCoordinator[Any], DescriptionT, MacAddress]] = []
        for target in pending:
            exists = _exists(*target, device_mac)
            if exists is None:
                waiting.append(target)
            elif exists:
                entities.append(entity_type(*target))
        pending = waiting

        if entities:
            async_add_entities(entities)

        # Stop listening to the coordinators nothing waits for
        waited = {target[0] for target in pending}
        for coordinator in listeners.keys() - waited:
            listeners.pop(coordinator)()

    _async_add_entities()

    # A coordinator without entities polls only while something waits for it
    for coordinator in {target[0] for target in pending}:
        listeners[coordinator] = coordinator.async_add_listener(
            _async_add_entities
        )

    @callback
    def _async_remove_listeners() -> None:
        """Stop listening to the coordinators."""

        for remove_listener in listeners.values():
            remove_listener()
        listeners.clear()

    config_entry.async_on_unload(_async_remove_listeners)
