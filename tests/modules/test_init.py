"""Tests for the modules module."""

from __future__ import annotations

import pytest

from custom_components.asusrouter.entity import AREntityDescription
from custom_components.asusrouter.modules import DESCRIPTIONS


@pytest.mark.parametrize(
    "description",
    [description for description in DESCRIPTIONS if description.name_fn],
    ids=lambda description: description.key,
)
def test_name_placeholder(description: AREntityDescription) -> None:
    """Test that a self-naming entity has a name before its data is read."""

    # A keyed entity gets its default name from its key
    assert description.placeholders_fn is not None or "name" in (
        description.translation_placeholders or {}
    )


@pytest.mark.parametrize(
    "description",
    [description for description in DESCRIPTIONS if description.keys_fn],
    ids=lambda description: description.key,
)
def test_keyed(description: AREntityDescription) -> None:
    """Test that a keyed entity reads its key and builds its unique_id."""

    assert description.item_fn is not None
    assert description.unique_id_fn is not None
    assert not description.unique_id_name


@pytest.mark.parametrize(
    "description",
    [description for description in DESCRIPTIONS if not description.keys_fn],
    ids=lambda description: description.key,
)
def test_single(description: AREntityDescription) -> None:
    """Test that a single entity has its unique_id name."""

    assert description.unique_id_name
    assert description.item_fn is None
    assert description.unique_id_fn is None
