"""Helpers for unit test modules."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import AsyncMock, Mock

AsyncPatch = Callable[..., AsyncMock]
SyncPatch = Callable[..., Mock]
