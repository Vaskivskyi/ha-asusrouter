"""AsusRouter router module."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
import logging
from typing import Any, TypeVar

from asusrouter import (
    AiMeshDevice,
    AsusDevice,
    AsusRouterConnectionError,
    ConnectedDevice,
)

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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .bridge import ARBridge
from .const import (
    ACCESS_POINT,
    AIMESH,
    ALIAS,
    CONF_DEFAULT_CONSIDER_HOME,
    CONF_DEFAULT_ENABLE_CONTROL,
    CONF_DEFAULT_INTERVALS,
    CONF_DEFAULT_LATEST_CONNECTED,
    CONF_DEFAULT_MODE,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_PORTS,
    CONF_DEFAULT_SCAN_INTERVAL,
    CONF_DEFAULT_SPLIT_INTERVALS,
    CONF_DEFAULT_TRACK_DEVICES,
    CONF_ENABLE_CONTROL,
    CONF_EVENT_DEVICE_CONNECTED,
    CONF_EVENT_DEVICE_DISCONNECTED,
    CONF_EVENT_DEVICE_RECONNECTED,
    CONF_EVENT_NODE_CONNECTED,
    CONF_EVENT_NODE_DISCONNECTED,
    CONF_EVENT_NODE_RECONNECTED,
    CONF_INTERVAL,
    CONF_INTERVAL_DEVICES,
    CONF_LATEST_CONNECTED,
    CONF_MODE,
    CONF_REQ_RELOAD,
    CONF_SPLIT_INTERVALS,
    CONF_TRACK_DEVICES,
    CONNECTED,
    CONNECTION,
    CONNECTION_TYPE_2G,
    CONNECTION_TYPE_5G,
    CONNECTION_TYPE_5G2,
    CONNECTION_TYPE_6G,
    CONNECTION_TYPE_UNKNOWN,
    CONNECTION_TYPE_WIRED,
    COORDINATOR,
    DEVICE_ATTRIBUTE_CONNECTION_TIME,
    DEVICE_ATTRIBUTE_CONNECTION_TYPE,
    DEVICE_ATTRIBUTE_GUEST,
    DEVICE_ATTRIBUTE_GUEST_ID,
    DEVICE_ATTRIBUTE_INTERNET,
    DEVICE_ATTRIBUTE_INTERNET_MODE,
    DEVICE_ATTRIBUTE_IP_TYPE,
    DEVICE_ATTRIBUTE_LAST_ACTIVITY,
    DEVICE_ATTRIBUTE_RSSI,
    DEVICE_ATTRIBUTE_RX_SPEED,
    DEVICE_ATTRIBUTE_TX_SPEED,
    DEVICE_ATTRIBUTES,
    DEVICES,
    DOMAIN,
    FIRMWARE,
    HTTP,
    HTTPS,
    IP,
    LEVEL,
    LIST,
    MAC,
    MEDIA_BRIDGE,
    METHOD,
    MODEL,
    NAME,
    NO_SSL,
    NODE,
    NUMBER,
    PARENT,
    PRODUCT_ID,
    ROUTER,
    SENSORS,
    SENSORS_AIMESH,
    SENSORS_CONNECTED_DEVICES,
    SSL,
    TYPE,
    WIRED,
)
from .helpers import as_dict

_T = TypeVar("_T")
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
        self._connected_devices: int = 0
        self._connected_devices_list: list[dict[str, Any]] = []
        self._latest_connected: datetime | None = None
        self._latest_connected_list: list[dict[str, Any]] = []
        self._aimesh_devices: int = 0
        self._aimesh_list: list[dict[str, Any]] = []

    async def _get_connected_devices(self) -> dict[str, Any]:
        """Return connected devices sensors."""

        return {
            SENSORS_CONNECTED_DEVICES[0]: self._connected_devices,
            SENSORS_CONNECTED_DEVICES[1]: self._connected_devices_list,
            SENSORS_CONNECTED_DEVICES[2]: self._latest_connected_list,
            SENSORS_CONNECTED_DEVICES[3]: self._latest_connected,
        }

    async def _get_aimesh_devices(self) -> dict[str, Any]:
        """Return aimesh devices sensors."""

        # Only in router or AP mode
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            return {
                NUMBER: self._aimesh_devices,
                LIST: self._aimesh_list,
            }
        return {}

    def update_device_count(
        self,
        connected_devices: int,
        connected_devices_list: list[Any],
        latest_connected: datetime | None,
        latest_connected_list: list[Any],
    ) -> bool:
        """Update connected devices attribute."""

        if (
            self._connected_devices == connected_devices
            and self._connected_devices_list == connected_devices_list
            and self._latest_connected == latest_connected
            and self._latest_connected_list == latest_connected_list
        ):
            return False
        self._connected_devices = connected_devices
        self._connected_devices_list = connected_devices_list
        self._latest_connected = latest_connected
        self._latest_connected_list = latest_connected_list
        return True

    def update_aimesh(
        self,
        nodes_number: int,
        nodes_list: list[dict[str, Any]],
    ) -> bool:
        """Update aimesh sensors."""

        if self._aimesh_devices == nodes_number and self._aimesh_list == nodes_list:
            return False

        self._aimesh_devices = nodes_number
        self._aimesh_list = nodes_list
        return True

    async def get_coordinator(
        self,
        sensor_type: str,
        update_method: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    ) -> DataUpdateCoordinator:
        """Find coordinator for the sensor type."""

        # Should sensor be polled?
        should_poll = True

        # Sensor-specific rules
        method: Callable[[], Awaitable[dict[str, Any]]]
        if sensor_type == DEVICES:
            should_poll = False
            method = self._get_connected_devices
        elif sensor_type == AIMESH:
            should_poll = False
            method = self._get_aimesh_devices
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
            MAC: None,
            IP: None,
            ALIAS: None,
            MODEL: None,
            TYPE: None,
            CONNECTED: None,
        }
        self._extra_state_attributes: dict[str, Any] = {}

    @callback
    def update(
        self,
        node_info: AiMeshDevice | None = None,
        event_call: Callable[[str, dict[str, Any] | None], None] | None = None,
    ) -> None:
        """Update AiMesh device."""

        if node_info:
            self.native = node_info
            self._mac = self._extra_state_attributes[MAC] = self.identity[
                MAC
            ] = format_mac(node_info.mac)
            # Online
            if node_info.status:
                # State: router / node
                self._extra_state_attributes[TYPE] = self.identity[
                    TYPE
                ] = node_info.state
                # IP
                self._extra_state_attributes[IP] = self.identity[IP] = node_info.ip
                # Alias
                self._extra_state_attributes[ALIAS] = self.identity[
                    ALIAS
                ] = node_info.alias
                # Model
                self._extra_state_attributes[MODEL] = self.identity[
                    MODEL
                ] = node_info.model
                # Product ID
                self._extra_state_attributes[PRODUCT_ID] = node_info.product_id
                # Node level
                self._extra_state_attributes[LEVEL] = node_info.level
                # Node parent
                if node_info.parent == {}:
                    self._extra_state_attributes[PARENT] = {
                        CONNECTION: WIRED,
                    }
                else:
                    self._extra_state_attributes[PARENT] = node_info.parent
                # Node config
                # self._extra_state_attributes[CONFIG] = node_info.config
                # Access point
                # self._extra_state_attributes[ACCESS_POINT] = node_info.ap
                # Notify reconnect
                if self.identity[CONNECTED] is False and callable(event_call):
                    event_call(
                        CONF_EVENT_NODE_RECONNECTED,
                        self.identity,
                    )
                # Connection status
                self.identity[CONNECTED] = True
            else:
                # Notify disconnect
                if self.identity[CONNECTED] is True and callable(event_call):
                    event_call(
                        CONF_EVENT_NODE_DISCONNECTED,
                        self.identity,
                    )
                # Connection status
                self.identity[CONNECTED] = False
        elif callable(event_call):
            # Notify disconnect
            event_call(
                CONF_EVENT_NODE_DISCONNECTED,
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


class ARConnectedDevice:
    """Representation of an AsusRouter device info."""

    def __init__(
        self,
        mac: str,
        name: str | None = None,
    ) -> None:
        """Initialize an AsusRouter device info."""

        self._mac = mac
        self._name = name
        self._ip: str | None = None
        self.identity: dict[str, Any] = {
            MAC: self._mac,
            IP: self._ip,
            NAME: self._name,
            DEVICE_ATTRIBUTE_CONNECTION_TYPE: None,
            DEVICE_ATTRIBUTE_GUEST: False,
            DEVICE_ATTRIBUTE_GUEST_ID: 0,
            CONNECTED: None,
            NODE: None,
        }
        self._connected: bool = False
        self._extra_state_attributes: dict[str, Any] = {}

    @callback
    def update(
        self,
        dev_info: ConnectedDevice | None = None,
        consider_home: int = 0,
        event_call: Callable[[str, dict[str, Any] | None], None] | None = None,
        connected_call: Callable[[dict[str, Any] | None], None] | None = None,
    ):
        """Update AsusRouter device info."""

        utc_point_in_time = dt_util.utcnow()

        if dev_info:
            self._name = dev_info.name
            self.identity[NAME] = self._name
            # Online
            if dev_info.online:
                self._ip = dev_info.ip
                self.identity[IP] = self._ip
                # Connection time
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_CONNECTION_TIME
                ] = dev_info.connected_since
                self.identity[CONNECTED] = (
                    dev_info.connected_since
                    or self.identity[CONNECTED]
                    or utc_point_in_time
                )
                # Connection type
                con_type = dev_info.connection_type
                if con_type == 0:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_WIRED
                elif con_type == 1:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_2G
                elif con_type == 2:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_5G
                elif con_type == 3:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_5G2
                elif con_type == 4:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_6G
                else:
                    self._extra_state_attributes[
                        DEVICE_ATTRIBUTE_CONNECTION_TYPE
                    ] = CONNECTION_TYPE_UNKNOWN
                # Add connection type to identity
                self.identity[
                    DEVICE_ATTRIBUTE_CONNECTION_TYPE
                ] = self._extra_state_attributes[DEVICE_ATTRIBUTE_CONNECTION_TYPE]
                # Guest network
                guest_id = dev_info.guest or 0
                self._extra_state_attributes[DEVICE_ATTRIBUTE_GUEST] = guest_id != 0
                self.identity[DEVICE_ATTRIBUTE_GUEST] = self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_GUEST
                ]
                self._extra_state_attributes[DEVICE_ATTRIBUTE_GUEST_ID] = guest_id
                self.identity[DEVICE_ATTRIBUTE_GUEST_ID] = guest_id
                # Internet
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_INTERNET_MODE
                ] = dev_info.internet_mode
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_INTERNET
                ] = dev_info.internet_state
                # IP method
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_IP_TYPE
                ] = dev_info.ip_method
                # Last activity
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_LAST_ACTIVITY
                ] = utc_point_in_time
                # RSSI
                self._extra_state_attributes[DEVICE_ATTRIBUTE_RSSI] = dev_info.rssi
                # Connection speed
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_RX_SPEED
                ] = dev_info.rx_speed
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_TX_SPEED
                ] = dev_info.tx_speed
                # Node
                self.identity[NODE] = self._extra_state_attributes[NODE] = (
                    format_mac(dev_info.node) if dev_info.node is not None else None
                )
                # If not connected before
                if self._connected is False and callable(event_call):
                    event_call(
                        CONF_EVENT_DEVICE_RECONNECTED,
                        self.identity,
                    )
                    if callable(connected_call):
                        connected_call(self.identity)
                # Set state
                self._connected = True
            # Offline
            elif (
                DEVICE_ATTRIBUTE_LAST_ACTIVITY in self._extra_state_attributes
                and self._extra_state_attributes[DEVICE_ATTRIBUTE_LAST_ACTIVITY]
                is not None
                and (
                    utc_point_in_time
                    - self._extra_state_attributes[DEVICE_ATTRIBUTE_LAST_ACTIVITY]
                ).total_seconds()
                > consider_home
            ):
                # Notify
                if self._connected is True and callable(event_call):
                    event_call(
                        CONF_EVENT_DEVICE_DISCONNECTED,
                        self.identity,
                    )
                # Reset state
                self._connected = False
                # Reset IP
                self._ip = None
                # Reset attributes
                for attribute in DEVICE_ATTRIBUTES:
                    self._extra_state_attributes[attribute] = None
        elif self._connected:
            # Reset state if needed
            self._connected = (
                utc_point_in_time
                - self._extra_state_attributes[DEVICE_ATTRIBUTE_LAST_ACTIVITY]
            ).total_seconds() < consider_home
            if self._connected is False and callable(event_call):
                event_call(
                    CONF_EVENT_DEVICE_DISCONNECTED,
                    self.identity,
                )
            # Reset IP
            self._ip = None
            # Reset attributes
            for attribute in DEVICE_ATTRIBUTES:
                self._extra_state_attributes[attribute] = None

    @property
    def is_connected(self):
        """Return connected status."""

        return self._connected

    @property
    def mac(self):
        """Return device mac address."""

        return self._mac

    @property
    def name(self):
        """Return device name."""

        return self._name

    @property
    def ip(self):
        """Return device ip address."""

        return self._ip

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""

        return self._extra_state_attributes


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
        self._sensor_handler: ARSensorHandler | None = None
        self._sensor_coordinator: dict[str, Any] = {}

        self._aimesh: dict[str, Any] = {}
        self._devices: dict[str, Any] = {}
        self._aimesh_devices: int = 0
        self._aimesh_devices_list: list[dict[str, Any]] = []
        self._connected_devices: int = 0
        self._connected_devices_list: list[dict[str, Any]] = []
        self._latest_connected: datetime | None = None
        self._latest_connected_list: list[dict[str, Any]] = []
        self._connect_error: bool = False

        # On-clode parameters
        self._on_close: list[Callable] = []

    async def setup(self) -> None:
        """Set up an AsusRouter."""

        _LOGGER.debug("Setting up router")

        # Connect & check connection
        try:
            await self.bridge.async_connect()
        except (OSError, AsusRouterConnectionError) as ex:
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

        # Migrate from 0.21.x and below
        # To be removed in 0.25.0
        # Tracked entities
        entity_reg = er.async_get(self.hass)
        tracked_entries = er.async_entries_for_config_entry(
            entity_reg, self._config_entry.entry_id
        )
        for entry in tracked_entries:
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

            if any(id_to_find in uid for id_to_find in ("lan_speed", "wan_speed")):
                entity_reg.async_remove(entry.entity_id)

        # Initialize services
        await self._init_services()

        # Mode-specific
        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            # Update AiMesh
            await self.update_nodes()

            # Update devices
            await self.update_devices()
        else:
            _LOGGER.debug(
                "Device is in AiMesh node mode. Device tracking and AiMesh monitoring is disabled"
            )

        # Initialize sensor coordinators
        await self._init_sensor_coordinators()

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
        now: datetime | None = None,
    ) -> None:
        """Update all AsusRouter platforms."""

        if self._mode in (ACCESS_POINT, MEDIA_BRIDGE, ROUTER):
            await self.update_devices()
            await self.update_nodes()

    async def update_devices(self) -> None:
        """Update AsusRouter devices tracker."""

        if self._options.get(CONF_TRACK_DEVICES, CONF_DEFAULT_TRACK_DEVICES) is False:
            _LOGGER.debug("Device tracking is disabled")
        else:
            _LOGGER.debug("Device tracking is enabled")

        new_device = False
        _LOGGER.debug("Updating AsusRouter device list for '%s'", self._conf_host)
        try:
            api_devices = await self.bridge.async_get_connected_devices()
            # For Media bridge mode only leave wired devices
            if self._mode == MEDIA_BRIDGE:
                api_devices = {
                    mac: description
                    for mac, description in api_devices.items()
                    if description.connection_type == 0
                }
        except UpdateFailed as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to '%s' for device update: %s",
                    self._conf_host,
                    ex,
                )
            return

        if self._connect_error:
            self._connect_error = False
            _LOGGER.info("Reconnected to '%s'", self._conf_host)

        consider_home = self._options.get(
            CONF_CONSIDER_HOME, CONF_DEFAULT_CONSIDER_HOME
        )

        wrt_devices = {format_mac(mac): dev for mac, dev in api_devices.items()}
        for device_mac, device in self._devices.items():
            dev_info = wrt_devices.pop(device_mac, None)
            device.update(
                dev_info,
                consider_home,
                event_call=self.fire_event,
                connected_call=self.connected_device,
            )

        new_devices = []

        for device_mac, dev_info in wrt_devices.items():
            new_device = True
            device = ARConnectedDevice(device_mac)
            device.update(
                dev_info,
                event_call=self.fire_event,
                connected_call=self.connected_device,
            )
            self._devices[device_mac] = device
            new_devices.append(device)

        for device in new_devices:
            self.fire_event(
                CONF_EVENT_DEVICE_CONNECTED,
                device.identity,
            )

        # Connected devices sensor
        self._connected_devices = 0
        self._connected_devices_list = []
        for mac, device in self._devices.items():
            if device.is_connected:
                self._connected_devices += 1
                self._connected_devices_list.append(device.identity)

        async_dispatcher_send(self.hass, self.signal_device_update)
        if new_device:
            async_dispatcher_send(self.hass, self.signal_device_new)
        await self._update_unpolled_sensors()

    async def update_nodes(self) -> None:
        """Update AsusRouter AiMesh nodes."""

        _LOGGER.debug("Updating AiMesh status for '%s'", self._conf_host)
        try:
            aimesh = await self.bridge.async_get_aimesh_nodes()
        except UpdateFailed as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to '%s' for device update: %s",
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
        self._aimesh_devices = 0
        self._aimesh_devices_list = []
        for mac, node in self._aimesh.items():
            if node.identity[CONNECTED]:
                self._aimesh_devices += 1
            self._aimesh_devices_list.append(node.identity)

        async_dispatcher_send(self.hass, self.signal_aimesh_update)
        if new_node:
            async_dispatcher_send(self.hass, self.signal_aimesh_new)

    async def _init_services(self) -> None:
        """Initialize AsusRouter services."""

        # Adjust WLAN service
        async def async_service_adjust_wlan(service: ServiceCall):
            """Handle WLAN adjust."""

            await self.bridge.async_adjust_wlan(raw=service.data)

        # Parental control service
        async def async_service_device_internet_access(service: ServiceCall):
            """Adjust device internet access."""

            await self.bridge.async_parental_control(raw=service.data)

        # Remove device trackers service
        async def async_service_remove_trackers(service: ServiceCall):
            """Remove device trackers."""

            await self.remove_trackers(raw=service.data)

        # Port forwarding service
        async def async_service_port_forwarding(service: ServiceCall):
            """Adjust port forwarding rules."""

            await self.bridge.async_port_forwarding(raw=service.data)

        # Services only available in control mode
        if self._options.get(CONF_ENABLE_CONTROL, CONF_DEFAULT_ENABLE_CONTROL):
            self.hass.services.async_register(
                DOMAIN, "adjust_wlan", async_service_adjust_wlan
            )

            self.hass.services.async_register(
                DOMAIN, "device_internet_access", async_service_device_internet_access
            )

            if self._mode == ROUTER:
                self.hass.services.async_register(
                    DOMAIN, "port_forwarding", async_service_port_forwarding
                )

        # Services always available
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
        self._sensor_handler.update_device_count(
            self._connected_devices,
            self._connected_devices_list,
            self._latest_connected,
            self._latest_connected_list,
        )
        self._sensor_handler.update_aimesh(
            self._aimesh_devices,
            self._aimesh_devices_list,
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
                self._aimesh_devices,
                self._aimesh_devices_list,
            ):
                await coordinator.async_refresh()

        # Devices
        if DEVICES in self._sensor_coordinator:
            coordinator = self._sensor_coordinator[DEVICES][COORDINATOR]
            if self._sensor_handler.update_device_count(
                self._connected_devices,
                self._connected_devices_list,
                self._latest_connected,
                self._latest_connected_list,
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

    def connected_device_time(self, element: dict[str, Any]) -> datetime:
        """Get connected time for the device."""

        connected = element.get(CONNECTED)
        if isinstance(connected, datetime):
            return connected
        return datetime.utcnow()

    @callback
    def connected_device(
        self,
        identity: dict[str, Any],
    ) -> None:
        """Mark device connected."""

        mac = identity.get(MAC, None)
        if not mac:
            return

        # If device already in list
        for device in self._latest_connected_list:
            if device.get(MAC, None) == mac:
                self._latest_connected_list.remove(device)

        # Sort the list by time
        self._latest_connected_list.sort(key=self.connected_device_time)

        # Add new identity
        self._latest_connected_list.append(identity)

        # Check the size
        while len(self._latest_connected_list) > self._options.get(
            CONF_LATEST_CONNECTED, CONF_DEFAULT_LATEST_CONNECTED
        ):
            self._latest_connected_list.pop(0)

        # Update latest connected time
        self._latest_connected = self._latest_connected_list[-1].get(CONNECTED)

    @callback
    def fire_event(
        self,
        event: str,
        args: dict[str, Any] | None = None,
    ):
        """Fire HA event."""

        if self._options.get(event) is True:
            self.hass.bus.fire(
                f"{DOMAIN}_{event}",
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
                if mac in self._devices:
                    self._devices.pop(mac)
                    _LOGGER.debug("Found and removed")

        # Update devices
        await self.update_devices()

        # Reload device tracker platform
        unload = await self.hass.config_entries.async_unload_platforms(
            self._config_entry, [Platform.DEVICE_TRACKER]
        )
        if unload:
            self.hass.config_entries.async_setup_platforms(
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
    def aimesh(self) -> dict[str, Any]:
        """Return AiMesh nodes."""

        return self._aimesh

    @property
    def devices(self) -> dict[str, Any]:
        """Return devices."""

        return self._devices

    @property
    def mac(self) -> str:
        """Router MAC address."""

        return self._mac

    @property
    def sensor_coordinator(self) -> dict[str, Any]:
        """Return sensor coordinator."""

        return self._sensor_coordinator
