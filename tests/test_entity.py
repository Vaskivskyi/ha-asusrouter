"""Tests for the entity module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouterError
from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
)
from asusrouter.tools.identifiers import MacAddress
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import pytest

from custom_components.asusrouter import ARRuntimeData, entity as entity_module
from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.entity import (
    AREntity,
    AREntityDescription,
    ARToggleDescription,
    ARToggleEntity,
    _async_remove_entity,
    async_setup_entities,
    get_supported,
)

pytestmark = pytest.mark.asyncio

MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
OTHER_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:03")
OWNED_NODE_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:04")
DEVICE_DATA = {"key": "value"}

SOURCE = ARSystemStatusSourceUniversal


def _get_description(**kwargs: Any) -> AREntityDescription:
    """Create an entity description."""

    return AREntityDescription(
        key="test",
        translation_key="test",
        source=SOURCE,
        update_interval=timedelta(seconds=30),
        value_fn=Mock(),
        **{"unique_id_name": "Test Name", **kwargs},
    )


def _get_coordinator(data: dict[Any, Any] | None = None) -> Mock:
    """Create a coordinator reading devices from the data."""

    data = {MAC: DEVICE_DATA} if data is None else data

    return Mock(data=data, get_device=Mock(side_effect=data.get))


def _get_entity(
    data: dict[Any, Any] | None = None,
    success: bool = True,
    **kwargs: Any,
) -> AREntity:
    """Create an entity of the test device."""

    coordinator = _get_coordinator(data)
    coordinator.last_update_success = success

    return AREntity(coordinator, _get_description(**kwargs), MAC)


# ---------------------------
# ENTITY -->
# ---------------------------


async def test_init() -> None:
    """Test that the entity is tied to its device by MAC."""

    entity = _get_entity()

    assert entity.unique_id == "aa:bb:cc:dd:ee:01_test_name"
    assert entity.device_info == {
        "identifiers": {(DOMAIN, "aa:bb:cc:dd:ee:01")}
    }
    assert entity.has_entity_name is True


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({MAC: DEVICE_DATA}, DEVICE_DATA),
        # Another device only
        ({OTHER_MAC: DEVICE_DATA}, None),
    ],
)
async def test_device_data(data: dict[Any, Any], expected: Any) -> None:
    """Test that the entity reads the data of its own device."""

    assert _get_entity(data)._device_data == expected


async def test_device_data_fn() -> None:
    """Test that the entity can read the whole coordinator data."""

    data = {OTHER_MAC: DEVICE_DATA}
    data_fn = Mock(return_value=DEVICE_DATA)

    assert _get_entity(data, data_fn=data_fn)._device_data is DEVICE_DATA
    data_fn.assert_called_once_with(data)


def _get_keyed_entity(
    data: dict[Any, Any] | None = None, **kwargs: Any
) -> AREntity:
    """Create the entity of the key "a" of the test device."""

    description = _get_description(
        unique_id_name="",
        keys_fn=lambda data: data,
        item_fn=lambda data, key: data.get(key),
        unique_id_fn=lambda key: f"Test {key}",
        placeholders_fn=lambda key: {"key": key},
        **kwargs,
    )

    return AREntity(_get_coordinator(data), description, MAC, "a")


async def test_device_info_fn() -> None:
    """Test that a key gets its own device, linked to the device."""

    device_info = DeviceInfo(name="Client")
    device_info_fn = Mock(return_value=device_info)
    coordinator = _get_coordinator({MAC: {"a": "item"}})
    description = _get_description(
        unique_id_name="",
        keys_fn=lambda data: data,
        item_fn=lambda data, key: data.get(key),
        unique_id_fn=lambda key: f"Test {key}",
        device_info_fn=device_info_fn,
    )

    with patch.object(
        entity_module.dr,
        "async_get_device_id_by_identifier",
        return_value="device",
    ) as get_device_id:
        entity = AREntity(coordinator, description, MAC, "a")

    get_device_id.assert_called_once_with(
        coordinator.hass,
        (DOMAIN, "aa:bb:cc:dd:ee:01"),
        config_entry_id=coordinator.config_entry.entry_id,
    )
    device_info_fn.assert_called_once_with("device", "a", "item")
    assert entity.device_info is device_info


async def test_keyed_init() -> None:
    """Test that a keyed entity builds its unique_id and name from its key."""

    entity = _get_keyed_entity(translation_placeholders={"unit": "1"})

    assert entity.unique_id == "aa:bb:cc:dd:ee:01_test_a"
    assert entity.translation_placeholders == {"unit": "1", "key": "a"}


async def test_keyed_name() -> None:
    """Test that the name of a keyed entity keeps the key placeholders."""

    entity = _get_keyed_entity(
        {MAC: {"a": "item"}}, name_fn=Mock(return_value="Example")
    )

    assert entity.translation_placeholders == {"key": "a", "name": "Example"}


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({MAC: {"a": "item"}}, "item"),
        ({MAC: {"b": "item"}}, None),
        # The device itself is not read
        ({OTHER_MAC: {"a": "item"}}, None),
    ],
)
async def test_keyed_device_data(data: dict[Any, Any], expected: Any) -> None:
    """Test that a keyed entity reads the data of its key."""

    assert _get_keyed_entity(data)._device_data == expected


@pytest.mark.parametrize(
    ("data", "success", "expected"),
    [
        ({MAC: DEVICE_DATA}, True, True),
        ({OTHER_MAC: DEVICE_DATA}, True, False),
        ({MAC: DEVICE_DATA}, False, False),
    ],
)
async def test_available(
    data: dict[Any, Any], success: bool, expected: bool
) -> None:
    """Test that the entity is available only with data of its device."""

    assert _get_entity(data, success=success).available is expected


@pytest.mark.parametrize("live", [True, False])
async def test_available_fn(live: bool) -> None:
    """Test that the entity is available only with a live value."""

    available_fn = Mock(return_value=live)

    assert _get_entity(available_fn=available_fn).available is live
    available_fn.assert_called_once_with(DEVICE_DATA)


async def test_extra_state_attributes() -> None:
    """Test that the attributes are read from the device data."""

    attributes_fn = Mock(return_value={"attribute": "value"})
    entity = _get_entity(attributes_fn=attributes_fn)

    assert entity.extra_state_attributes == {"attribute": "value"}
    attributes_fn.assert_called_once_with(DEVICE_DATA)
    assert _get_entity().extra_state_attributes is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Example", {"unit": "1", "name": "Example"}), (None, {"unit": "1"})],
)
async def test_name(name: str | None, expected: dict[str, str]) -> None:
    """Test that the name placeholder is filled from the data."""

    name_fn = Mock(return_value=name)
    entity = _get_entity(
        name_fn=name_fn, translation_placeholders={"unit": "1"}
    )

    name_fn.assert_called_once_with(DEVICE_DATA)
    assert not hasattr(entity, "_attr_name")
    assert entity.translation_placeholders == expected


async def test_name_without_placeholders() -> None:
    """Test that a description without placeholders gets only the name."""

    entity = _get_entity(name_fn=Mock(return_value="Example"))

    assert entity.translation_placeholders == {"name": "Example"}


async def test_name_unread() -> None:
    """Test that an entity without data keeps its translated name."""

    name_fn = Mock()
    entity = _get_entity(data={}, name_fn=name_fn)

    name_fn.assert_not_called()
    assert not hasattr(entity, "_attr_translation_placeholders")


async def test_name_update() -> None:
    """Test that an entity is renamed before its state is written."""

    entity = _get_entity(name_fn=Mock(side_effect=["Old", "New", None]))

    with patch.object(
        CoordinatorEntity, "_handle_coordinator_update"
    ) as handle_update:
        entity._handle_coordinator_update()
        assert entity.translation_placeholders == {"name": "New"}
        handle_update.assert_called_once()

        # A missing name keeps the last one
        handle_update.reset_mock()
        entity._handle_coordinator_update()
        assert entity.translation_placeholders == {"name": "New"}
        handle_update.assert_called_once()


def _get_action_entity(run_action: AsyncMock) -> AREntity:
    """Create an entity whose device runs actions with the given mock."""

    entity = _get_entity()
    coordinator: Any = entity.coordinator
    coordinator.config_entry.runtime_data.bridge.api.async_run_action = (
        run_action
    )
    coordinator.async_refresh = AsyncMock()

    return entity


@pytest.mark.parametrize("refresh", [True, False])
async def test_run_action(refresh: bool) -> None:
    """Test that an applied action is read back right away when asked."""

    run_action = AsyncMock(return_value=True)
    entity = _get_action_entity(run_action)
    action = Mock()

    await entity._async_run_action(action, refresh=refresh)

    run_action.assert_awaited_once_with(action)
    coordinator: Any = entity.coordinator
    assert coordinator.async_refresh.await_count == int(refresh)


@pytest.mark.parametrize(
    ("run_action", "translation_key"),
    [
        (AsyncMock(side_effect=AsusRouterError()), "action_failed"),
        (AsyncMock(return_value=False), "action_not_applied"),
    ],
)
async def test_run_action_failed(
    run_action: AsyncMock, translation_key: str
) -> None:
    """Test that a failed action raises and reads nothing back."""

    entity = _get_action_entity(run_action)
    entity.entity_id = "light.test"

    with pytest.raises(HomeAssistantError) as error:
        await entity._async_run_action(Mock())

    assert error.value.translation_domain == DOMAIN
    assert error.value.translation_key == translation_key
    assert error.value.translation_placeholders == {"entity": "light.test"}

    coordinator: Any = entity.coordinator
    coordinator.async_refresh.assert_not_awaited()


def _get_toggle_entity(**kwargs: Any) -> ARToggleEntity:
    """Create an entity of the test device turned on and off."""

    description = ARToggleDescription(
        key="test",
        translation_key="test",
        source=SOURCE,
        update_interval=timedelta(seconds=30),
        unique_id_name="Test Name",
        **{"value_fn": Mock(), "action_fn": Mock(), **kwargs},
    )

    return ARToggleEntity(_get_coordinator(), description, MAC)


async def test_toggle_is_on() -> None:
    """Test that the state is read from the device data."""

    value_fn = Mock(return_value=True)
    entity = _get_toggle_entity(value_fn=value_fn)

    assert entity.is_on is True
    value_fn.assert_called_once_with(DEVICE_DATA)


@pytest.mark.parametrize(("method", "state"), [("on", True), ("off", False)])
async def test_toggle_turn(method: str, state: bool) -> None:
    """Test that turning the entity runs its action."""

    action_fn = Mock()
    entity = _get_toggle_entity(action_fn=action_fn)

    with patch.object(
        ARToggleEntity, "_async_run_action", AsyncMock()
    ) as run_action:
        await getattr(entity, f"async_turn_{method}")()

    action_fn.assert_called_once_with(state, DEVICE_DATA)
    run_action.assert_awaited_once_with(action_fn.return_value)


# ---------------------------
# <-- ENTITY
# ---------------------------

# ---------------------------
# ENTITIES -->
# ---------------------------


async def test_get_supported() -> None:
    """Test that only the descriptions the device supports are kept."""

    bridge = Mock()
    supported_fn = Mock(return_value=True)
    every = _get_description()
    supported = _get_description(supported_fn=supported_fn)
    unsupported = _get_description(supported_fn=Mock(return_value=False))

    result = get_supported([every, supported, unsupported], bridge)

    assert result == [every, supported]
    supported_fn.assert_called_once_with(bridge)


def _get_runtime_coordinator(data: dict[Any, Any]) -> Mock:
    """Create a coordinator that can be listened to."""

    coordinator = _get_coordinator(data)
    coordinator.async_add_listener = Mock(return_value=Mock())

    return coordinator


def _get_entry(
    mac: MacAddress | None = MAC,
    data: dict[Any, Any] | None = None,
    node_data: dict[Any, Any] | None = None,
) -> Mock:
    """Create the entry of a router with one node of its own."""

    bridge = Mock()
    bridge.identity.mac = mac

    entry = Mock()
    entry.runtime_data = ARRuntimeData(
        bridge=bridge,
        coordinators={
            SOURCE: _get_runtime_coordinator(
                {MAC: DEVICE_DATA} if data is None else data
            ),
            ARSystemStatusSource(target=NODE_MAC): _get_runtime_coordinator(
                {NODE_MAC: DEVICE_DATA} if node_data is None else node_data
            ),
        },
        mesh=frozenset({NODE_MAC, OWNED_NODE_MAC}),
        nodes=[NODE_MAC],
    )

    return entry


def _get_entity_args(*args: Any) -> Any:
    """Stand in for an entity, keeping what it was created with."""

    return args


def _setup_entities(
    entry: Mock, descriptions: list[AREntityDescription]
) -> list[Any]:
    """Set up the entities, returning the ones added in each call."""

    add_entities = Mock()
    async_setup_entities(entry, descriptions, _get_entity_args, add_entities)

    return [call.args[0] for call in add_entities.call_args_list]


def _get_listener(coordinator: Mock) -> Any:
    """Get the only listener added to the coordinator."""

    coordinator.async_add_listener.assert_called_once()
    return coordinator.async_add_listener.call_args.args[0]


async def test_setup_entities() -> None:
    """Test that the device and its own nodes get their entities."""

    entry = _get_entry()
    coordinators = entry.runtime_data.coordinators
    node_coordinator = coordinators[ARSystemStatusSource(target=NODE_MAC)]
    device = _get_description()
    node = _get_description(node_source=ARSystemStatusSource)

    assert _setup_entities(entry, [device, node]) == [
        [
            (coordinators[SOURCE], device, MAC),
            (coordinators[SOURCE], node, MAC),
            (node_coordinator, node, NODE_MAC),
        ]
    ]
    # Nothing waits, so nothing is listened to
    for coordinator in coordinators.values():
        coordinator.async_add_listener.assert_not_called()


async def test_setup_entities_mesh() -> None:
    """Test that a source of the whole mesh serves every node."""

    entry = _get_entry()
    coordinator = entry.runtime_data.coordinators[SOURCE]
    description = _get_description(
        on_device=False, node_source=lambda _: SOURCE, covers_mesh=True
    )

    (entities,) = _setup_entities(entry, [description])

    assert sorted(entities, key=lambda args: str(args[2])) == [
        (coordinator, description, NODE_MAC),
        (coordinator, description, OWNED_NODE_MAC),
    ]


async def test_setup_entities_exists() -> None:
    """Test that only the entities the device reports are created."""

    entry = _get_entry()
    coordinator = entry.runtime_data.coordinators[SOURCE]
    exists_fn = Mock(side_effect=[True, False])
    reported = _get_description(exists_fn=exists_fn)
    missing = _get_description(exists_fn=exists_fn)

    assert _setup_entities(entry, [reported, missing]) == [
        [(coordinator, reported, MAC)]
    ]
    exists_fn.assert_called_with(DEVICE_DATA)
    # The device was read, so the missing entity never appears
    coordinator.async_add_listener.assert_not_called()


async def test_setup_entities_exists_no_device() -> None:
    """Test that the device not in its read data gets no entity."""

    entry = _get_entry(data={OTHER_MAC: DEVICE_DATA})
    coordinator = entry.runtime_data.coordinators[SOURCE]
    exists_fn = Mock()

    assert (
        _setup_entities(entry, [_get_description(exists_fn=exists_fn)]) == []
    )
    exists_fn.assert_not_called()
    coordinator.async_add_listener.assert_not_called()


async def test_setup_entities_unread() -> None:
    """Test that the entities of an unread source appear once it is read."""

    entry = _get_entry()
    coordinator = entry.runtime_data.coordinators[SOURCE]
    coordinator.data = None
    reported = _get_description(exists_fn=Mock(return_value=True))
    missing = _get_description(exists_fn=Mock(return_value=False))
    add_entities = Mock()

    async_setup_entities(
        entry, [reported, missing], _get_entity_args, add_entities
    )

    add_entities.assert_not_called()
    # Listened to once for both entities
    listener = _get_listener(coordinator)

    # Still nothing read
    listener()
    add_entities.assert_not_called()

    coordinator.data = {MAC: DEVICE_DATA}
    listener()
    add_entities.assert_called_once_with([(coordinator, reported, MAC)])
    # Nothing waits any more
    coordinator.async_add_listener.return_value.assert_called_once_with()

    # Every entity was decided, none is added twice
    listener()
    add_entities.assert_called_once()


async def test_setup_entities_node_offline() -> None:
    """Test that the entities of an offline node appear once it is online."""

    entry = _get_entry(data={MAC: DEVICE_DATA})
    coordinator = entry.runtime_data.coordinators[SOURCE]
    description = _get_description(
        node_source=lambda _: SOURCE, exists_fn=Mock(return_value=True)
    )
    add_entities = Mock()

    async_setup_entities(entry, [description], _get_entity_args, add_entities)

    add_entities.assert_called_once_with([(coordinator, description, MAC)])
    listener = _get_listener(coordinator)

    coordinator.data[NODE_MAC] = DEVICE_DATA
    listener()

    add_entities.assert_called_with([(coordinator, description, NODE_MAC)])
    coordinator.async_add_listener.return_value.assert_called_once_with()


async def test_setup_entities_unload() -> None:
    """Test that the coordinators are no longer listened to on unload."""

    entry = _get_entry()
    coordinator = entry.runtime_data.coordinators[SOURCE]
    coordinator.data = None

    _setup_entities(entry, [_get_description(exists_fn=Mock())])

    remove_listener = coordinator.async_add_listener.return_value
    (unload,) = entry.async_on_unload.call_args.args
    unload()
    remove_listener.assert_called_once_with()

    # Removed only once
    unload()
    remove_listener.assert_called_once_with()


async def test_setup_entities_unsupported() -> None:
    """Test that an unsupported description gets no entity."""

    description = _get_description(supported_fn=Mock(return_value=False))

    assert _setup_entities(_get_entry(), [description]) == []


async def test_setup_entities_without_mac() -> None:
    """Test that no entity is created for a device without a MAC."""

    assert _setup_entities(_get_entry(None), [_get_description()]) == []


def _get_keyed_description(**kwargs: Any) -> AREntityDescription:
    """Create a description of an entity for each key of the device data."""

    return _get_description(
        unique_id_name="",
        keys_fn=lambda data: data,
        item_fn=lambda data, key: data.get(key),
        unique_id_fn=lambda key: f"Test {key}",
        **kwargs,
    )


def _setup_keyed(
    description: AREntityDescription, data: dict[Any, Any] | None
) -> tuple[Mock, Mock, Any, Mock]:
    """Set up the keyed entities, removing none for real."""

    entry = _get_entry(data={MAC: data} if data is not None else {})
    coordinator = entry.runtime_data.coordinators[SOURCE]
    coordinator.last_update_success = True

    def _get_device(mac: MacAddress) -> Any:
        """Read whatever the data is by then."""

        return (coordinator.data or {}).get(mac)

    coordinator.get_device = Mock(side_effect=_get_device)
    if data is None:
        coordinator.data = None
    add_entities = Mock()

    with patch.object(entity_module, "_async_remove_entity") as remove:
        async_setup_entities(
            entry, [description], _get_entity_args, add_entities
        )
    listener = _get_listener(coordinator)

    return coordinator, add_entities, listener, remove


async def test_setup_entities_keyed() -> None:
    """Test that every key gets its entity, also those appearing later."""

    description = _get_keyed_description()
    coordinator, add_entities, listener, _ = _setup_keyed(
        description, {"a": 1, "b": 2}
    )

    (entities,) = add_entities.call_args.args
    assert sorted(entities, key=lambda args: args[3]) == [
        (coordinator, description, MAC, "a"),
        (coordinator, description, MAC, "b"),
    ]

    coordinator.data[MAC]["c"] = 3
    listener()
    add_entities.assert_called_with([(coordinator, description, MAC, "c")])

    # Known keys are not added twice, and the listener stays for new ones
    add_entities.reset_mock()
    listener()
    add_entities.assert_not_called()
    coordinator.async_add_listener.return_value.assert_not_called()


async def test_setup_entities_keyed_unread() -> None:
    """Test that the keys are read once the source is read."""

    description = _get_keyed_description()
    coordinator, add_entities, listener, _ = _setup_keyed(description, None)

    add_entities.assert_not_called()

    # A failed read is not read
    coordinator.data = {MAC: {"a": 1}}
    coordinator.last_update_success = False
    listener()
    add_entities.assert_not_called()

    # Nor is a device missing from the data, as an offline node
    coordinator.last_update_success = True
    coordinator.data = {OTHER_MAC: {"a": 1}}
    listener()
    add_entities.assert_not_called()

    coordinator.data = {MAC: {"a": 1}}
    listener()
    add_entities.assert_called_once_with(
        [(coordinator, description, MAC, "a")]
    )


@pytest.mark.parametrize(
    ("remove_missing", "data", "removed"),
    [
        (True, {"a": 1}, ("b", 2)),
        # An empty read is no proof that every key is gone
        (True, {}, None),
        (False, {"a": 1}, None),
    ],
)
async def test_setup_entities_keyed_missing(
    remove_missing: bool, data: dict[str, int], removed: Any
) -> None:
    """Test that the entity of a missing key is removed only when asked."""

    description = _get_keyed_description(remove_missing=remove_missing)
    coordinator, _, listener, _ = _setup_keyed(description, {"a": 1, "b": 2})
    coordinator.data[MAC] = data

    with patch.object(entity_module, "_async_remove_entity") as remove:
        listener()

    if removed is None:
        remove.assert_not_called()
    else:
        (entry, entity) = remove.call_args.args
        assert entry is not None
        assert entity == (coordinator, description, MAC, removed[0])


async def test_remove_entity() -> None:
    """Test that an entity is removed with its registry entry."""

    entry = Mock(entry_id="entry")
    entity = Mock(unique_id="unique")
    registry = Mock()
    entries = [
        Mock(unique_id="other", entity_id="sensor.other"),
        Mock(unique_id="unique", entity_id="sensor.unique"),
    ]

    with (
        patch.object(entity_module.er, "async_get", return_value=registry),
        patch.object(
            entity_module.er,
            "async_entries_for_config_entry",
            return_value=entries,
        ) as entries_for,
    ):
        _async_remove_entity(entry, entity)

    entries_for.assert_called_once_with(registry, "entry")
    registry.async_remove.assert_called_once_with("sensor.unique")


# ---------------------------
# <-- ENTITIES
# ---------------------------
