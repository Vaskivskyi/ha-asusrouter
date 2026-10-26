"""AsusRouter coordinator module."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from asusrouter import AsusRouterError
from asusrouter.modules.source import ARDataSource
from asusrouter.tools.identifiers import MacAddress
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .errors import is_auth_error

if TYPE_CHECKING:
    from . import ARConfigEntry
    from .entity import AREntityDescription

_LOGGER = logging.getLogger(__name__)


class ARCoordinator(DataUpdateCoordinator[dict[Any, Any]]):
    """Coordinator of a single library data source."""

    config_entry: ARConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ARConfigEntry,
        source: ARDataSource,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN} {source}",
            update_interval=update_interval,
            # Skip entity updates when the data did not change
            always_update=False,
        )

        self._source = source

    async def _async_update_data(self) -> dict[Any, Any]:
        """Fetch the source from the device."""

        api = self.config_entry.runtime_data.bridge.api

        try:
            data = await api.async_fetch_data(self._source)
        except AsusRouterError as ex:
            if is_auth_error(ex):
                # Reconnecting cannot help, requires new credentials
                raise ConfigEntryAuthFailed(
                    "Device refused the saved credentials"
                ) from ex
            raise UpdateFailed(f"Cannot fetch `{self._source}`") from ex

        # The library returns nothing when no fresh data is available
        content: dict[Any, Any] = (data or {}).get(self._source) or {}
        return content


async def async_setup_coordinators(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    descriptions: Iterable[AREntityDescription],
    nodes: Iterable[MacAddress] = (),
) -> dict[ARDataSource, ARCoordinator]:
    """Set up a coordinator for every source of the descriptions."""

    descriptions = tuple(descriptions)
    nodes = tuple(nodes)

    requests = [
        (description.source, description.update_interval)
        for description in descriptions
    ]
    node_requests = [
        (description.node_source(mac), description.update_interval)
        for description in descriptions
        if description.node_source is not None
        for mac in nodes
    ]
    node_sources = {source for source, _ in node_requests}

    # A shared source polls at the shortest interval requested
    intervals: dict[ARDataSource, timedelta] = {}
    for source, interval in (*requests, *node_requests):
        intervals[source] = min(intervals.get(source, interval), interval)

    coordinators = {
        source: ARCoordinator(hass, config_entry, source, interval)
        for source, interval in intervals.items()
    }

    # Let the library decide how many fetches run at once
    results = await asyncio.gather(
        *(
            # A failed node leaves only its own entities unavailable
            coordinator.async_refresh()
            if source in node_sources
            else coordinator.async_config_entry_first_refresh()
            for source, coordinator in coordinators.items()
        ),
        return_exceptions=True,
    )

    errors = [
        result for result in results if isinstance(result, BaseException)
    ]
    if errors:
        # New credentials are required whatever else failed
        raise next(
            (
                error
                for error in errors
                if isinstance(error, ConfigEntryAuthFailed)
            ),
            errors[0],
        )

    return coordinators
