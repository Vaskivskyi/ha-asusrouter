"""AsusRouter Router."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, TypeVar

from asusrouter import AsusRouterConnectionError, ConnectedDevice
from homeassistant.components.device_tracker.const import CONF_CONSIDER_HOME
from homeassistant.components.device_tracker.const import DOMAIN as TRACKER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .bridge import ARBridge
from .const import (
    CONF_REQ_RELOAD,
    CONNECTION_TYPE_2G,
    CONNECTION_TYPE_5G,
    CONNECTION_TYPE_WIRED,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_HTTP,
    DEFAULT_PORT,
    DEFAULT_PORTS,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_ATTRIBUTE_CONNECTION_TIME,
    DEVICE_ATTRIBUTE_CONNECTION_TYPE,
    DEVICE_ATTRIBUTE_INTERNET,
    DEVICE_ATTRIBUTE_INTERNET_MODE,
    DEVICE_ATTRIBUTE_IP_TYPE,
    DEVICE_ATTRIBUTE_LAST_ACTIVITY,
    DEVICE_ATTRIBUTE_RSSI,
    DEVICE_ATTRIBUTE_RX_SPEED,
    DEVICE_ATTRIBUTE_TX_SPEED,
    DEVICE_ATTRIBUTES,
    DOMAIN,
    KEY_COORDINATOR,
    SENSORS_CONNECTED_DEVICES,
    SENSORS_TYPE_DEVICES,
)

_T = TypeVar("_T")


class AsusRouterSensorHandler:
    """Data handler for AsusRouter sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ARBridge,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialise data handler."""

        self._hass = hass
        self._api = api
        self._connected_devices = 0
        self._connected_devices_list: list[str] = list()
        self._scan_interval = timedelta(seconds=scan_interval)

    async def _get_connected_devices(self) -> dict[str, int]:
        """Return number of connected devices."""

        return {
            SENSORS_CONNECTED_DEVICES[0]: self._connected_devices,
            SENSORS_CONNECTED_DEVICES[1]: self._connected_devices_list,
        }

    def update_device_count(
        self,
        conn_devices: int,
        list_devices: list[str],
    ) -> bool:
        """Update connected devices attribute."""

        if (
            self._connected_devices == conn_devices
            and self._connected_devices_list == list_devices
        ):
            return False
        self._connected_devices = conn_devices
        self._connected_devices_list = list_devices
        return True

    async def get_coordinator(
        self,
        sensor_type: str,
        update_method: Callable[[], Awaitable[_T]] | None = None,
    ) -> DataUpdateCoordinator:
        """Find coordinator for the sensor type."""

        should_poll = True

        if sensor_type == SENSORS_TYPE_DEVICES:
            should_poll = False
            method = self._get_connected_devices
        elif update_method is not None:
            method = update_method
        else:
            raise RuntimeError(f"Unknown sensor type: {sensor_type}")

        coordinator = DataUpdateCoordinator(
            self._hass,
            _LOGGER,
            name=sensor_type,
            update_method=method,
            update_interval=self._scan_interval if should_poll else None,
        )
        await coordinator.async_refresh()

        return coordinator


class AsusRouterDevInfo:
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
        self._connected: bool = False
        self._extra_state_attributes: dict[str, Any] = dict()

    def update(
        self,
        dev_info: dict[str, ConnectedDevice] | None = None,
        consider_home: int = 0,
    ):
        """Update AsusRouter device info."""

        utc_point_in_time = dt_util.utcnow()

        if dev_info:
            self._name = dev_info.name
            # Online
            if dev_info.online:
                self._ip = dev_info.ip
                # State
                self._connected = True
                # Connection time
                self._extra_state_attributes[
                    DEVICE_ATTRIBUTE_CONNECTION_TIME
                ] = dev_info.connected_since
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
                # Reset state
                self._connected = False
                # Reset IP
                self._ip = None
                # Reset attributes
                for el in DEVICE_ATTRIBUTES:
                    self._extra_state_attributes[el] = None
        elif self._connected:
            # Reset state if needed
            self._connected = (
                utc_point_in_time
                - self._extra_state_attributes[DEVICE_ATTRIBUTE_LAST_ACTIVITY]
            ).total_seconds() < consider_home
            # Reset IP
            self._ip = None
            ## Reset attributes
            for el in DEVICE_ATTRIBUTES:
                self._extra_state_attributes[el] = None

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
        """Return extrar state attributes."""

        return self._extra_state_attributes


class AsusRouterObj:
    """Representatiion of AsusRouter."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the object."""

        self.hass = hass
        self._entry = entry

        self._api: ARBridge | None = None

        self._options = entry.options.copy()

        self._host: str = entry.data[CONF_HOST]
        self._port: str = self._options[CONF_PORT]

        self._name: str = self._options[CONF_NAME]

        self._mac: str | None = None
        self._model: str = "ASUS Router"
        self._vendor: str = "ASUSTek"
        self._serial: str | None = None
        self._firmware: str | None = None

        self._devices: dict[str, Any] = {}
        self._connected_devices: int = 0
        self._connected_devices_list: list[str] = list()
        self._connect_error: bool = False

        self._sensors_data_handler: AsusRouterSensorHandler | None = None
        self._sensors_coordinator: dict[str, Any] = {}

        self._on_close: list[Callable] = []

        if self._port == DEFAULT_PORT:
            self._port = (
                DEFAULT_PORTS["ssl"]
                if self._options[CONF_VERIFY_SSL]
                else DEFAULT_PORTS["no_ssl"]
            )

    async def setup(self) -> None:
        """Setup an AsusRouter object."""

        self._api = ARBridge(self.hass, dict(self._entry.data), self._options)

        try:
            await self._api.async_connect()
        except (OSError, AsusRouterConnectionError) as ex:
            raise ConfigEntryNotReady from ex

        if not self._api.is_connected:
            raise ConfigEntryNotReady

        # Services
        async def async_service_reboot(service: ServiceCall):
            """Handle reboot."""

            await self._api.async_reboot()

        self.hass.services.async_register(
            DOMAIN, "service_reboot", async_service_reboot
        )

        self._mac = await self._api.get_mac()
        self._serial = await self._api.get_serial()
        self._model = await self._api.get_model()
        self._vendor = await self._api.get_vendor()
        self._firmware = await self._api.get_firmware()

        if self._model is not None:
            if self._name is None or self._name == "":
                self._name = self._model

        # Load tracked entities from registry
        entity_reg = er.async_get(self.hass)
        track_entries = er.async_entries_for_config_entry(
            entity_reg, self._entry.entry_id
        )
        for entry in track_entries:

            if entry.domain != TRACKER_DOMAIN:
                continue
            device_mac = format_mac(entry.unique_id)

            # migrate entity unique ID if wrong formatted
            if device_mac != entry.unique_id:
                existing_entity_id = entity_reg.async_get_entity_id(
                    DOMAIN, TRACKER_DOMAIN, device_mac
                )
                if existing_entity_id:
                    # entity with uniqueid properly formatted already
                    # exists in the registry, we delete this duplicate
                    entity_reg.async_remove(entry.entity_id)
                    continue

                entity_reg.async_update_entity(
                    entry.entity_id, new_unique_id=device_mac
                )

            self._devices[device_mac] = AsusRouterDevInfo(
                device_mac, entry.original_name
            )

        # Update devices
        await self.update_devices()

        # Initialise sensors
        await self.init_sensors_coordinator()

        self.async_on_close(
            async_track_time_interval(
                self.hass,
                self.update_all,
                timedelta(seconds=self._options[CONF_SCAN_INTERVAL]),
            )
        )

    async def update_all(
        self,
        now: datetime | None = None,
    ) -> None:
        """Update all AsusRouter platforms."""

        await self.update_devices()

    async def update_devices(self) -> None:
        """Update AsusRouter devices tracker."""

        new_device = False
        _LOGGER.debug(f"Updating AsusRouter device list for '{self._host}'")
        try:
            api_devices = await self._api.async_get_connected_devices()
        except OSError as ex:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    f"Error connecting to '{self._host}' for device update: {ex}"
                )
            return

        if self._connect_error:
            self._connect_error = False
            _LOGGER.info(f"Reconnected to '{self._host}'")

        self._connected_devices = 0
        self._connected_devices_list = list()
        for device in api_devices:
            if api_devices[device].online:
                self._connected_devices += 1
                self._connected_devices_list.append(
                    f"{api_devices[device].mac}/{api_devices[device].ip}/{api_devices[device].name}"
                )
        consider_home = self._options.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME)

        wrt_devices = {format_mac(mac): dev for mac, dev in api_devices.items()}
        for device_mac, device in self._devices.items():
            dev_info = wrt_devices.pop(device_mac, None)
            device.update(dev_info, consider_home)

        for device_mac, dev_info in wrt_devices.items():
            new_device = True
            device = AsusRouterDevInfo(device_mac)
            device.update(dev_info)
            self._devices[device_mac] = device

        async_dispatcher_send(self.hass, self.signal_device_update)
        if new_device:
            async_dispatcher_send(self.hass, self.signal_device_new)
        await self._update_unpolled_sensors()

    async def init_sensors_coordinator(self) -> None:
        """Initialize AsusRouter sensors coordinators."""

        if self._sensors_data_handler:
            return

        self._sensors_data_handler = AsusRouterSensorHandler(
            self.hass, self._api, self._options[CONF_SCAN_INTERVAL]
        )
        self._sensors_data_handler.update_device_count(
            self._connected_devices, self._connected_devices_list
        )

        sensors_types = await self._api.async_get_available_sensors()
        sensors_types[SENSORS_TYPE_DEVICES] = {"sensors": SENSORS_CONNECTED_DEVICES}

        for sensor_type, sensor_def in sensors_types.items():
            if not (sensor_names := sensor_def.get("sensors")):
                continue
            coordinator = await self._sensors_data_handler.get_coordinator(
                sensor_type, update_method=sensor_def.get("method")
            )
            self._sensors_coordinator[sensor_type] = {
                KEY_COORDINATOR: coordinator,
                sensor_type: sensor_names,
            }

    async def _update_unpolled_sensors(self) -> None:
        """Request refresh for AsusRouter unpolled sensors."""

        if not self._sensors_data_handler:
            return

        if SENSORS_TYPE_DEVICES in self._sensors_coordinator:
            coordinator = self._sensors_coordinator[SENSORS_TYPE_DEVICES][
                KEY_COORDINATOR
            ]
            if self._sensors_data_handler.update_device_count(
                self._connected_devices, self._connected_devices_list
            ):
                await coordinator.async_refresh()

    async def close(self) -> None:
        """Close the connection."""

        if self._api is not None:
            await self._api.async_disconnect()
        self._api = None

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

        req_reload = False
        for name, new_opt in new_options.items():
            if name in CONF_REQ_RELOAD:
                old_opt = self._options.get(name)
                if not old_opt or old_opt != new_opt:
                    req_reload = True
                    break

        self._options.update(new_options)
        return req_reload

    @property
    def device_info(self) -> DeviceInfo:
        """Device information."""

        return DeviceInfo(
            identifiers={
                (DOMAIN, self._mac),
                (DOMAIN, self._serial),
            },
            name=self._name,
            model=self._model,
            manufacturer=self._vendor,
            sw_version=self._firmware,
            configuration_url="{}://{}:{}".format(
                DEFAULT_HTTP["ssl"]
                if self._options[CONF_VERIFY_SSL]
                else DEFAULT_HTTP["no_ssl"],
                self._host,
                self._port,
            ),
        )

    @property
    def signal_device_new(self) -> str:
        """Event specific per AsusRouter entry to signal new device."""

        return f"{DOMAIN}-device-new"

    @property
    def signal_device_update(self) -> str:
        """Event specific per AsusRouter entry to signal updates in devices."""

        return f"{DOMAIN}-device-update"

    @property
    def devices(self) -> dict[str, Any]:
        """Return devices."""

        return self._devices

    @property
    def host(self) -> str:
        """Router hostname."""

        return self._host

    @property
    def api(self) -> ARBridge:
        """Router API."""

        return self._api
