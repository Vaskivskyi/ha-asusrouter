"""AsusRouter router module."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from asusrouter.error import AsusRouterError
from asusrouter.modules.client import AsusClientConnectionWlan
from asusrouter.modules.connection import ConnectionState, ConnectionType
from asusrouter.modules.identity import AsusDevice
from asusrouter.modules.parental_control import ParentalControlRule
from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    Platform,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .aimesh import AiMeshNode
from .bridge import ARBridge
from .client import ARClient
from .const import (
    ACCESS_POINT,
    AIMESH,
    CONF_CLIENT_DEVICE,
    CONF_CLIENT_FILTER,
    CONF_CLIENT_FILTER_LIST,
    CONF_CLIENTS_IN_ATTR,
    CONF_CREATE_DEVICES,
    CONF_DEFAULT_CLIENT_DEVICE,
    CONF_DEFAULT_CLIENT_FILTER,
    CONF_DEFAULT_CLIENTS_IN_ATTR,
    CONF_DEFAULT_CONSIDER_HOME,
    CONF_DEFAULT_CREATE_DEVICES,
    CONF_DEFAULT_EVENT,
    CONF_DEFAULT_INTERVALS,
    CONF_DEFAULT_LATEST_CONNECTED,
    CONF_DEFAULT_MODE,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_PORTS,
    CONF_DEFAULT_SCAN_INTERVAL,
    CONF_DEFAULT_SPLIT_INTERVALS,
    CONF_DEFAULT_TRACK_DEVICES,
    CONF_EVENT_NODE_CONNECTED,
    CONF_INTERVAL,
    CONF_INTERVAL_DEVICES,
    CONF_LATEST_CONNECTED,
    CONF_MODE,
    CONF_REQ_RELOAD,
    CONF_SPLIT_INTERVALS,
    CONF_TRACK_DEVICES,
    CONNECTED,
    COORDINATOR,
    DEVICES,
    DOMAIN,
    FIRMWARE,
    HTTP,
    HTTPS,
    LIST,
    MAC,
    MEDIA_BRIDGE,
    METHOD,
    NO_SSL,
    NUMBER,
    ROUTER,
    SENSORS,
    SENSORS_AIMESH,
    SENSORS_CONNECTED_DEVICES,
    SSL,
)
from .helpers import as_dict

_LOGGER = logging.getLogger(__name__)


class ARSensorHandler:
    """Handler for AsusRouter sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        bridge: ARBridge,
        options: dict[str, Any],
    ) -> None:
        """Initialise sensor handler."""

        self.hass = hass
        self.bridge = bridge

        # Selected options
        self._options = options
        self._mode = options.get(CONF_MODE, CONF_DEFAULT_MODE)
        self._split_intervals = options.get(
            CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS
        )

        # Sensors
        self._clients_number: int = 0
        self._clients_list: Optional[list[dict[str, Any]]] = []
        self._latest_connected: Optional[datetime] = None
        self._latest_connected_list: list[dict[str, Any]] = []
        self._aimesh_number: int = 0
        self._aimesh_list: list[dict[str, Any]] = []
        self._gn_clients_number: int = 0

    async def _get_clients(self) -> dict[str, Any]:
        """Return clients sensors."""

        return {
            SENSORS_CONNECTED_DEVICES[0]: self._clients_number,
            SENSORS_CONNECTED_DEVICES[1]: self._clients_list,
            SENSORS_CONNECTED_DEVICES[2]: self._latest_connected_list,
            SENSORS_CONNECTED_DEVICES[3]: self._latest_connected,
            SENSORS_CONNECTED_DEVICES[4]: self._gn_clients_number,
        }

    async def _get_aimesh(self) -> dict[str, Any]:
        """Return aimesh sensors."""

        # In router / AP / Media Bridge mode
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            return {
                NUMBER: self._aimesh_number,
                LIST: self._aimesh_list,
            }
        return {}

    def update_clients(
        self,
        clients_number: int,
        clients_list: Optional[list[Any]],
        latest_connected: Optional[datetime],
        latest_connected_list: list[Any],
        gn_clients_number: int,
    ) -> bool:
        """Update connected devices attribute."""

        if (
            self._clients_number == clients_number
            and self._clients_list == clients_list
            and self._latest_connected == latest_connected
            and self._latest_connected_list == latest_connected_list
            and self._gn_clients_number == gn_clients_number
        ):
            return False
        self._clients_number = clients_number
        self._clients_list = clients_list
        self._latest_connected = latest_connected
        self._latest_connected_list = latest_connected_list
        self._gn_clients_number = gn_clients_number
        return True

    def update_aimesh(
        self,
        nodes_number: int,
        nodes_list: list[dict[str, Any]],
    ) -> bool:
        """Update aimesh sensors."""

        if self._aimesh_number == nodes_number and self._aimesh_list == nodes_list:
            return False

        self._aimesh_number = nodes_number
        self._aimesh_list = nodes_list
        return True

    async def get_coordinator(
        self,
        sensor_type: str,
        update_method: Optional[Callable[[], Awaitable[dict[str, Any]]]] = None,
    ) -> DataUpdateCoordinator:
        """Find coordinator for the sensor type."""

        # Should sensor be polled?
        should_poll = True

        # Sensor-specific rules
        method: Callable[[], Awaitable[dict[str, Any]]]
        if sensor_type == DEVICES:
            should_poll = False
            method = self._get_clients
        elif sensor_type == AIMESH:
            should_poll = False
            method = self._get_aimesh
        elif update_method is not None:
            method = update_method
        else:
            raise RuntimeError(f"Unknown sensor type: {sensor_type}")

        # Update interval
        update_interval: timedelta
        # Static intervals
        if sensor_type == FIRMWARE:
            update_interval = timedelta(
                seconds=self._options.get(
                    CONF_INTERVAL + sensor_type,
                    CONF_DEFAULT_INTERVALS[CONF_INTERVAL + sensor_type],
                )
            )
        # Configurable intervals
        else:
            update_interval = timedelta(
                seconds=self._options.get(
                    CONF_INTERVAL + sensor_type,
                    self._options.get(CONF_SCAN_INTERVAL, CONF_DEFAULT_SCAN_INTERVAL),
                )
                if self._options.get(CONF_SPLIT_INTERVALS, CONF_DEFAULT_SPLIT_INTERVALS)
                else self._options.get(CONF_SCAN_INTERVAL, CONF_DEFAULT_SCAN_INTERVAL)
            )

        # Coordinator
        coordinator = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            name=sensor_type,
            update_method=method,
            update_interval=update_interval if should_poll else None,
        )

        _LOGGER.debug(
            "Coordinator initialized for `%s`. Update interval: `%s`",
            sensor_type,
            update_interval,
        )

        # Update coordinator
        await coordinator.async_refresh()

        return coordinator


