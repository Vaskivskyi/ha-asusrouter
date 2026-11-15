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
from homeassistant.components.device_tracker import ScannerEntityDescription
from homeassistant.components.light import LightEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.components.update import UpdateEntityDescription
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
    # The name the unique_id is built from, kept for existing entities
    unique_id_name: str = ""
    # Reads the entity data, the device's own when None
    data_fn: Callable[[Any], Any] | None = None
    value_fn: Callable[[Any], Any]
    attributes_fn: Callable[[Any], dict[str, Any]] | None = None
    # Names the entity from its data, its translated name when None
    name_fn: Callable[[Any], str | None] | None = None
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
    # Reads the keys of an entity each from the data, a single one when None
    keys_fn: Callable[[Any], Iterable[Any]] | None = None
    # Reads the data of a key
    item_fn: Callable[[Any, Any], Any] | None = None
    # Builds the name the unique_id of a key is built from
    unique_id_fn: Callable[[Any], str] | None = None
    # Builds the translation placeholders of a key
    placeholders_fn: Callable[[Any], dict[str, str]] | None = None
    # Removes the entity of a key the device stops reporting, otherwise it
    # stays unavailable
    remove_missing: bool = False
    # Builds the device of a key linked to the device id, from the key and
    # its data, the device itself when None
    device_info_fn: Callable[[str, Any, Any], DeviceInfo] | None = None


@dataclass(frozen=True, kw_only=True)
class ARToggleDescription(AREntityDescription):
    """AsusRouter description of an entity turned on and off."""

    # Builds the action turning the entity on or off from its data
    action_fn: Callable[[bool, Any], ARAction]


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
    # Builds the action the button runs on the device
    action_fn: Callable[[], ARAction] | None = None
    # Runs in Home Assistant instead of an action on the device
    press_fn: Callable[[HomeAssistant, ARConfigEntry], None] | None = None


@dataclass(frozen=True, kw_only=True)
class ARLightDescription(ARToggleDescription, LightEntityDescription):
    """AsusRouter light description."""

    # Effects the light can show, none when empty
    effects: tuple[str, ...] = ()
    # Reads the effect, None when no effect is shown
    effect_fn: Callable[[Any], str | None] | None = None
    # Reads the RGB color, a light without colors when None
    rgb_fn: Callable[[Any], tuple[int, int, int] | None] | None = None
    # Reads the brightness on 0..255
    brightness_fn: Callable[[Any], int | None] | None = None
    # Builds the action turning the light on with the requested settings,
    # the plain action when None
    turn_on_fn: Callable[[dict[str, Any], Any], ARAction] | None = None


@dataclass(frozen=True, kw_only=True)
class ARSensorDescription(AREntityDescription, SensorEntityDescription):
    """AsusRouter sensor description."""


@dataclass(frozen=True, kw_only=True)
class ARSwitchDescription(ARToggleDescription, SwitchEntityDescription):
    """AsusRouter switch description."""


@dataclass(frozen=True, kw_only=True)
class ARTrackerDescription(AREntityDescription, ScannerEntityDescription):
    """AsusRouter device tracker description."""

    # Reads the IP address of the tracked device
    ip_fn: Callable[[Any], str | None]
    # Reads the hostname of the tracked device
    hostname_fn: Callable[[Any], str | None]


