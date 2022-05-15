"""Asus Router"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from collections.abc import Callable, Awaitable
from datetime import datetime, timedelta, tzinfo, timezone
from typing import Any, TypeVar

from homeassistant.components.device_tracker.const import (
    CONF_CONSIDER_HOME,
    DEFAULT_CONSIDER_HOME,
    DOMAIN as TRACKER_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_VERIFY_SSL,
    CONF_SSL,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .bridge import AsusRouterBridge
from .const import (
    CONF_CACHE_TIME,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    CONF_REQ_RELOAD,
    DEFAULT_CACHE_TIME,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_ENABLE_MONITOR,
    DEFAULT_HTTP,
    DEFAULT_PORT,
    DEFAULT_PORTS,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    KEY_COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    SENSORS_CONNECTED_DEVICES,
    SENSORS_TYPE_DEVICES,
)


from asusrouter import ConnectedDevice


_T = TypeVar("_T")


class AsusRouterSensorHandler:
    """Data handler for AsusRouter sensors"""

    def __init__(self, hass : HomeAssistant, api : AsusRouterBridge) -> None:
        """Initialise data handler"""

        self._hass = hass
        self._api = api
        self._connected_devices = 0


    async def _get_connected_devices(self) -> dict[str, int]:
        """Return number of connected devices"""

        return {SENSORS_CONNECTED_DEVICES[0]: self._connected_devices}


    def update_device_count(self, conn_devices : int) -> bool:
        """Update connected devices attribute"""

        if self._connected_devices == conn_devices:
            return False
        self._connected_devices = conn_devices
        return True


    async def get_coordinator(self, sensor_type : str, update_method : Callable[[], Awaitable[_T]] | None = None) -> DataUpdateCoordinator:
        """Find coordinator for the sensor type"""

        should_poll = True

        if sensor_type == SENSORS_TYPE_DEVICES:
            should_poll = False
            method = self._get_connected_devices
        elif update_method is not None:
            method = update_method
        else:
            raise RuntimeError("Unknown sensor type: {}".format(sensor_type))

        coordinator = DataUpdateCoordinator(
            self._hass,
            _LOGGER,
            name = sensor_type,
            update_method = method,
            update_interval = DEFAULT_SCAN_INTERVAL if should_poll else None,
        )
        await coordinator.async_refresh()

        return coordinator


class AsusRouterDevInfo:
    """Representation of an AsusRouter device info"""

    def __init__(self, mac : str, name : str | None = None) -> None:
        """Initialize an AsusRouter device info"""

        self._mac = mac
        self._name = name
        self._ip : str | None = None
        self._last_activity : datetime | None = None
        self._connected : bool = False
        self._connection_time : str | None = None


    def update(self, dev_info : dict[str, ConnectedDevice] | None = None, consider_home : int = 0):
        """Update AsusRouter device info"""

        utc_point_in_time = dt_util.utcnow()

        if dev_info:
            self._name = dev_info.name
            self._ip = dev_info.ip
            self._last_activity = utc_point_in_time
            if dev_info.online:
                self._connected = True
            if dev_info.connected_since:
                ### EDIT THIS WHEN
                ### AsusRouter library fixes datetime object to have timezone
                self._connection_time = dev_info.connected_since.replace(tzinfo = timezone.utc)
        elif self._connected:
            self._connected = (
                utc_point_in_time - self._last_activity
            ).total_seconds() < consider_home
            self._ip = None


    @property
    def is_connected(self):
        """Return connected status"""

        return self._connected


    @property
    def mac(self):
        """Return device mac address"""

        return self._mac


    @property
    def name(self):
        """Return device name"""

        return self._name


    @property
    def ip(self):
        """Return device ip address"""

        return self._ip


    @property
    def last_activity(self):
        """Return device last activity"""

        return self._last_activity


    @property
    def connection_time(self):
        """Return connection time"""

        return self._connection_time


class AsusRouterObj:
    """Representatiion of AsusRouter"""

    def __init__(self, hass : HomeAssistant, entry : ConfigEntry) -> None:
        """Initialize the object"""

        self.hass = hass
        self._entry = entry

        self._api : AsusRouterBridge | None = None
        self._host : str = entry.data[CONF_HOST]
        self._port : str = entry.data[CONF_PORT]

        self._name : str = entry.data[CONF_NAME]

        self._mac : str | None = None
        self._model : str = "ASUS Router"
        self._vendor : str = "ASUSTek"
        self._serial : str | None = None
        self._firmware : str | None = None

        self._devices : dict[str, Any] = {}
        self._connected_devices : int = 0
        self._connect_error : bool = False

        self._sensors_data_handler : AsusRouterSensorHandler | None = None
        self._sensors_coordinator : dict[str, Any] = {}

        self._on_close : list[Callable] = []

        self._options = {
            CONF_SSL: DEFAULT_SSL,
            CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
            CONF_CACHE_TIME: DEFAULT_CACHE_TIME,
            CONF_ENABLE_MONITOR: DEFAULT_ENABLE_MONITOR, 
            CONF_ENABLE_CONTROL: DEFAULT_ENABLE_CONTROL,
        }

        self._options.update(entry.options)

        if self._port == DEFAULT_PORT:
            self._port = DEFAULT_PORTS["ssl"] if self._options[CONF_VERIFY_SSL] else DEFAULT_PORTS["no_ssl"]


    async def setup(self) -> None:
        """Setup an AsusRouter object"""

        self._api = AsusRouterBridge.get_bridge(self.hass, dict(self._entry.data), self._options)

        try:
            await self._api.async_connect()
        except OSError as ex:
            raise ConfigEntryNotReady from ex

        if not self._api.is_connected:
            raise ConfigEntryNotReady

        self._mac = await self._api.get_mac()
        self._serial = await self._api.get_serial()
        self._model = await self._api.get_model()
        self._vendor = await self._api.get_vendor()
        self._firmware = await self._api.get_firmware()

        if self._model is not None:
            if (
                self._name is None
                or self._name == ""
            ):
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

            self._devices[device_mac] = AsusRouterDevInfo(device_mac, entry.original_name)

        # Update devices
        await self.update_devices()

        # Initialise sensors
        await self.init_sensors_coordinator()

        self.async_on_close(
            async_track_time_interval(self.hass, self.update_all, DEFAULT_SCAN_INTERVAL)
        )


    async def update_all(self, now : datetime | None = None) -> None:
        """Update all AsusRouter platforms"""

        await self.update_devices()


    async def update_devices(self) -> None:
        """Update AsusRouter devices tracker"""

        new_device = False
        _LOGGER.debug("Checking devices for ASUS router %s", self._host)
        try:
            api_devices = await self._api.async_get_connected_devices()
        except OSError as exc:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error(
                    "Error connecting to ASUS router %s for device update: %s",
                    self._host,
                    exc,
                )
            return

        if self._connect_error:
            self._connect_error = False
            _LOGGER.info("Reconnected to ASUS router %s", self._host)

        self._connected_devices = 0
        for device in api_devices:
            if api_devices[device].online:
                self._connected_devices += 1
        consider_home = self._options.get(
            CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME.total_seconds()
        )

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
        """Initialize AsusRouter sensors coordinators"""

        if self._sensors_data_handler:
            return

        self._sensors_data_handler = AsusRouterSensorHandler(self.hass, self._api)
        self._sensors_data_handler.update_device_count(self._connected_devices)

        sensors_types = await self._api.async_get_available_sensors()
        sensors_types[SENSORS_TYPE_DEVICES] = {"sensors": SENSORS_CONNECTED_DEVICES}

        for sensor_type, sensor_def in sensors_types.items():
            if not (sensor_names := sensor_def.get("sensors")):
                continue
            coordinator = await self._sensors_data_handler.get_coordinator(sensor_type, update_method = sensor_def.get("method"))
            self._sensors_coordinator[sensor_type] = {
                KEY_COORDINATOR: coordinator,
                sensor_type: sensor_names,
            }


    async def _update_unpolled_sensors(self) -> None:
        """Request refresh for AsusWrt unpolled sensors."""

        if not self._sensors_data_handler:
            return

        if SENSORS_TYPE_DEVICES in self._sensors_coordinator:
            coordinator = self._sensors_coordinator[SENSORS_TYPE_DEVICES][KEY_COORDINATOR]
            if self._sensors_data_handler.update_device_count(self._connected_devices):
                await coordinator.async_refresh()


    async def close(self) -> None:
        """Close the connection"""

        if self._api is not None:
            self._api.async_disconnect()
        self._api = None

        for func in self._on_close:
            func()
        self._on_close.clear()


    @callback
    def async_on_close(self, func : CALLBACK_TYPE) -> None:
        """Functions on router close"""

        self._on_close.append(func)


    def update_options(self, new_options: dict) -> bool:
        """Update router options"""

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
        """Device information"""

        return DeviceInfo(
            identifiers = {
                (DOMAIN, self._mac),
                (DOMAIN, self._serial),
                },
            name = self._name,
            model = self._model,
            manufacturer = self._vendor,
            sw_version = self._firmware,
            configuration_url = "{}://{}:{}".format(
                DEFAULT_HTTP["ssl"] if self._options[CONF_VERIFY_SSL] else DEFAULT_HTTP["no_ssl"],
                self._host,
                self._port
            ),
        )


    @property
    def signal_device_new(self) -> str:
        """Event specific per AsusWrt entry to signal new device."""

        return f"{DOMAIN}-device-new"


    @property
    def signal_device_update(self) -> str:
        """Event specific per AsusWrt entry to signal updates in devices."""

        return f"{DOMAIN}-device-update"


    @property
    def devices(self) -> dict[str, Any]:
        """Return devices."""

        return self._devices


    @property
    def host(self) -> str:
        """Router hostname"""

        return self._host


    @property
    def api(self) -> AsusRouterBridge:
        """Router API"""

        return self._api


