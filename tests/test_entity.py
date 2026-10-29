"""Tests for the entity module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock

from asusrouter import AsusRouterError
from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
)
from asusrouter.tools.identifiers import MacAddress
from homeassistant.exceptions import HomeAssistantError
import pytest

from custom_components.asusrouter import ARRuntimeData
from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.entity import (
    AREntity,
    AREntityDescription,
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
        unique_id_name="Test Name",
        value_fn=Mock(),
        **kwargs,
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


# ---------------------------
# <-- ENTITIES
# ---------------------------