@dataclass(frozen=True, kw_only=True)
class ARUpdateDescription(AREntityDescription, UpdateEntityDescription):
    """AsusRouter update description."""

    # The installed version is the value, the latest one is read here
    latest_fn: Callable[[Any], str | None]
    # Reads the release notes, none when None
    release_notes_fn: Callable[[Any], str | None] | None = None


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
        key: Any = None,
    ) -> None:
        """Initialize the entity for the device with the given MAC."""

        super().__init__(coordinator)

        self.entity_description = description
        self._mac = mac
        self._key = key

        unique_id_fn = description.unique_id_fn
        unique_id_name = (
            description.unique_id_name
            if unique_id_fn is None
            else unique_id_fn(key)
        )
        device_mac = format_mac(str(mac))
        self._attr_unique_id = to_unique_id(f"{device_mac}_{unique_id_name}")
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_mac)})
        if (device_info_fn := description.device_info_fn) is not None:
            via_device_id = dr.async_get_device_id_by_identifier(
                coordinator.hass,
                (DOMAIN, device_mac),
                config_entry_id=coordinator.config_entry.entry_id,
            )
            self._attr_device_info = device_info_fn(
                via_device_id, key, self._device_data
            )

        self._placeholders = dict(description.translation_placeholders or {})
        if (placeholders_fn := description.placeholders_fn) is not None:
            self._placeholders.update(placeholders_fn(key))
            self._attr_translation_placeholders = self._placeholders
        self._update_name()

    @property
    def _device_data(self) -> Any:
        """Return the data of this entity, of its key when it has one."""

        data = _get_data(self.coordinator, self.entity_description, self._mac)
        item_fn = self.entity_description.item_fn
        if item_fn is None or data is None:
            return data

        return item_fn(data, self._key)

    def _update_name(self) -> None:
        """Fill the name placeholder from its data, when it names itself."""

        description = self.entity_description
        name_fn = description.name_fn
        if name_fn is None or (data := self._device_data) is None:
            return

        # A missing name keeps the last one
        if (name := name_fn(data)) is not None:
            self._attr_translation_placeholders = {
                **self._placeholders,
                "name": name,
            }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Rename the entity from the new data before writing its state."""

        self._update_name()
        super()._handle_coordinator_update()

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


class ARToggleEntity(AREntity):
    """AsusRouter entity turned on and off."""

    entity_description: ARToggleDescription

    @property
    def is_on(self) -> bool | None:
        """Return the entity state."""

        value: bool | None = self.entity_description.value_fn(
            self._device_data
        )
        return value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""

        await self._async_run_action(
            self.entity_description.action_fn(True, self._device_data)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""

        await self._async_run_action(
            self.entity_description.action_fn(False, self._device_data)
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
    entity_type: Callable[..., EntityT],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the entities of the device and its AiMesh nodes as they appear."""

    runtime_data = config_entry.runtime_data
    device_mac = runtime_data.bridge.identity.mac
    targets = _get_targets(runtime_data, descriptions)
    pending = [target for target in targets if target[1].keys_fn is None]
    # The entities of every key read so far, by the target reading them
    keyed: list[
        tuple[
            tuple[ARCoordinator[Any], DescriptionT, MacAddress],
            dict[Any, EntityT],
        ]
    ] = [(target, {}) for target in targets if target[1].keys_fn is not None]
    # New keys can appear on every update
    keyed_coordinators = {target[0] for target, _ in keyed}
    listeners: dict[ARCoordinator[Any], CALLBACK_TYPE] = {}

    @callback
    def _async_add_entities() -> None:
        """Add the entities known to exist by now."""

        nonlocal pending

        entities = _async_update_keys(config_entry, keyed, entity_type)
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
        waited = {target[0] for target in pending} | keyed_coordinators
        for coordinator in listeners.keys() - waited:
            listeners.pop(coordinator)()

    _async_add_entities()

    # A coordinator without entities polls only while something waits for it
    for coordinator in {target[0] for target in pending} | keyed_coordinators:
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


def _get_keys(
    coordinator: ARCoordinator[Any],
    description: AREntityDescription,
    mac: MacAddress,
) -> set[Any] | None:
    """Get the keys the device with the given MAC reports, None unread."""

    keys_fn = description.keys_fn
    # A failed read keeps the entities, as an offline node does
    if (
        keys_fn is None
        or coordinator.data is None
        or not coordinator.last_update_success
        or (data := _get_data(coordinator, description, mac)) is None
    ):
        return None

    return set(keys_fn(data))


@callback
def _async_update_keys[DescriptionT: AREntityDescription, EntityT: AREntity](
    config_entry: ARConfigEntry,
    keyed: list[
        tuple[
            tuple[ARCoordinator[Any], DescriptionT, MacAddress],
            dict[Any, EntityT],
        ]
    ],
    entity_type: Callable[..., EntityT],
) -> list[EntityT]:
    """Get the entities of new keys, removing those of missing ones."""

    entities: list[EntityT] = []
    for target, known in keyed:
        keys = _get_keys(*target)
        if keys is None:
            continue

        for key in keys - known.keys():
            known[key] = entity_type(*target, key)
            entities.append(known[key])
        # An empty read is no proof that every key is gone
        if target[1].remove_missing and keys:
            for key in known.keys() - keys:
                _async_remove_entity(config_entry, known.pop(key))

    return entities


@callback
def _async_remove_entity(
    config_entry: ARConfigEntry, entity: AREntity
) -> None:
    """Remove an entity and its registry entry."""

    registry = er.async_get(entity.coordinator.hass)
    for entry in er.async_entries_for_config_entry(
        registry, config_entry.entry_id
    ):
        # Removing the entry removes the entity
        if entry.unique_id == entity.unique_id:
            registry.async_remove(entry.entity_id)
