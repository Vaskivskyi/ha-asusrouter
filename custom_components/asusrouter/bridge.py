"""AsusRouter bridge."""

from __future__ import annotations

import aiohttp
from datetime import datetime
import logging
from typing import Any, Awaitable, Callable, TypeVar

from asusrouter import AsusDevice, AsusRouter, AsusRouterError, ConnectedDevice
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import helpers
from .const import (
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_ENABLE_CONTROL,
    CONF_ENABLE_MONITOR,
    DEFAULT_CACHE_TIME,
    DEFAULT_ENABLE_CONTROL,
    DEFAULT_ENABLE_MONITOR,
    DEFAULT_PORT,
    DEFAULT_SENSORS,
    DEFAULT_VERIFY_SSL,
    SENSORS_LIGHT,
    SENSORS_MISC,
    SENSORS_NETWORK_STAT,
    SENSORS_PORTS,
    SENSORS_RAM,
    SENSORS_SYSINFO,
    SENSORS_TYPE_CPU,
    SENSORS_TYPE_LIGHT,
    SENSORS_TYPE_MISC,
    SENSORS_TYPE_NETWORK_STAT,
    SENSORS_TYPE_PORTS,
    SENSORS_TYPE_RAM,
    SENSORS_TYPE_SYSINFO,
    SENSORS_TYPE_TEMPERATURE,
    SENSORS_TYPE_VPN,
    SENSORS_TYPE_WAN,
    SENSORS_TYPE_WLAN,
    SENSORS_VPN,
    SENSORS_WAN,
    SENSORS_WLAN,
)

_T = TypeVar("_T")

_LOGGER = logging.getLogger(__name__)


