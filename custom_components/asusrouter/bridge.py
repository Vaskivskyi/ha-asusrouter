"""AsusRouter bridge."""

from __future__ import annotations

import aiohttp
import dataclasses
from datetime import datetime
import logging
from typing import Any, Awaitable, Callable, TypeVar

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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from asusrouter import (
    AsusDevice,
    AsusRouter,
    AsusRouterError,
    ConnectedDevice,
    FilterDevice,
)
from asusrouter.util import converters

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
    KEY_OVPN_CLIENT,
    KEY_OVPN_SERVER,
    SENSORS_FIRMWARE,
    SENSORS_GWLAN,
    SENSORS_LIGHT,
    SENSORS_MISC,
    SENSORS_NETWORK_STAT,
    SENSORS_PORTS,
    SENSORS_RAM,
    SENSORS_SYSINFO,
    SENSORS_TYPE_CPU,
    SENSORS_TYPE_FIRMWARE,
    SENSORS_TYPE_GWLAN,
    SENSORS_TYPE_LIGHT,
    SENSORS_TYPE_MISC,
    SENSORS_TYPE_NETWORK_STAT,
    SENSORS_TYPE_PARENTAL_CONTROL,
    SENSORS_TYPE_PORTS,
    SENSORS_TYPE_RAM,
    SENSORS_TYPE_SYSINFO,
    SENSORS_TYPE_TEMPERATURE,
    SENSORS_TYPE_VPN,
    SENSORS_TYPE_WAN,
    SENSORS_TYPE_WLAN,
    SENSORS_PARENTAL_CONTROL,
    SENSORS_VPN,
    SENSORS_VPN_SERVER,
    SENSORS_WAN,
    SENSORS_WLAN,
    SERVICE_ALLOWED_ADJUST_GWLAN,
    SERVICE_ALLOWED_ADJUST_WLAN,
    SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS,
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
        self.hass = hass

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
            SENSORS_TYPE_FIRMWARE: {
                "sensors": SENSORS_FIRMWARE,
                "method": self._get_data_firmware,
            },
            SENSORS_TYPE_GWLAN: {
                "sensors": await self._get_sensors_gwlan(),
                "method": self._get_data_gwlan,
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
            SENSORS_TYPE_PARENTAL_CONTROL: {
                "sensors": SENSORS_PARENTAL_CONTROL,
                "method": self._get_data_parental_control,
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
        except AsusRouterError as ex:
            raise UpdateFailed(ex) from ex

    # Connected devices
    async def async_get_connected_devices(self) -> dict[str, ConnectedDevice]:
        """Get dict of connected devices."""

        return await self._get_data(self.api.async_get_devices)

    # Sensor-specific methods
    async def _get_data_cpu(self) -> dict[str, Any]:
        """Get CPU data from the device."""

        return await self._get_data(self.api.async_get_cpu)

    async def _get_data_firmware(self) -> dict[str, Any]:
        """Get firmware data from the device."""

        return await self._get_data(self.api.async_get_firmware_update)

    async def _get_data_gwlan(self) -> dict[str, Any]:
        """Get GWLAN data from the device."""

        return await self._get_data(self.api.async_get_gwlan)

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

    async def _get_data_parental_control(self) -> dict[str, dict[str, int]]:
        """Get parental control data from the device."""

        return await self._get_data(
            self.api.async_get_parental_control, self._process_data_parental_control
        )

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
    def _process_data_parental_control(raw: dict[str, Any]) -> dict[str, Any]:
        """Process parental control data."""

        data = dict()
        data["state"] = raw.get("parental_control")
        devices = list()
        for el in raw["list"]:
            device = dataclasses.asdict(raw["list"][el])
            device.pop("timemap")
            devices.append(device)
        data["list"] = devices.copy()
        return data

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

    async def _get_sensors_gwlan(self) -> list[str]:
        """Get the available GWLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_gwlan_ids,
            self._process_sensors_gwlan,
            type=SENSORS_TYPE_GWLAN,
        )

    async def _get_sensors_network_stat(self) -> list[str]:
        """Get the available network stat sensors."""

        return await self._get_sensors(
            self.api.async_get_network_labels,
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
    def _process_sensors_gwlan(raw: list[str]) -> list[str]:
        """Process GWLAN sensors."""

        sensors = list()
        for id in raw:
            for sensor in SENSORS_GWLAN:
                sensors.append(f"wl{id}_{sensor}")
            sensors.append(f"wl{id}_bss_enabled")
        return sensors

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
            if KEY_OVPN_CLIENT in vpn:
                for sensor in SENSORS_VPN:
                    sensors.append(f"{vpn}_{sensor}")
            elif KEY_OVPN_SERVER in vpn:
                for sensor in SENSORS_VPN_SERVER:
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

    ### SERVICES ->
    async def async_reboot(self) -> bool:
        """Reboot the device."""

        return await self.api.async_service_reboot()

    async def async_adjust_wlan(self, **kwargs: Any) -> bool:
        """Adjust WLAN settings"""

        if not "raw" in kwargs:
            return False

        raw = kwargs["raw"]

        # Check entity
        entity_reg = er.async_get(self.hass)
        entity = entity_reg.async_get(raw["entity_id"])
        capabilities = entity.capabilities

        args_raw = raw.copy()

        args = dict()

        prefix = str()
        if capabilities["api_type"] == SENSORS_TYPE_GWLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg in args_raw:
                if arg in SERVICE_ALLOWED_ADJUST_GWLAN:
                    args[arg] = (
                        str(SERVICE_ALLOWED_ADJUST_GWLAN[arg](args_raw[arg]))
                        if SERVICE_ALLOWED_ADJUST_GWLAN[arg] is not None
                        else str(args_raw[arg])
                    )

            if "password" in args_raw:
                args["wpa_psk"] = str(args_raw["password"])
            if "state" in args_raw:
                args["bss_enabled"] = str(converters.int_from_bool(args_raw["state"]))
            if "expire" in args_raw:
                args["expire_tmp"] = str(0)

            # Name arguments correctly
            service_args = {f"{prefix}_{arg}": args[arg] for arg in args}

            # We need to specify unit/subunit, otherwise expiry timer will not reset
            service_args["wl_unit"] = str(capabilities["api_id"][0])
            service_args["wl_subunit"] = str(capabilities["api_id"][-1])

            return await self.api.async_service_run(
                service="restart_wireless;restart_firewall",
                arguments=service_args,
                expect_modify=True,
            )
        elif capabilities["api_type"] == SENSORS_TYPE_WLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg in args_raw:
                if arg in SERVICE_ALLOWED_ADJUST_WLAN:
                    args[arg] = (
                        str(SERVICE_ALLOWED_ADJUST_WLAN[arg](args_raw[arg]))
                        if SERVICE_ALLOWED_ADJUST_WLAN[arg] is not None
                        else str(args_raw[arg])
                    )

            if "password" in args_raw:
                args["wpa_psk"] = str(args_raw["password"])
            if "state" in args_raw:
                args["radio"] = str(converters.int_from_bool(args_raw["state"]))

            # Name arguments correctly
            service_args = {f"{prefix}_{arg}": args[arg] for arg in args}

            return await self.api.async_service_run(
                service="restart_wireless",
                arguments=service_args,
                expect_modify=True,
            )
        else:
            return False

    async def async_parental_control(self, **kwargs: Any) -> bool:
        """Adjust parental control rules"""

        raw = kwargs.get("raw", None)
        if raw is None:
            return False

        rules_to_change = list()

        state = raw.get("state")

        # Devices are set
        if "devices" in raw:
            rules = raw["devices"]
            for rule in rules:
                if "mac" in rule:
                    mac = rule["mac"].upper()
                    name = rule.get("name", mac)
                    rules_to_change.append(
                        FilterDevice(
                            mac=mac,
                            name=name,
                            state=state,
                        )
                    )
                else:
                    _LOGGER.warning(
                        f"Parental control rule is missing MAC address. This rule is skipped"
                    )
        # Single MAC is set
        elif "mac" in raw:
            mac = raw["mac"].upper()
            name = raw.get("name", mac)
            rules_to_change.append(
                FilterDevice(
                    mac=mac,
                    name=name,
                    state=state,
                )
            )
        # Entities are set
        elif "entities" in raw:
            entities = raw["entities"]
            entity_reg = er.async_get(self.hass)
            for entity in entities:
                reg_value = entity_reg.async_get(entity)
                rules_to_change.append(
                    FilterDevice(
                        mac=reg_value.capabilities["mac"].upper(),
                        name=reg_value.capabilities["name"],
                        state=state,
                    )
                )
        # Single entity_id is provided
        elif "entity_id" in raw:
            entity_reg = er.async_get(self.hass)
            reg_value = entity_reg.async_get(raw["entity_id"])
            rules_to_change.append(
                FilterDevice(
                    mac=reg_value.capabilities["mac"].upper(),
                    name=reg_value.capabilities["name"],
                    state=state,
                )
            )

        if state == "remove":
            rules = await self.api.async_remove_parental_control_rules(rules_to_change)
            return True if rules != dict() else False
        elif state in SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS:
            return await self.api.async_set_parental_control_rules(rules_to_change)
        else:
            return False

    ### <- SERVICES
