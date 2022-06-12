"""AsusRouter entity."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .dataclass import AREntityDescription
from .router import AsusRouterObj


class AREntity(CoordinatorEntity):
    """AsusRouter entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: AREntityDescription,
    ) -> None:
        """Initialize AsusRouter binary sensor."""

        super().__init__(coordinator)
        self.entity_description: AREntityDescription = description
        self.router = router
        self.api = router.api._api
        self.coordinator = coordinator

        self._attr_name = f"{router._name} {description.name}"
        self._attr_unique_id = f"{DOMAIN} {self.name}"
        self._attr_device_info = router.device_info

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        description = self.entity_description
        _attributes = description.extra_state_attributes
        if not _attributes:
            return {}

        attributes = {}

        for attr in _attributes:
            if attr in self.coordinator.data:
                attributes[_attributes[attr]] = self.coordinator.data[attr]

        return attributes
