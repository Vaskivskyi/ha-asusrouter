"""AsusRouter bridge"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)

from typing import Any
from abc import ABC, abstractmethod
from datetime import datetime

from asusrouter import AsusRouter

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import (
    CONF_USE_SSL,
    CONF_CERT_PATH,
    CONF_CACHE_TIME,
    CONF_ENABLE_MONITOR,
    CONF_ENABLE_CONTROL,
    SENSORS_RAM,
    SENSORS_NETWORK_STAT,
    SENSORS_MISC,
)

SENSORS_TYPE_CPU = "cpu"
SENSORS_TYPE_RAM = "ram"
SENSORS_TYPE_NETWORK_STAT = "network_stat"
SENSORS_TYPE_DEVICES = "devices"
SENSORS_TYPE_MISC = "misc"


class AsusRouterBridge(ABC):
    """The Base Bridge abstract class"""

    @staticmethod
    def get_bridge(hass : HomeAssistant, conf : dict[str, Any], options : dict[str, Any] | None = None) -> AsusRouterBridge:
        """Get Bridge instance"""

        return AsusRouterBridgeHTTP(conf)


    def __init__(self) -> None:
        """Initialize Bridge"""

        self._api = None

        self._mac : str | None = None
        self._serial : str | None = None
        self._model : str = "ASUS Router"
        self._vendor : str = "ASUSTek"
        self._firmware : str | None = None


    @property
    def is_connected(self) -> bool:
        """Get connected status"""
        return False


    @abstractmethod
    async def async_connect(self) -> None:
        """Connect to the device"""


    @abstractmethod
    async def async_disconnect(self) -> None:
        """Disconnect to the device"""


    @abstractmethod
    async def async_get_connected_devices(self) -> dict[str, dict[str, Any]]:
        """Get list of connected devices"""


    async def get_mac(self) -> str | None:
        """Get label mac information"""

        return self._mac


    async def get_serial(self) -> str | None:
        """Get serial information"""

        return self._serial


    async def get_model(self) -> str | None:
        """Get model information"""

        return self._model


    async def get_vendor(self) -> str | None:
        """Get vendor information"""

        return self._vendor


    async def get_firmware(self) -> str | None:
        """Get firmware information"""

        return self._firmware


    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Return a dictionary of available sensors for this bridge"""

        return {}


class AsusRouterBridgeHTTP(AsusRouterBridge):
    """Bridge for AsusRouter HTTP library"""

    def __init__(self, conf : dict[str, Any]) -> None:
        """Initialise bridge"""

        super().__init__()
        self._api = self._get_api(conf)


    @staticmethod
    def _get_api(conf : dict[str, Any]) -> AsusRouter:
        """Get the AsusWrtHttp API"""

        return AsusRouter(
            host = conf[CONF_HOST],
            username = conf[CONF_USERNAME],
            password = conf[CONF_PASSWORD],
            port = conf[CONF_PORT],
            use_ssl = conf[CONF_USE_SSL],
            cert_check = conf[CONF_VERIFY_SSL],
            cert_path = conf.get(CONF_CERT_PATH, ""),
            cache_time = conf.get(CONF_CACHE_TIME, 3),
            enable_monitor = conf.get(CONF_ENABLE_MONITOR),
            enable_control = conf.get(CONF_ENABLE_CONTROL),
        )


    @property
    def is_connected(self) -> bool:
        """Get connected status"""

        return self._api.connected


    async def async_connect(self) -> None:
        """Connect to the device"""

        try:
            await self._api.connection.async_connect()
        except Exception as ex:
            raise ConfigEntryNotReady from ex


    async def async_disconnect(self) -> None:
        """Disconnect from the device"""

        await self._api.connection.async_disconnect()


    async def async_get_connected_devices(self) -> dict[str, Any]:
        """Get list of connected devices"""

        try:
            api_devices = await self._api.async_get_devices()
        except Exception as ex:
            raise UpdateFailed(ex) from ex
        
        return api_devices


    async def _async_get_settings(self, info_type : str) -> dict[str, Any]:
        """Get AsusWrt router info from nvram"""

        info = {}
        try:
            info = await self._api.async_get_settings(info_type)
        except Exception as ex:
            _LOGGER.warning("Error calling method async_get_settings(%s): %s", info_type, ex)

        return info


    async def _async_get_device_info(self) -> None:
        """Load device info"""

        await self._api.async_initialize()
        nvram = self._api._monitor_nvram

        if nvram:
            if "label_mac" in nvram:
                self._mac = format_mac(nvram['label_mac'])
            if "serial" in nvram:
                self._serial = nvram['serial']
            if "model" in nvram:
                self._model = nvram['model']
            if "pci/1/1/ATE_Brand" in nvram:
                self._vendor = nvram['pci/1/1/ATE_Brand']
            if "firmver" in nvram:
                self._firmware = "{}.{}_{}".format(nvram['firmver'], nvram['buildno'], nvram['extendno'])

        return


    async def get_firmware(self) -> str | None:
        """Get firmware information"""

        if self._firmware is None:
            self._firmware = ""
            await self._async_get_device_info()

        return self._firmware or None


    async def get_mac(self) -> str | None:
        """Get MAC information"""

        if self._mac is None:
            self._mac = ""
            await self._async_get_device_info()

        return self._mac or None


    async def get_serial(self) -> str | None:
        """Get serial information"""

        if self._serial is None:
            self._serial = ""
            await self._async_get_device_info()

        return self._serial or None


    async def get_model(self) -> str | None:
        """Get model information"""

        if self._model is None:
            self._model = ""
            await self._async_get_device_info()

        return self._model or None


    async def get_vendor(self) -> str | None:
        """Get vendor information"""

        if self._vendor is None:
            self._vendor = ""
            await self._async_get_device_info()

        return self._vendor or None


    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Return a dictionary of available sensors for this bridge."""

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
        }
        return sensors_types


    ### GET DATA FROM DEVICE ->
    async def _get_cpu(self) -> dict[str, Any]:
        """Get CPU data from router"""

        try:
            data = await self._api.async_get_cpu()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_ram(self) -> dict[str, Any]:
        """Get RAM data from router"""

        try:
            data = await self._api.async_get_ram()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_network_stat(self) -> dict[str, Any]:
        """Get network data from router"""

        try:
            data = await self._api.async_get_network()
        except (OSError, ValueError) as ex:
            raise UpdateFailed(ex) from ex

        return data


    async def _get_misc(self) -> dict[str, Any]:
        """Get MISC sensors"""

        data = dict()
        await self._api.async_monitor_misc()
        data["boottime"] = datetime.fromisoformat(self._api.boottime)

        return data
    ### <- GET DATA FROM DEVICE


    ### GET SENSORS LIST ->
    async def _get_cpu_sensors(self):
        """Check the available CPU sensors"""

        try:
            sensors = await self._api.async_get_cpu_labels()
            _LOGGER.debug("Available CPU sensors: {}".format(sensors))
        except Exception as ex:
            _LOGGER.debug("Cannot get available CPU sensors for {}: {}".format(self._host, ex))
            sensors = ["total"]
        return sensors


    async def _get_network_stat_sensors(self):
        """Check the available network stat sensors"""

        try:
            sensors = []
            labels = await self._api.async_get_network_labels()
            for label in labels:
                for el in SENSORS_NETWORK_STAT:
                    sensors.append("{}_{}".format(label, el))
            _LOGGER.debug("Available network stat sensors: {}".format(sensors))
        except Exception as ex:
            _LOGGER.debug("Cannot get available network stat sensors for {}: {}".format(self._host, ex))
        return sensors
    ### <- GET SENSORS LIST

