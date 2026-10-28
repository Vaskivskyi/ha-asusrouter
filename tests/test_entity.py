"""Tests for the entity module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import Mock

from asusrouter.modules.system_status import (
    ARSystemStatusSource,
    ARSystemStatusSourceUniversal,
)
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter import ARRuntimeData
from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.entity import (
    AREntity,
    AREntityDescription,
    get_entities,
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


def _get_runtime_data(mac: MacAddress | None = MAC) -> ARRuntimeData:
    """Create the runtime data of a router with one node of its own."""

    bridge = Mock()
    bridge.identity.mac = mac

    return ARRuntimeData(
        bridge=bridge,
        coordinators={
            SOURCE: Mock(),
            ARSystemStatusSource(target=NODE_MAC): Mock(),
        },
        mesh=frozenset({NODE_MAC, OWNED_NODE_MAC}),
        nodes=[NODE_MAC],
    )


def _get_entity_args(*args: Any) -> Any:
    """Stand in for an entity, keeping what it was created with."""

    return args


async def test_get_entities() -> None:
    """Test that the device and its own nodes get their entities."""

    runtime_data = _get_runtime_data()
    coordinators = runtime_data.coordinators
    device = _get_description()
    node = _get_description(node_source=ARSystemStatusSource)

    entities = get_entities(runtime_data, [device, node], _get_entity_args)

    assert entities == [
        (coordinators[SOURCE], device, MAC),
        (coordinators[SOURCE], node, MAC),
        (coordinators[ARSystemStatusSource(target=NODE_MAC)], node, NODE_MAC),
    ]


async def test_get_entities_mesh() -> None:
    """Test that a source of the whole mesh serves every node."""

    runtime_data = _get_runtime_data()
    coordinator = runtime_data.coordinators[SOURCE]
    description = _get_description(
        on_device=False, node_source=lambda _: SOURCE, covers_mesh=True
    )

    entities = get_entities(runtime_data, [description], _get_entity_args)

    assert sorted(entities, key=lambda args: str(args[2])) == [
        (coordinator, description, NODE_MAC),
        (coordinator, description, OWNED_NODE_MAC),
    ]


async def test_get_entities_exists() -> None:
    """Test that only the entities the device reports are created."""

    runtime_data = _get_runtime_data()
    coordinator = Mock(get_device=Mock(return_value=DEVICE_DATA))
    runtime_data.coordinators[SOURCE] = coordinator
    exists_fn = Mock(side_effect=[True, False])
    reported = _get_description(exists_fn=exists_fn)
    missing = _get_description(exists_fn=exists_fn)

    entities = get_entities(
        runtime_data, [reported, missing], _get_entity_args
    )

    assert entities == [(coordinator, reported, MAC)]
    exists_fn.assert_called_with(DEVICE_DATA)


async def test_get_entities_exists_no_device() -> None:
    """Test that no entity is created when the device is not in the data."""

    runtime_data = _get_runtime_data()
    runtime_data.coordinators[SOURCE] = Mock(
        get_device=Mock(return_value=None)
    )
    exists_fn = Mock()

    assert (
        get_entities(
            runtime_data,
            [_get_description(exists_fn=exists_fn)],
            _get_entity_args,
        )
        == []
    )
    exists_fn.assert_not_called()


async def test_get_entities_exists_unread(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an unread source gets its entities only on reload."""

    runtime_data = _get_runtime_data()
    coordinator = runtime_data.coordinators[SOURCE]
    coordinator.data = None
    coordinator.name = "source"
    description = _get_description(exists_fn=Mock())

    entities = get_entities(
        runtime_data, [description, description], _get_entity_args
    )

    assert entities == []
    # Reported once per source
    assert caplog.text.count("Cannot read `source` at setup") == 1


async def test_get_entities_unsupported() -> None:
    """Test that an unsupported description gets no entity."""

    description = _get_description(supported_fn=Mock(return_value=False))

    assert (
        get_entities(_get_runtime_data(), [description], _get_entity_args)
        == []
    )


async def test_get_entities_without_mac() -> None:
    """Test that no entity is created for a device without a MAC."""

    description = _get_description()

    assert (
        get_entities(_get_runtime_data(None), [description], _get_entity_args)
        == []
    )


# ---------------------------
# <-- ENTITIES
# ---------------------------
