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

    assert "name" in (description.translation_placeholders or {})
