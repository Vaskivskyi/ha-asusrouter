"""Tests for the entity module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import Mock

from asusrouter.modules.system_status import ARSystemStatusSourceUniversal
from asusrouter.tools.identifiers import MacAddress
import pytest

from custom_components.asusrouter.const import DOMAIN
from custom_components.asusrouter.entity import AREntity, AREntityDescription

pytestmark = pytest.mark.asyncio

MAC = MacAddress.from_value("AA:BB:CC:DD:EE:01")
OTHER_MAC = MacAddress.from_value("AA:BB:CC:DD:EE:02")
DEVICE_DATA = {"key": "value"}


def _get_description() -> AREntityDescription:
    """Create an entity description."""

    return AREntityDescription(
        key="test",
        translation_key="test",
        source=ARSystemStatusSourceUniversal,
        update_interval=timedelta(seconds=30),
        unique_id_name="Test Name",
        value_fn=Mock(),
    )


def _get_entity(
    data: dict[Any, Any] | None = None, success: bool = True
) -> AREntity:
    """Create an entity of the test device."""

    coordinator = Mock(
        data={MAC: DEVICE_DATA} if data is None else data,
        last_update_success=success,
    )

    return AREntity(coordinator, _get_description(), MAC)


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
        ({OTHER_MAC: DEVICE_DATA}, {}),
    ],
)
async def test_device_data(
    data: dict[Any, Any], expected: dict[Any, Any]
) -> None:
    """Test that the entity reads the data of its own device."""

    assert _get_entity(data)._device_data == expected


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