class ARDevice:
    """Representatiion of AsusRouter."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the object."""

        self.hass = hass
        self._config_entry = config_entry
        self._options = config_entry.options.copy()

        # Device configs
        self._conf_host: str = config_entry.data[CONF_HOST]
        self._conf_port: int = self._options[CONF_PORT]
        self._conf_name: str = "AsusRouter"

        if self._conf_port == CONF_DEFAULT_PORT:
            self._conf_port = (
                CONF_DEFAULT_PORTS[SSL]
                if self._options[CONF_SSL]
                else CONF_DEFAULT_PORTS[NO_SSL]
            )

        self._mode = self._options.get(CONF_MODE, CONF_DEFAULT_MODE)

        # Bridge & device information
        self.bridge: ARBridge = ARBridge(
            hass, dict(self._config_entry.data), self._options
        )
        self._identity: AsusDevice = AsusDevice()
        self._mac: str = ""

        # Device sensors
        self._sensor_handler: Optional[ARSensorHandler] = None
        self._sensor_coordinator: dict[str, Any] = {}

        self._aimesh: dict[str, Any] = {}
        self._clients: dict[str, Any] = {}
        self._clients_number: int = 0
        self._clients_list: list[dict[str, Any]] = []
        self._aimesh_number: int = 0
        self._aimesh_list: list[dict[str, Any]] = []
        self._latest_connected: Optional[datetime] = None
        self._latest_connected_list: list[dict[str, Any]] = []
        self._connect_error: bool = False
        self._gn_clients_number: int = 0

        # Sensor filters
        self.sensor_filters: dict[tuple[str, str], list[str]] = {}

        # Client features
        self.client_device: bool = self._options.get(
            CONF_CLIENT_DEVICE,
            CONF_DEFAULT_CLIENT_DEVICE,
        )
        self.clients_in_attr: bool = self._options.get(
            CONF_CLIENTS_IN_ATTR,
            CONF_DEFAULT_CLIENTS_IN_ATTR,
        )
        if self.clients_in_attr is False:
            # Mask clients in attributes
            self.sensor_filters[(DEVICES, NUMBER)] = [DEVICES]
        self.create_devices: bool = self._options.get(
            CONF_CREATE_DEVICES,
            CONF_DEFAULT_CREATE_DEVICES,
        )
        self._pc_rules: dict[str, Any] = {}

        # Client filter
        self._client_filter: str = self._options.get(
            CONF_CLIENT_FILTER, CONF_DEFAULT_CLIENT_FILTER
        )
        self._client_filter_list: list[str] = self._options.get(
            CONF_CLIENT_FILTER_LIST, []
        )

        # On-close parameters
        self._on_close: list[Callable] = []

    async def setup(self) -> None:
        """Set up an AsusRouter."""

        _LOGGER.debug("Setting up router")

        # Connect & check connection
        try:
            await self.bridge.async_connect()
        except (OSError, AsusRouterError) as ex:
            raise ConfigEntryNotReady from ex
        if not self.bridge.connected:
            raise ConfigEntryNotReady

        _LOGGER.debug("Bridge connected")

        # Write the identity
        self._identity = self.bridge.identity
        self._mac = format_mac(self._identity.mac)

        # Use device model as the default device name if name not set
        if self._identity.model is not None:
            self._conf_name = self._identity.model

        # Tracked entities
        entity_reg = er.async_get(self.hass)
        tracked_entries = er.async_entries_for_config_entry(
            entity_reg, self._config_entry.entry_id
        )

        # Clean up devices with no entities
        device_registry = dr.async_get(self.hass)
        devices = dr.async_entries_for_config_entry(
            dr.async_get(self.hass), self._config_entry.entry_id
        )
        for device_entry in devices:
            entries = er.async_entries_for_device(entity_reg, device_entry.id)
            # No entities for the device
            if len(entries) == 0:
                _LOGGER.debug(
                    "Removing device `%s` since it has no entities", device_entry.name
                )
                device_registry.async_remove_device(device_entry.id)

        for entry in tracked_entries:
            # Migrate from 0.21.x and below
            # To be removed in 0.30.0
            uid: str = entry.unique_id
            if DOMAIN in uid:
                new_uid = uid.replace(f"{DOMAIN}_", "")

                # Check whether UID has duplicate
                conflict_entity_id = entity_reg.async_get_entity_id(
                    entry.domain, DOMAIN, new_uid
                )
                if conflict_entity_id:
                    entity_reg.async_remove(entry.entity_id)
                    continue

                entity_reg.async_update_entity(entry.entity_id, new_unique_id=new_uid)

            # Migrate from 0.21.x and below
            # To be removed in 0.30.0
            if any(id_to_find in uid for id_to_find in ("lan_speed", "wan_speed")):
                entity_reg.async_remove(entry.entity_id)

            # Clients already tracked
            if entry.domain != "device_tracker":
                continue
            capabilities = entry.capabilities
            # Check that capabilities is a dictionary and that it has the MAC address
            # I actually don't know how this can be possible, but the issue #785
            # https://github.com/Vaskivskyi/ha-asusrouter/issues/785
            # shows that device_tracker entry can exist without a MAC address
            if isinstance(capabilities, dict) and "mac" in capabilities:
                mac = capabilities["mac"]
                self._clients[mac] = ARClient(mac)

                # Create devices when tracker was enabled
                disabled_by = entry.disabled_by
                if disabled_by is None:
                    self._clients[mac].device = True

        # Mode-specific
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            # Update AiMesh
            await self.update_nodes()

            # Update clients
            await self.update_clients()

            # Update parental control
            await self.update_pc_rules()
        else:
            _LOGGER.debug(
                "Device is in AiMesh node mode. Device tracking and AiMesh monitoring is disabled"
            )

        # Clients filter
        match self._client_filter:
            case "include":
                _LOGGER.debug("Setting clients filter: `include`")
                self._clients = {
                    mac: client
                    for mac, client in self._clients.items()
                    if mac in self._client_filter_list
                }
            case "exclude":
                _LOGGER.debug("Setting clients filter: `exclude`")
                self._clients = {
                    mac: client
                    for mac, client in self._clients.items()
                    if mac not in self._client_filter_list
                }
            case _:
                _LOGGER.debug("Setting clients filter: `no_filter`")

        # Initialize sensor coordinators
        await self._init_sensor_coordinators()

        # Initialize services
        await self._init_services()

        # On-close parameters
        self.async_on_close(
            async_track_time_interval(
                self.hass,
                self.update_all,
                timedelta(
                    seconds=self._options.get(
                        CONF_INTERVAL_DEVICES, CONF_DEFAULT_SCAN_INTERVAL
                    )
                ),
            )
        )

    async def update_all(
        self,
        now: Optional[datetime] = None,
    ) -> None:
        """Update all AsusRouter platforms."""

        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            await self.update_clients()
            await self.update_nodes()
            await self.update_pc_rules()

    async def update_clients(self) -> None:
        """Update AsusRouter clients."""

        # Check clients tracking settings
        if self._options.get(CONF_TRACK_DEVICES, CONF_DEFAULT_TRACK_DEVICES) is False:
            _LOGGER.debug("Device tracking is disabled")
        else:
            _LOGGER.debug("Device tracking is enabled")

        # Get client list
        _LOGGER.debug("Updating AsusRouter device list for '%s'", self._conf_host)
        try:
            api_clients = await self.bridge.async_get_clients()
            # For Media bridge mode only leave wired devices
            if self._mode == MEDIA_BRIDGE:
                api_clients = {
                    mac: client
                    for mac, client in api_clients.items()
                    if client.connection is not None
                    and client.connection.type == ConnectionType.WIRED
                }
        except UpdateFailed as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Cannot get clients from '%s': %s",
                    self._conf_host,
                    ex,
                )
            return

        # Notify about reconnection
        if self._connect_error:
            self._connect_error = False
            _LOGGER.info("Reconnected to '%s'", self._conf_host)

        # Get the consider home settings
        consider_home = self._options.get(
            CONF_CONSIDER_HOME, CONF_DEFAULT_CONSIDER_HOME
        )

        # Format clients MAC
        clients = {format_mac(mac): client for mac, client in api_clients.items()}

        # Update known clients
        for client_mac, client_state in self._clients.items():
            client_info = clients.pop(client_mac, None)
            client_state.update(
                client_info,
                consider_home,
                event_call=self.fire_event,
            )

        # Add new clients
        new_clients = []
        new_client = False

        for client_mac, client_info in clients.items():
            # We proceed only if device is online
            # This way we'll avoid adding long history of devices
            # which might have been connected long time ago
            # and are not important anymore
            state = client_info.state
            if state is not ConnectionState.CONNECTED:
                continue

            # Flag that new client is added
            new_client = True

            # Create new client and process it
            client_name = (
                client_info.description.name if client_info.description else None
            )
            client = ARClient(client_mac, client_name)
            client.update(
                client_info,
                consider_home,
                event_call=self.fire_event,
            )

            # Add client to the storage
            self._clients[client_mac] = client

            # Add client to the list of new clients
            new_clients.append(client)

        # Notify about new clients
        for client in new_clients:
            _LOGGER.debug("New client: %s", client.identity)
            self.fire_event(
                "device_connected",
                client.identity,
            )

        # Connected clients sensor
        self._clients_number = 0
        self._clients_list = []

        # Connected GuestNetwork clients sensor
        self._gn_clients_number = 0

        for client_mac, client in self._clients.items():
            if client.state:
                self._clients_number += 1
                self._clients_list.append(client.identity)

            if isinstance(client.connection, AsusClientConnectionWlan) and client.connection.guest:
                self._gn_clients_number += 1


        # Filter clients
        # Only include the listed clients
        if self._client_filter == "include":
            self._clients = {
                mac: client
                for mac, client in self._clients.items()
                if mac in self._client_filter_list
            }
        # Exclude the listed clients
        elif self._client_filter == "exclude":
            self._clients = {
                mac: client
                for mac, client in self._clients.items()
                if mac not in self._client_filter_list
            }

        async_dispatcher_send(self.hass, self.signal_device_update)
        if new_client:
            async_dispatcher_send(self.hass, self.signal_device_new)

        # Update latest connected sensors
        self.update_latest_connected()

        await self._update_unpolled_sensors()

    def update_latest_connected(self) -> None:
        """Update latest connected sensors."""

        def latest_connected_time(self, element: dict[str, Any]) -> datetime:
            """Get connected time for the device."""

            connected = element.get("connected")
            if isinstance(connected, datetime):
                return connected
            # If not connected, return the current time
            # This is just a fallback, since the device should be connected
            return datetime.now(timezone.utc)

        # New list
        new_list = []

        # We take all the clients currently connected from the self._clients_list
        # which have the connected time set
        for client in self._clients_list:
            if client.get("connected"):
                new_list.append(client)

        # Append any client which was already in the list self._latest_connected_list
        # but is not in the new list. This means that the client has disconnected,
        # but the sensor should be showing all the connections made
        # Since client itself might have changed, we should compare MAC addresses
        for client in self._latest_connected_list:
            if client["mac"] not in [x["mac"] for x in new_list]:
                new_list.append(client)

        # Sort the list by time using the latest_connected_time function
        # Newer devices should be at the end of the list
        new_list.sort(key=lambda x: latest_connected_time(self, x))

        # Reduce the list to the size specified in the configuration
        while len(new_list) > self._options.get(
            CONF_LATEST_CONNECTED, CONF_DEFAULT_LATEST_CONNECTED
        ):
            new_list.pop(0)

        # Update the self._latest_connected and self._latest_connected_list
        # Check that list has at least one element so that we don't get an error
        if len(new_list) > 0:
            self._latest_connected = new_list[-1].get(CONNECTED)
            self._latest_connected_list = new_list

    async def update_nodes(self) -> None:
        """Update AsusRouter AiMesh nodes."""

        _LOGGER.debug("Updating AiMesh status for '%s'", self._conf_host)
        try:
            aimesh = await self.bridge.async_get_aimesh_nodes()
        except UpdateFailed as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to '%s' for aimesh update: %s",
                    self._conf_host,
                    ex,
                )
            return

        new_node = False

        # Update existing nodes
        nodes = {format_mac(mac): description for mac, description in aimesh.items()}
        for node_mac, node in self._aimesh.items():
            node_info = nodes.pop(node_mac, None)
            node.update(
                node_info,
                event_call=self.fire_event,
            )

        # Add new nodes
        new_nodes = []
        for node_mac, node_info in nodes.items():
            new_node = True
            node = AiMeshNode(node_mac)
            node.update(
                node_info,
                event_call=self.fire_event,
            )
            self._aimesh[node_mac] = node
            new_nodes.append(node)

        # Notify new nodes
        for node in new_nodes:
            self.fire_event(
                CONF_EVENT_NODE_CONNECTED,
                node.identity,
            )

        # AiMesh sensors
        self._aimesh_number = 0
        self._aimesh_list = []
        for mac, node in self._aimesh.items():
            if node.identity[CONNECTED]:
                self._aimesh_number += 1
            self._aimesh_list.append(node.identity)

        async_dispatcher_send(self.hass, self.signal_aimesh_update)
        if new_node:
            async_dispatcher_send(self.hass, self.signal_aimesh_new)

    async def update_pc_rules(self) -> None:
        """Update parental control rules."""

        _LOGGER.debug("Updating parental control rules for '%s'", self._conf_host)
        try:
            pc_data = (
                await self.bridge._get_data_parental_control()  # pylint: disable=protected-access
            )
        except UpdateFailed as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to '%s' for pc rules update: %s",
                    self._conf_host,
                    ex,
                )
            return

        new_flag = False

        rules: dict[str, ParentalControlRule] = pc_data.get("rules", {})

        rules_to_save = {}

        # Update existing rules
        for mac, rule in self._pc_rules.items():
            rule = rules.pop(mac, None)
            if rule is None:
                # If the rule was removed
                new_flag = True
                continue
            rules_to_save[mac] = rule

        # Add new rules
        for mac, rule in rules.items():
            new_flag = True
            rules_to_save[mac] = rule

        # Check the rules for non-valid ones
        rules_to_save = {
            mac: rule
            for mac, rule in rules_to_save.items()
            if mac != "" and rule.mac is not None
        }

        # Save rules
        self._pc_rules = rules_to_save

        async_dispatcher_send(self.hass, self.signal_pc_rules_update)
        if new_flag:
            async_dispatcher_send(self.hass, self.signal_pc_rules_new)

    async def _init_services(self) -> None:
        """Initialize AsusRouter services."""

        # Parental control service
        async def async_service_device_internet_access(service: ServiceCall):
            """Adjust device internet access."""

            await self.bridge.async_pc_rule(raw=service.data)

            # Force PC rules update
            await self.update_pc_rules()

            # In case of removing rule(s) we need to reload the platform
            if service.data.get("state") == "remove":
                unload = await self.hass.config_entries.async_unload_platforms(
                    self._config_entry, [Platform.SWITCH]
                )
                if unload:
                    await self.hass.config_entries.async_forward_entry_setups(
                        self._config_entry, [Platform.SWITCH]
                    )

        if self._mode == ROUTER:
            self.hass.services.async_register(
                DOMAIN, "device_internet_access", async_service_device_internet_access
            )

        # Remove device trackers service
        async def async_service_remove_trackers(service: ServiceCall):
            """Remove device trackers."""

            await self.remove_trackers(raw=service.data)

        self.hass.services.async_register(
            DOMAIN, "remove_trackers", async_service_remove_trackers
        )

    async def _init_sensor_coordinators(self) -> None:
        """Initialize sensor coordinators."""

        # If already initialized
        if self._sensor_handler:
            return

        # Initialize sensor handler
        self._sensor_handler = ARSensorHandler(self.hass, self.bridge, self._options)

        # Update devices
        self._sensor_handler.update_clients(
            self._clients_number,
            self._clients_list,
            self._latest_connected,
            self._latest_connected_list,
            self._gn_clients_number,
        )
        self._sensor_handler.update_aimesh(
            self._aimesh_number,
            self._aimesh_list,
        )

        # Get available sensors
        available_sensors = await self.bridge.async_get_available_sensors()

        # Add devices sensors
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            available_sensors[DEVICES] = {SENSORS: SENSORS_CONNECTED_DEVICES}
            available_sensors[AIMESH] = {SENSORS: SENSORS_AIMESH}

        # Process available sensors
        for sensor_type, sensor_definition in available_sensors.items():
            sensor_names = sensor_definition.get(SENSORS)
            if not sensor_names:
                continue

            # Find and initialize coordinator
            coordinator = await self._sensor_handler.get_coordinator(
                sensor_type, sensor_definition.get(METHOD)
            )

            # Save the coordinator
            self._sensor_coordinator[sensor_type] = {
                COORDINATOR: coordinator,
                sensor_type: sensor_names,
            }

    async def _update_unpolled_sensors(self) -> None:
        """Request refresh for AsusRouter unpolled sensors."""

        # If sensor handler is not initialized
        if not self._sensor_handler:
            return

        # AiMesh
        if AIMESH in self._sensor_coordinator:
            coordinator = self._sensor_coordinator[AIMESH][COORDINATOR]
            if self._sensor_handler.update_aimesh(
                self._aimesh_number,
                self._aimesh_list,
            ):
                await coordinator.async_refresh()

        # Devices
        if DEVICES in self._sensor_coordinator:
            coordinator = self._sensor_coordinator[DEVICES][COORDINATOR]

            # Block clients list for attributes
            clients_list = None if self.clients_in_attr is False else self._clients_list

            if self._sensor_handler.update_clients(
                self._clients_number,
                clients_list,
                self._latest_connected,
                self._latest_connected_list,
                self._gn_clients_number,
            ):
                await coordinator.async_refresh()

    async def close(self) -> None:
        """Close the connection."""

        # Disconnect the bridge
        if self.bridge.active:
            await self.bridge.async_disconnect()

        # Run on-close methods
        for func in self._on_close:
            func()

        self._on_close.clear()

    @callback
    def async_on_close(
        self,
        func: CALLBACK_TYPE,
    ) -> None:
        """Functions on router close."""

        self._on_close.append(func)

    def update_options(
        self,
        new_options: dict,
    ) -> bool:
        """Update router options."""

        require_reload = False
        for name, new_option in new_options.items():
            if name in CONF_REQ_RELOAD:
                old_opt = self._options.get(name)
                if not old_opt or old_opt != new_option:
                    require_reload = True
                    break

        self._options.update(new_options)
        return require_reload

    @callback
    def fire_event(
        self,
        event: str,
        args: Optional[dict[str, Any]] = None,
    ):
        """Fire HA event."""

        # Check for mute
        _event_mac = args.get("mac") if isinstance(args, dict) else None
        if _event_mac is not None:
            match self._client_filter:
                case "include":
                    if _event_mac not in self._client_filter_list:
                        return
                case "exclude":
                    if _event_mac in self._client_filter_list:
                        return

        _event_status = self._options.get(event)
        if _event_status is None:
            _event_status = CONF_DEFAULT_EVENT.get(event, False)
        if _event_status is True:
            event_name = f"{DOMAIN}_{event}"
            _LOGGER.debug("Firing event `%s` with arguments: %s", event_name, args)
            self.hass.bus.fire(
                event_name,
                args,
            )

    async def remove_trackers(self, **kwargs: Any) -> None:
        """Remove device trackers."""

        _LOGGER.debug("Removing trackers")

        # Check that data is provided
        raw = kwargs.get("raw", None)
        if raw is None:
            return

        # Get entities to remove
        if "entities" in raw:
            entities = raw["entities"]
            entity_reg = er.async_get(self.hass)
            for entity in entities:
                reg_value = entity_reg.async_get(entity)
                if not isinstance(reg_value, er.RegistryEntry):
                    continue
                capabilities: dict[str, Any] = as_dict(reg_value.capabilities)
                mac = capabilities[MAC]
                _LOGGER.debug("Trying to remove tracker with mac: %s", mac)
                if mac in self._clients:
                    self._clients.pop(mac)
                    _LOGGER.debug("Found and removed")

        # Update clients
        await self.update_clients()

        # Reload device tracker platform
        unload = await self.hass.config_entries.async_unload_platforms(
            self._config_entry, [Platform.DEVICE_TRACKER]
        )
        if unload:
            await self.hass.config_entries.async_forward_entry_setups(
                self._config_entry, [Platform.DEVICE_TRACKER]
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Device information."""

        return DeviceInfo(
            identifiers={
                (DOMAIN, self.mac),
                (DOMAIN, self._identity.serial),
            },
            name=self._conf_name,
            model=self._identity.model,
            manufacturer=self._identity.brand,
            sw_version=str(self._identity.firmware),
            configuration_url=f"{HTTPS if self._options[CONF_SSL] else HTTP}://\
{self._conf_host}:{self._conf_port}",
        )

    @property
    def signal_aimesh_new(self) -> str:
        """Notify new AiMesh nodes."""

        return f"{DOMAIN}-aimesh-new"

    @property
    def signal_aimesh_update(self) -> str:
        """Notify updated AiMesh nodes."""

        return f"{DOMAIN}-aimesh-update"

    @property
    def signal_device_new(self) -> str:
        """Notify new device."""

        return f"{DOMAIN}-device-new"

    @property
    def signal_device_update(self) -> str:
        """Notify updated device."""

        return f"{DOMAIN}-device-update"

    @property
    def signal_pc_rules_new(self) -> str:
        """Notify new parental control rules."""

        return f"{DOMAIN}-pc-rules-new"

    @property
    def signal_pc_rules_update(self) -> str:
        """Notify updated parental control rules."""

        return f"{DOMAIN}-pc-rules-update"

    @property
    def aimesh(self) -> dict[str, Any]:
        """Return AiMesh nodes."""

        return self._aimesh

    @property
    def devices(self) -> dict[str, Any]:
        """Return devices."""

        return self._clients

    @property
    def mac(self) -> str:
        """Router MAC address."""

        return self._mac

    @property
    def pc_rules(self) -> dict[str, ParentalControlRule]:
        """Return parental control rules."""

        return self._pc_rules

    @property
    def sensor_coordinator(self) -> dict[str, Any]:
        """Return sensor coordinator."""

        return self._sensor_coordinator