class ARBridge:
    """Bridge for AsusRouter library."""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: dict[str, Any],
        options: dict[str, Any] = dict(),
    ) -> None:
        """Initialize bridge."""

        super().__init__()
        self._configs = configs.copy()
        self._configs.update(options)
        session = async_get_clientsession(hass)
        self._api = self._get_api(self._configs, session)
        self._host = self._configs[CONF_HOST]
        self._identity: AsusDevice | None = None

    @staticmethod
    def _get_api(configs: dict[str, Any], session: aiohttp.ClientSession) -> AsusRouter:
        """Get AsusRouter API."""

        return AsusRouter(
            host=configs[CONF_HOST],
            username=configs[CONF_USERNAME],
            password=configs[CONF_PASSWORD],
            port=configs.get(CONF_PORT, DEFAULT_PORT),
            use_ssl=configs[CONF_SSL],
            cert_check=configs.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            cert_path=configs.get(CONF_CERT_PATH, ""),
            cache_time=configs.get(CONF_CACHE_TIME, DEFAULT_CACHE_TIME),
            enable_monitor=configs.get(CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR),
            enable_control=configs.get(CONF_ENABLE_CONTROL, DEFAULT_ENABLE_CONTROL),
            session=session,
        )

    @property
    def identity(self) -> AsusDevice:
        """Return identity."""

        return self._identity

    @property
    def is_connected(self) -> bool:
        """Return connection status."""

        return self.api.connected

    @property
    def api(self) -> AsusRouter:
        """Return API."""

        return self._api

    ### CONNECTION ->
    async def async_connect(self) -> None:
        """Connect to the device."""

        try:
            await self.api.async_connect()
            self._identity = await self.api.async_get_identity()
        except Exception as ex:
            raise ConfigEntryNotReady from ex

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""

        await self.api.async_disconnect()

    async def async_clean(self) -> None:
        """Cleanup."""

        await self.api.connection.async_cleanup()

    ### <- CONNECTION

    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Get a dictionary of available sensors."""

        sensors_types = {
            SENSORS_TYPE_CPU: {
                "sensors": await self._get_sensors_cpu(),
                "method": self._get_data_cpu,
            },
            SENSORS_TYPE_LIGHT: {
                "sensors": SENSORS_LIGHT,
                "method": self._get_data_light,
            },
            SENSORS_TYPE_MISC: {"sensors": SENSORS_MISC, "method": self._get_data_misc},
            SENSORS_TYPE_NETWORK_STAT: {
                "sensors": await self._get_sensors_network_stat(),
                "method": self._get_data_network,
            },
            SENSORS_TYPE_PORTS: {
                "sensors": await self._get_sensors_ports(),
                "method": self._get_data_ports,
            },
            SENSORS_TYPE_RAM: {"sensors": SENSORS_RAM, "method": self._get_data_ram},
            SENSORS_TYPE_SYSINFO: {
                "sensors": await self._get_sensors_sysinfo(),
                "method": self._get_data_sysinfo,
            },
            SENSORS_TYPE_TEMPERATURE: {
                "sensors": await self._get_sensors_temperature(),
                "method": self._get_data_temperature,
            },
            SENSORS_TYPE_VPN: {
                "sensors": await self._get_sensors_vpn(),
                "method": self._get_data_vpn,
            },
            SENSORS_TYPE_WAN: {"sensors": SENSORS_WAN, "method": self._get_data_wan},
            SENSORS_TYPE_WLAN: {
                "sensors": await self._get_sensors_wlan(),
                "method": self._get_data_wlan,
            },
        }
        return sensors_types

    ### GET DATA FROM DEVICE ->
    # General method
    async def _get_data(
        self,
        method: Callable[[], Awaitable[_T]],
        process: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Get data from the device."""

        try:
            raw = await method()
            if process is not None:
                return process(raw)
            return raw
        except (OSError, ValueError, AsusRouterError) as ex:
            raise UpdateFailed(ex) from ex

    # Connected devices
    async def async_get_connected_devices(self) -> dict[str, ConnectedDevice]:
        """Get dict of connected devices."""

        return await self._get_data(self.api.async_get_devices)

    # Sensor-specific methods
    async def _get_data_cpu(self) -> dict[str, Any]:
        """Get CPU data from the device."""

        return await self._get_data(self.api.async_get_cpu)

    async def _get_data_light(self) -> dict[str, Any]:
        """Get light data from the device."""

        return {"led": self.api.led}

    async def _get_data_misc(self) -> dict[str, Any]:
        """Get MISC sensors from the device."""

        return {"boottime": datetime.fromisoformat(self.api.boottime)}

    async def _get_data_network(self) -> dict[str, Any]:
        """Get network data from device."""

        return await self._get_data(self.api.async_get_network)

    async def _get_data_ram(self) -> dict[str, Any]:
        """Get RAM data from the device."""

        return await self._get_data(self.api.async_get_ram)

    async def _get_data_ports(self) -> dict[str, dict[str, int]]:
        """Get ports data from the device."""

        return await self._get_data(self.api.async_get_ports, self._process_data_ports)

    async def _get_data_sysinfo(self) -> dict[str, Any]:
        """Get sysinfo data from the device."""

        return await self._get_data(self.api.async_get_sysinfo)

    async def _get_data_temperature(self) -> dict[str, Any]:
        """Get temperarture data from the device."""

        return await self._get_data(self.api.async_get_temperature)

    async def _get_data_vpn(self) -> dict[str, Any]:
        """Get VPN data from the device."""

        return await self._get_data(self.api.async_get_vpn, self._process_data_vpn)

    async def _get_data_wan(self) -> dict[str, Any]:
        """Get WAN data from the device."""

        return await self._get_data(self.api.async_get_wan)

    async def _get_data_wlan(self) -> dict[str, Any]:
        """Get WLAN data from the device."""

        return await self._get_data(self.api.async_get_wlan)

    ### <- GET DATA FROM DEVICE

    ### PROCESS DATA ->
    @staticmethod
    def _process_data_ports(raw: dict[str, Any]) -> dict[str, Any]:
        """Process ports data."""

        data = dict()
        for type in SENSORS_PORTS:
            if type in raw:
                _total = f"{type}_total"
                data[_total] = 0
                for port in raw[type]:
                    data[f"{type}_{port}"] = raw[type][port]
                    data[_total] += raw[type][port]
                if data[_total] > 0:
                    data[type] = True
        return data

    @staticmethod
    def _process_data_vpn(raw: dict[str, Any]) -> dict[str, Any]:
        """Process VPN data."""

        return helpers.as_dict(helpers.flatten_dict(raw))

    ### <- PROCESS DATA

    ### GET SENSORS LIST ->
    async def _get_sensors(
        self,
        method: Callable[[], Awaitable[_T]],
        process: Callable[[list[str]], list[str]] | None = None,
        type: str | None = None,
        defaults: bool = False,
    ) -> list[str]:
        """Get the available sensors."""

        try:
            sensors = await method()
            if process is not None:
                sensors = process(sensors)
            _LOGGER.debug(f"Available `{type}` sensors: {sensors}")
        except Exception as ex:
            sensors = DEFAULT_SENSORS[type] if defaults else list()
            _LOGGER.debug(
                f"Cannot get available `{type}` sensors with exception: {ex}. Will use the following list: {sensors}"
            )
        return sensors

    async def _get_sensors_cpu(self) -> list[str]:
        """Get the available CPU sensors."""

        return await self._get_sensors(
            self.api.async_get_cpu_labels, type=SENSORS_TYPE_CPU, defaults=True
        )

    async def _get_sensors_network_stat(self) -> list[str]:
        """Get the available network stat sensors."""

        return await self._get_sensors(
            self.async_get_network_interfaces,
            self._process_sensors_network_stat,
            type=SENSORS_TYPE_NETWORK_STAT,
        )

    async def _get_sensors_ports(self) -> list[str]:
        """Get the available ports sensors."""

        return await self._get_sensors(
            self.api.async_get_ports,
            self._process_sensors_ports,
            type=SENSORS_TYPE_PORTS,
        )

    async def _get_sensors_sysinfo(self) -> list[str]:
        """Get the available sysinfo sensors."""

        return await self._get_sensors(
            self.api.async_get_sysinfo,
            self._process_sensors_sysinfo,
            type=SENSORS_TYPE_SYSINFO,
        )

    async def _get_sensors_temperature(self) -> list[str]:
        """Get the available temperature sensors."""

        return await self._get_sensors(
            self.api.async_get_temperature_labels, type=SENSORS_TYPE_TEMPERATURE
        )

    async def _get_sensors_vpn(self) -> list[str]:
        """Get the available VPN sensors."""

        return await self._get_sensors(
            self.api.async_get_vpn, self._process_sensors_vpn, type=SENSORS_TYPE_VPN
        )

    async def _get_sensors_wlan(self) -> list[str]:
        """Get the available WLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_wlan_ids,
            self._process_sensors_wlan,
            type=SENSORS_TYPE_WLAN,
        )

    ### <- GET SENSORS LIST

    ### PROCESS SENSORS LIST->
    @staticmethod
    def _process_sensors_network_stat(raw: list[str]) -> list[str]:
        """Process network stat sensors."""

        sensors = list()
        for label in raw:
            for el in SENSORS_NETWORK_STAT:
                sensors.append(f"{label}_{el}")
        return sensors

    @staticmethod
    def _process_sensors_ports(raw: list[str]) -> list[str]:
        """Process ports sensors."""

        sensors = list()
        for type in SENSORS_PORTS:
            if type in raw:
                sensors.append(type)
                sensors.append(f"{type}_total")
                for port in raw[type]:
                    sensors.append(f"{type}_{port}")
        return sensors

    @staticmethod
    def _process_sensors_sysinfo(raw: list[str]) -> list[str]:
        """Process SysInfo sensors."""

        sensors = list()
        for type in SENSORS_SYSINFO:
            if type in raw:
                sensors.append(type)
        return sensors

    @staticmethod
    def _process_sensors_vpn(raw: list[str]) -> list[str]:
        """Process VPN sensors."""

        sensors = list()
        for vpn in raw:
            for sensor in SENSORS_VPN:
                sensors.append(f"{vpn}_{sensor}")
            sensors.append(f"{vpn}_state")
        return sensors

    @staticmethod
    def _process_sensors_wlan(raw: list[str]) -> list[str]:
        """Process WLAN sensors."""

        sensors = list()
        for id in raw:
            for sensor in SENSORS_WLAN:
                sensors.append(f"wl{id}_{sensor}")
            sensors.append(f"wl{id}_radio")
        return sensors

    ### <- PROCESS SENSORS LSIT

    ### GENERAL USAGE METHODS ->
    async def async_get_network_interfaces(self) -> list[str]:
        """Get the list of network interfaces of the device."""

        return await self.api.async_get_network_labels()

    ### <- GENERAL USAGE METHODS

    ### SERVICES ->
    async def async_reboot(self) -> bool:
        """Reboot the device."""

        return await self.api.async_service_reboot()

    ### <- SERVICES
