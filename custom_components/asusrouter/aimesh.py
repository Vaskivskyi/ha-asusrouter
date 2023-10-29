"""AsusRouter AiMesh module."""

from __future__ import annotations

from typing import Any, Callable, Optional

from asusrouter.modules.aimesh import AiMeshDevice
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac


class AiMeshNode:
    """Representation of an AiMesh node."""

    def __init__(
        self,
        mac: str,
    ) -> None:
        """Initialize an AiMesh node."""

        self._mac: str = mac
        self.native = AiMeshDevice()
        self.identity: dict[str, Any] = {
            "mac": None,
            "ip": None,
            "alias": None,
            "model": None,
            "type": None,
            "connected": None,
        }
        self._extra_state_attributes: dict[str, Any] = {}

    @callback
    def update(
        self,
        node_info: Optional[AiMeshDevice] = None,
        event_call: Optional[Callable[[str, Optional[dict[str, Any]]], None]] = None,
    ) -> None:
        """Update AiMesh device."""

        if node_info:
            self.native = node_info
            self._mac = self._extra_state_attributes["mac"] = self.identity[
                "mac"
            ] = format_mac(node_info.mac)
            # Online
            if node_info.status:
                # State: router / node
                self._extra_state_attributes["type"] = self.identity[
                    "type"
                ] = node_info.type
                # IP
                self._extra_state_attributes["ip"] = self.identity["ip"] = node_info.ip
                # Alias
                self._extra_state_attributes["alias"] = self.identity[
                    "alias"
                ] = node_info.alias
                # Model
                self._extra_state_attributes["model"] = self.identity[
                    "model"
                ] = node_info.model
                # Product ID
                self._extra_state_attributes["product_id"] = node_info.product_id
                # Node level
                self._extra_state_attributes["level"] = node_info.level
                # Node parent
                if node_info.parent == {}:
                    self._extra_state_attributes["parent"] = {
                        "connection": "wired",
                    }
                else:
                    self._extra_state_attributes["parent"] = node_info.parent
                # Node config
                # self._extra_state_attributes[CONFIG] = node_info.config
                # Access point
                # self._extra_state_attributes[ACCESS_POINT] = node_info.ap
                # Notify reconnect
                if self.identity["connected"] is False and callable(event_call):
                    event_call(
                        "node_reconnected",
                        self.identity,
                    )
                # Connection status
                self.identity["connected"] = True
            else:
                # Notify disconnect
                if self.identity["connected"] is True and callable(event_call):
                    event_call(
                        "node_disconnected",
                        self.identity,
                    )
                # Connection status
                self.identity["connected"] = False
        elif callable(event_call):
            # Notify disconnect
            event_call(
                "node_disconnected",
                self.identity,
            )

    @property
    def mac(self):
        """Return node mac address."""

        return self._mac

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""

        return self._extra_state_attributes
