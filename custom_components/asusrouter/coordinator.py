"""AsusRouter coordinator module."""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from asusrouter import AsusRouterError
from asusrouter.modules.aimesh import (
    ARAiMeshNode,
    ARAiMeshSource,
    ARAiMeshTopology,
)
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


class ARCoordinator[DataT](DataUpdateCoordinator[DataT], ABC):
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

    async def _async_update_data(self) -> DataT:
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
        return self._get_content((data or {}).get(self._source))

    @abstractmethod
    def _get_content(self, content: Any) -> DataT:
        """Get the coordinator data from the fetched source content."""

    @abstractmethod
    def get_device(self, mac: MacAddress) -> Any:
        """Get the data of the device with the given MAC, None when absent."""


class ARStateCoordinator(ARCoordinator[dict[Any, Any]]):
    """Coordinator of a source reporting its state as a dict."""

    def _get_content(self, content: Any) -> dict[Any, Any]:
        """Get the state, empty when nothing was fetched."""

        state: dict[Any, Any] = content or {}
        return state

    def get_device(self, mac: MacAddress) -> Any:
        """Get the state of the device with the given MAC."""

        return self.data.get(mac)


class ARTopologyCoordinator(ARCoordinator[ARAiMeshTopology]):
    """Coordinator of the AiMesh topology."""

    def _get_content(self, content: Any) -> ARAiMeshTopology:
        """Get the topology, failing when nothing was fetched."""

        # The device lists itself, so an empty topology is a failed read
        # HA keeps the last topology, so the mesh never looks gone
        if not isinstance(content, ARAiMeshTopology) or not content.nodes:
            raise UpdateFailed(f"No topology in `{self._source}`")

        return content

    def get_device(self, mac: MacAddress) -> ARAiMeshNode | None:
        """Get the AiMesh node with the given MAC."""

        return self.data.nodes.get(mac)


# Sources whose content is not a state dict
_COORDINATORS: dict[type[ARDataSource], type[ARCoordinator[Any]]] = {
    ARAiMeshSource: ARTopologyCoordinator,
}


async def async_setup_coordinators(
    hass: HomeAssistant,
    config_entry: ARConfigEntry,
    descriptions: Iterable[AREntityDescription],
    background: Iterable[tuple[ARDataSource, timedelta]] = (),
) -> dict[ARDataSource, ARCoordinator[Any]]:
    """Set up a coordinator for every source of the descriptions."""

    descriptions = tuple(descriptions)
    runtime_data = config_entry.runtime_data

    requests = [
        (description.source, description.update_interval)
        for description in descriptions
    ]
    # Sources that never fail the setup: the node and background ones
    optional_requests = [
        *background,
        *(
            (description.node_source(mac), description.update_interval)
            for description in descriptions
            if description.node_source is not None
            for mac in runtime_data.get_node_macs(description)
        ),
    ]
    optional_sources = {source for source, _ in optional_requests}

    # A shared source polls at the shortest interval requested
    intervals: dict[ARDataSource, timedelta] = {}
    for source, interval in (*requests, *optional_requests):
        intervals[source] = min(intervals.get(source, interval), interval)

    coordinators = {
        source: _COORDINATORS.get(type(source), ARStateCoordinator)(
            hass, config_entry, source, interval
        )
        for source, interval in intervals.items()
    }

    # Let the library decide how many fetches run at once
    results = await asyncio.gather(
        *(
            # A failed optional source leaves only its own entities unavailable
            coordinator.async_refresh()
            if source in optional_sources
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
