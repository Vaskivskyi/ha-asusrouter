"""AsusRouter Client module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac

from asusrouter.modules.client import (
    AsusClient,
    AsusClientConnection,
    AsusClientConnectionWlan,
    AsusClientDescription,
)
from asusrouter.modules.connection import ConnectionState, ConnectionType
from asusrouter.modules.homeassistant import convert_to_ha_state_bool

from .helpers import clean_dict


class ARClient:
    """AsussRouter Client class."""

    def __init__(
        self,
        mac: str,
        name: Optional[str] = None,
    ):
        """Initialize the client."""

        self._mac = mac
        self._name = name

        self.device: bool = False

        # To be recieved from the device
        # Client description
        self.description: Optional[AsusClientDescription] = None
        # Connection description - AsusClientConnection / AsusClientConnectionWlan
        self.connection: Optional[AsusClientConnection] = None

        # To be generated for other parts of the integration
        self._identity: Optional[dict[str, Any]] = None
        self._extra_state_attributes: dict[str, Any] = {}

        # Connection state
        self._state: ConnectionState = ConnectionState.UNKNOWN
        self._connection_type: ConnectionType = ConnectionType.DISCONNECTED
        self._guest: bool = False
        self._guest_id: int = 0

        # Device last active
        self._last_activity: Optional[datetime] = None

    @callback
    def update(
        self,
        client_info: Optional[AsusClient] = None,
        consider_home: int = 0,
        event_call: Optional[
            Callable[[str, Optional[dict[str, Any]]], None]
        ] = None,
    ):
        """Update client information."""

        utc_now: datetime = datetime.now(timezone.utc)

        state: Optional[ConnectionState] = None

        # If client information is provided
        if client_info is not None:
            # Description
            self.description = client_info.description

            # Connection
            self.connection = client_info.connection

            # Connected state
            state = client_info.state

        self._identity = self.generate_identity(state)
        self._extra_state_attributes = self.generate_extra_state_attributes()

        # If is connected
        if state is ConnectionState.CONNECTED:
            # Update last activity
            self._last_activity = utc_now

            # Device was disconnected, now it has reconnected
            # Fire event and connected callback
            if self._state is ConnectionState.DISCONNECTED:
                if event_call is not None:
                    event_call("device_reconnected", self.identity)

            # Update connection status
            self._state = ConnectionState.CONNECTED

        # If was connected, check if it's time to mark it as disconnected
        # when we are above the consider home time
        elif (
            self._state is ConnectionState.CONNECTED
            and self._last_activity is not None
            and (utc_now - self._last_activity).total_seconds() > consider_home
        ):
            # Update connection status
            self._state = ConnectionState.DISCONNECTED

            # Fire event
            if event_call is not None:
                event_call(
                    "device_disconnected",
                    self.identity,
                )

    def generate_identity(
        self, state: Optional[ConnectionState]
    ) -> dict[str, Any]:
        """Generate client identity."""

        identity: dict[str, Any] = {
            "mac": self.mac_address,
            "ip": self.ip_address,
            "name": self.name,
        }

        if isinstance(self.connection, AsusClientConnection):
            # Rewrite guest from last known state if needed
            if state == ConnectionState.DISCONNECTED:
                identity["guest"] = self._guest
                identity["guest_id"] = self._guest_id
            if self.connection.type != ConnectionType.DISCONNECTED:
                self._connection_type = self.connection.type
            identity["connection_type"] = self._connection_type
            identity["node"] = (
                format_mac(self.connection.node)
                if self.connection.node
                else None
            )

        if isinstance(self.connection, AsusClientConnectionWlan):
            identity["guest"] = self._guest = self.connection.guest
            identity["guest_id"] = self._guest_id = self.connection.guest_id
            identity["connected"] = self.connection.since

        return clean_dict(identity)

    def generate_extra_state_attributes(self) -> dict[str, Any]:
        """Generate extra state attributes."""

        attributes: dict[str, Any] = (
            self._identity.copy() if self._identity else {}
        )

        attributes["last_activity"] = self._last_activity

        if isinstance(self.description, AsusClientDescription):
            attributes["vendor"] = self.description.vendor

        if isinstance(self.connection, AsusClientConnection):
            attributes["ip_type"] = self.connection.ip_method
            attributes["internet_mode"] = self.connection.internet_mode
            attributes["internet"] = self.connection.internet_state

        if isinstance(self.connection, AsusClientConnectionWlan):
            attributes["rssi"] = self.connection.rssi
            attributes["rx_speed"] = self.connection.rx_speed
            attributes["tx_speed"] = self.connection.tx_speed

        return clean_dict(attributes)

    @property
    def state(self) -> Optional[bool]:
        """Return if the device is connected."""

        return convert_to_ha_state_bool(self._state)

    @property
    def ip_address(self) -> Optional[str]:
        """Return IP address."""

        return (
            self.connection.ip_address if self.connection is not None else None
        )

    @property
    def mac_address(self) -> str:
        """Return MAC address."""

        return self._mac

    @property
    def name(self) -> Optional[str]:
        """Return name."""

        return (
            self.description.name
            if self.description is not None
            else self._name
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""

        return self._extra_state_attributes

    @property
    def identity(self) -> Optional[dict[str, Any]]:
        """Return identity."""

        return self._identity
