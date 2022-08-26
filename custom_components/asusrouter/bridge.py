"""AsusRouter bridge."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

import aiohttp
from datetime import datetime
from typing import Any

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
    def _get_api(
        configs: dict[str, Any],
        session: aiohttp.ClientSession
    ) -> AsusRouter:
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
    def is_connected(self) -> bool:
        """Get connected status."""

        return self._api.connected

    async def async_connect(self) -> None:
        """Connect to the device."""

        try:
            await self._api.async_connect()
            self._identity = await self._async_get_device_identity()
        except AsusRouterError as ex:
            raise ex
        except Exception as ex:
            raise ConfigEntryNotReady from ex

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""

        await self._api.async_disconnect()

    async def async_clean(self) -> None:
        """Cleanup."""

        await self._api.connection.async_cleanup()

    async def _async_get_device_identity(self) -> AsusDevice:
        """Load device identity."""

        return await self._api.async_get_identity()

    async def async_get_connected_devices(self) -> dict[str, ConnectedDevice]:
        """Get dict of connected devices."""

        try:
            api_devices = await self._api.async_get_devices()
        except Exception as ex:
            raise UpdateFailed(ex) from ex

        return api_devices

    async def get_firmware(self) -> str | None:
        """Get firmware information."""

        return self._identity.firmware()

    async def get_mac(self) -> str | None:
        """Get MAC information."""

        return self._identity.mac

    async def get_serial(self) -> str | None:
        """Get serial information."""

        return self._identity.serial

    async def get_model(self) -> str | None:
        """Get model information."""

        return self._identity.model

    async def get_vendor(self) -> str | None:
        """Get vendor information."""

        return self._identity.brand

    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Get a dictionary of available sensors."""

        sensors_types = {
            SENSORS_TYPE_CPU: {
                "sensors": await self._get_cpu_sensors(),
                "method": self._get_cpu,
            },
            SENSORS_TYPE_RAM: {"sensors": SENSORS_RAM, "method": self._get_ram},
            SENSORS_TYPE_NETWORK_STAT: {
                "sensors": await self._get_network_stat_sensors(),
                "method": self._get_network_stat,
            },
            SENSORS_TYPE_MISC: {"sensors": SENSORS_MISC, "method": self._get_misc},
            SENSORS_TYPE_PORTS: {
                "sensors": await self._get_ports_sensors(),
                "method": self._get_ports,
            },
            SENSORS_TYPE_VPN: {
                "sensors": await self._get_vpn_sensors(),
                "method": self._get_vpn,
            },
            SENSORS_TYPE_WAN: {"sensors": SENSORS_WAN, "method": self._get_wan},
            SENSORS_TYPE_WLAN: {
                "sensors": await self._get_wlan_sensors(),
                "method": self._get_wlan,
            },
            SENSORS_TYPE_TEMPERATURE: {
                "sensors": await self._get_temperature_sensors(),
                "method": self._get_temperature,
            },
            SENSORS_TYPE_SYSINFO: {
                "sensors": await self._get_sysinfo_sensors(),
                "method": self._get_sysinfo,
            },
            SENSORS_TYPE_LIGHT: {
                "sensors": SENSORS_LIGHT,
                "method": self._get_light,
            },
        }
        return sensors_types

    ### GET DATA FROM DEVICE ->
    async def _get_cpu(self) -> dict[str, Any]:
        """Get CPU data from the device."""

        try:
            data = await self._api.async_get_cpu()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_ram(self) -> dict[str, Any]:
        """Get RAM data from the device."""

        try:
            data = await self._api.async_get_ram()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_network_stat(self) -> dict[str, Any]:
        """Get network data from device."""

        try:
            data = await self._api.async_get_network()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_misc(self) -> dict[str, Any]:
        """Get MISC sensors from the device."""

        data = dict()
        await self._api.async_monitor_misc()
        data["boottime"] = datetime.fromisoformat(self._api.boottime)

        return data

    async def _get_ports(self) -> dict[str, dict[str, int]]:
        """Get ports status from the device."""

        data = dict()
        try:
            raw = await self._api.async_get_ports()

            for type in SENSORS_PORTS:
                if type in raw:
                    _total = f"{type}_total"
                    data[_total] = 0
                    for port in raw[type]:
                        data[f"{type}_{port}"] = raw[type][port]
                        data[_total] += raw[type][port]
                    if data[_total] > 0:
                        data[type] = True
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_vpn(self) -> dict[str, Any]:
        """Get VPN data from the device."""

        try:
            data = helpers.as_dict(
                helpers.flatten_dict(await self._api.async_get_vpn())
            )
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_wan(self) -> dict[str, Any]:
        """Get WAN data from the device."""

        try:
            data = await self._api.async_get_wan()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_wlan(self) -> dict[str, Any]:
        """Get WLAN data from the device."""

        try:
            data = await self._api.async_get_wlan()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_temperature(self) -> dict[str, Any]:
        """Get temperarture data from the device."""

        try:
            data = await self._api.async_get_temperature()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_sysinfo(self) -> dict[str, Any]:
        """Get sysinfo data from the device."""

        try:
            data = await self._api.async_get_sysinfo()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data

    async def _get_light(self) -> dict[str, Any]:
        """Get light data from the device."""

        return {"led": self._api.led}

    ### <- GET DATA FROM DEVICE

    ### GET SENSORS LIST ->
    async def _get_cpu_sensors(self):
        """Get the available CPU sensors."""

        try:
            sensors = await self._api.async_get_cpu_labels()
            _LOGGER.debug(f"Available CPU sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(f"Cannot get available CPU sensors for {self._host}: {ex}")
            sensors = ["total"]
        return sensors

    async def _get_network_stat_sensors(self):
        """Get the available network stat sensors."""

        try:
            sensors = []
            labels = await self.async_get_network_interfaces()
            for label in labels:
                for el in SENSORS_NETWORK_STAT:
                    sensors.append(f"{label}_{el}")
            _LOGGER.debug(f"Available network stat sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(
                f"Cannot get available network stat sensors for {self._host}: {ex}"
            )
        return sensors

    async def _get_ports_sensors(self):
        """Get the available ports sensors."""

        try:
            sensors = []
            data = await self._api.async_get_ports()
            for type in SENSORS_PORTS:
                if type in data:
                    sensors.append(type)
                    sensors.append(f"{type}_total")
                    for port in data[type]:
                        sensors.append(f"{type}_{port}")
            _LOGGER.debug(f"Available ports sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(
                f"Cannot get available ports sensors for {self._host}: {ex}"
            )
        return sensors

    async def _get_sysinfo_sensors(self):
        """Get the available sysinfo sensors."""

        sensors = list()

        if self._identity.sysinfo:
            try:
                data = await self._api.async_get_sysinfo()
                for type in SENSORS_SYSINFO:
                    if type in data:
                        sensors.append(type)
                _LOGGER.debug(f"Available sysinfo sensors: {sensors}")
            except Exception as ex:
                _LOGGER.warning(
                    f"Cannot get available sysinfo sensors for {self._host}: {ex}"
                )

        return sensors

    async def _get_temperature_sensors(self):
        """Get the available temperature sensors."""

        try:
            sensors = await self._api.async_get_temperature_labels()
            _LOGGER.debug(f"Available temperature sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(
                f"Cannot get available temperature sensors for {self._host}: {ex}"
            )
            sensors = list()
        return sensors

    async def _get_vpn_sensors(self):
        """Get the available VPN sensors."""

        sensors = list()

        try:
            data = await self._api.async_get_vpn()
            for vpn in data:
                for sensor in SENSORS_VPN:
                    sensors.append(f"{vpn}_{sensor}")
                sensors.append(f"{vpn}_state")
            _LOGGER.debug(f"Available VPN sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(f"Cannot get available VPN sensors for {self._host}: {ex}")

        return sensors

    async def _get_wlan_sensors(self):
        """Get the available WLAN sensors."""

        sensors = list()

        try:
            data = await self._api.async_get_wlan_ids()
            for id in data:
                for sensor in SENSORS_WLAN:
                    sensors.append(f"wl{id}_{sensor}")
                sensors.append(f"wl{id}_radio")
            _LOGGER.debug(f"Available WLAN sensors: {sensors}")
        except Exception as ex:
            _LOGGER.warning(f"Cannot get available WLAN sensors for {self._host}: {ex}")

        return sensors

    ### <- GET SENSORS LIST

    ### GENERAL USAGE METHODS ->
    async def async_get_network_interfaces(self) -> list[str]:
        """Get the list of network interfaces of the device."""

        return await self._api.async_get_network_labels()

    ### <- GENERAL USAGE METHODS

    ### SERVICES ->
    async def async_reboot(self) -> bool:
        """Reboot the device."""

        return await self._api.async_service_reboot()

    ### <- SERVICES
