"""AsusRouter bridge"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from datetime import datetime
from typing import Any

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
from homeassistant.helpers.update_coordinator import UpdateFailed

from asusrouter import (
    AsusDevice,
    AsusRouter,
    AsusRouterError,
    ConnectedDevice,
)

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
    SENSORS_MISC,
    SENSORS_NETWORK_STAT,
    SENSORS_PORTS,
    SENSORS_RAM,
    SENSORS_TYPE_CPU,
    SENSORS_TYPE_MISC,
    SENSORS_TYPE_NETWORK_STAT,
    SENSORS_TYPE_PORTS,
    SENSORS_TYPE_RAM,
    SENSORS_TYPE_WAN,
    SENSORS_WAN,
)


class ARBridge():
    """Bridge for AsusRouter library"""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: dict[str, Any],
        options: dict[str, Any] = dict(),
    ) -> None:
        """Initialize bridge"""

        super().__init__()
        self._configs = configs.copy()
        self._configs.update(options)
        self._api = self._get_api(self._configs)
        self._host = self._configs[CONF_HOST]
        self._identity: AsusDevice | None = None


    @staticmethod
    def _get_api(
        configs: dict[str, Any],
    ) -> AsusRouter:
        """Get AsusRouter API"""

        return AsusRouter(
            host = configs[CONF_HOST],
            username = configs[CONF_USERNAME],
            password = configs[CONF_PASSWORD],
            port = configs.get(CONF_PORT, DEFAULT_PORT),
            use_ssl = configs[CONF_SSL],
            cert_check = configs.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            cert_path = configs.get(CONF_CERT_PATH, ""),
            cache_time = configs.get(CONF_CACHE_TIME, DEFAULT_CACHE_TIME),
            enable_monitor = configs.get(CONF_ENABLE_MONITOR, DEFAULT_ENABLE_MONITOR),
            enable_control = configs.get(CONF_ENABLE_CONTROL, DEFAULT_ENABLE_CONTROL),
        )


    @property
    def is_connected(self) -> bool:
        """Get connected status"""

        return self._api.connected


    async def async_connect(self) -> None:
        """Connect to the device"""

        try:
            await self._api.async_connect()
            self._identity = await self._async_get_device_identity()
        except AsusRouterError as ex:
            raise ex
        except Exception as ex:
            raise ConfigEntryNotReady from ex


    async def async_disconnect(self) -> None:
        """Disconnect from the device"""

        await self._api.async_disconnect()


    async def async_clean(self) -> None:
        """Cleanup"""

        await self._api.connection.async_cleanup()


    async def _async_get_device_identity(self) -> AsusDevice:
        """Load device identity"""

        return await self._api.async_get_identity()


    async def async_get_connected_devices(self) -> dict[str, ConnectedDevice]:
        """Get dict of connected devices"""

        try:
            api_devices = await self._api.async_get_devices()
        except Exception as ex:
            raise UpdateFailed(ex) from ex
        
        return api_devices


    async def get_firmware(self) -> str | None:
        """Get firmware information"""

        return self._identity.firmware()


    async def get_mac(self) -> str | None:
        """Get MAC information"""

        return self._identity.mac


    async def get_serial(self) -> str | None:
        """Get serial information"""

        return self._identity.serial


    async def get_model(self) -> str | None:
        """Get model information"""

        return self._identity.model


    async def get_vendor(self) -> str | None:
        """Get vendor information"""

        return self._identity.brand


    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Get a dictionary of available sensors"""

        sensors_types = {
            SENSORS_TYPE_CPU: {
                "sensors": await self._get_cpu_sensors(),
                "method": self._get_cpu
            },
            SENSORS_TYPE_RAM: {
                "sensors": SENSORS_RAM,
                "method": self._get_ram
            },
            SENSORS_TYPE_NETWORK_STAT: {
                "sensors": await self._get_network_stat_sensors(),
                "method": self._get_network_stat
            },
            SENSORS_TYPE_MISC: {
                "sensors": SENSORS_MISC,
                "method": self._get_misc
            },
            SENSORS_TYPE_PORTS: {
                "sensors": await self._get_ports_sensors(),
                "method": self._get_ports
            },
            SENSORS_TYPE_WAN: {
                "sensors": SENSORS_WAN,
                "method": self._get_wan
            },
        }
        return sensors_types


    ### GET DATA FROM DEVICE ->
    async def _get_cpu(self) -> dict[str, Any]:
        """Get CPU data from the device"""

        try:
            data = await self._api.async_get_cpu()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_ram(self) -> dict[str, Any]:
        """Get RAM data from the device"""

        try:
            data = await self._api.async_get_ram()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_network_stat(self) -> dict[str, Any]:
        """Get network data from device"""

        try:
            data = await self._api.async_get_network()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_misc(self) -> dict[str, Any]:
        """Get MISC sensors from the device"""

        data = dict()
        await self._api.async_monitor_misc()
        data["boottime"] = datetime.fromisoformat(self._api.boottime)

        return data


    async def _get_ports(self) -> dict[str, dict[str, int]]:
        """Get ports status from the device"""

        data = dict()
        try:
            raw = await self._api.async_get_ports()

            for type in SENSORS_PORTS:
                if type in raw:
                    data["{}_total".format(type)] = 0
                    for port in raw[type]:
                        data["{}_{}".format(type, port)] = raw[type][port]
                        data["{}_total".format(type)] += raw[type][port]
                    if data["{}_total".format(type)] > 0:
                        data[type] = True
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_wan(self) -> dict[str, Any]:
        """Get WAN data from the device"""

        try:
            data = await self._api.async_get_wan()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data
    ### <- GET DATA FROM DEVICE


    ### GET SENSORS LIST ->
    async def _get_cpu_sensors(self):
        """Get the available CPU sensors"""

        try:
            sensors = await self._api.async_get_cpu_labels()
            _LOGGER.debug("Available CPU sensors: {}".format(sensors))
        except Exception as ex:
            _LOGGER.warning("Cannot get available CPU sensors for {}: {}".format(self._host, ex))
            sensors = ["total"]
        return sensors


    async def _get_network_stat_sensors(self):
        """Get the available network stat sensors"""

        try:
            sensors = []
            labels = await self.async_get_network_interfaces()
            for label in labels:
                for el in SENSORS_NETWORK_STAT:
                    sensors.append("{}_{}".format(label, el))
            _LOGGER.debug("Available network stat sensors: {}".format(sensors))
        except Exception as ex:
            _LOGGER.warning("Cannot get available network stat sensors for {}: {}".format(self._host, ex))
        return sensors


    async def _get_ports_sensors(self):
        """Get the available ports sensors"""

        try:
            sensors = []
            data = await self._api.async_get_ports()
            for type in SENSORS_PORTS:
                if type in data:
                    sensors.append(type)
                    sensors.append("{}_total".format(type))
                    for port in data[type]:
                        sensors.append("{}_{}".format(type, port))
            _LOGGER.debug("Available ports sensors: {}".format(sensors))
        except Exception as ex:
            _LOGGER.warning("Cannot get available ports sensors for {}: {}".format(self._host, ex))
        return sensors
    ### <- GET SENSORS LIST


    ### GENERAL USAGE METHODS ->
    async def async_get_network_interfaces(self) -> list[str]:
        """Get the list of network interfaces of the device"""

        return await self._api.async_get_network_labels()
    ### <- GENERAL USAGE METHODS


