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
    AiMeshDevice,
    AsusDevice,
    AsusRouter,
    AsusRouterError,
    ConnectedDevice,
    FilterDevice,
)
from asusrouter.util import converters

from . import helpers
from .const import (
    BOOTTIME,
    CONF_CACHE_TIME,
    CONF_CERT_PATH,
    CONF_MODE,
    CPU,
    DEFAULT_CACHE_TIME,
    DEFAULT_MODE,
    DEFAULT_PORT,
    DEFAULT_SENSORS,
    DEFAULT_VERIFY_SSL,
    FIRMWARE,
    GWLAN,
    ISO,
    KEY_OVPN_CLIENT,
    KEY_OVPN_SERVER,
    LED,
    MAC,
    MODE_SENSORS,
    NAME,
    NETWORK,
    NETWORK_STAT,
    PARENTAL_CONTROL,
    PASSWORD,
    PORTS,
    RAM,
    SENSORS_BOOTTIME,
    SENSORS_CPU,
    SENSORS_FIRMWARE,
    SENSORS_LED,
    SENSORS_NETWORK,
    SENSORS_PORTS,
    SENSORS_RAM,
    SENSORS_SYSINFO,
    SENSORS_PARENTAL_CONTROL,
    SENSORS_VPN,
    SENSORS_VPN_SERVER,
    SENSORS_WAN,
    SERVICE_ALLOWED_ADJUST_GWLAN,
    SERVICE_ALLOWED_ADJUST_WLAN,
    SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS,
    SYSINFO,
    TEMPERATURE,
    TIMESTAMP,
    TOTAL,
    VPN,
    WAN,
    WLAN,
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
            cache_time=configs.get(CONF_CACHE_TIME, DEFAULT_CACHE_TIME),
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

    async def async_cleanup_sensors(self, sensors: dict[str, Any]) -> dict[str, Any]:
        """Cleanup sensors depending on the device mode."""

        mode = self._configs.get(CONF_MODE, DEFAULT_MODE)
        available = MODE_SENSORS[mode]
        _LOGGER.debug(f"Available sensors for mode=`{mode}`: {available}")
        sensors = {
            group: details for group, details in sensors.items() if group in available
        }

        return sensors

    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Get a dictionary of available sensors."""

        sensors = {
            BOOTTIME: {"sensors": SENSORS_BOOTTIME, "method": self._get_data_boottime},
            CPU: {
                "sensors": await self._get_sensors_cpu(),
                "method": self._get_data_cpu,
            },
            FIRMWARE: {
                "sensors": SENSORS_FIRMWARE,
                "method": self._get_data_firmware,
            },
            GWLAN: {
                "sensors": await self._get_sensors_gwlan(),
                "method": self._get_data_gwlan,
            },
            LED: {
                "sensors": SENSORS_LED,
                "method": self._get_data_led,
            },
            NETWORK: {
                "sensors": await self._get_sensors_network(),
                "method": self._get_data_network,
            },
            PARENTAL_CONTROL: {
                "sensors": SENSORS_PARENTAL_CONTROL,
                "method": self._get_data_parental_control,
            },
            PORTS: {
                "sensors": await self._get_sensors_ports(),
                "method": self._get_data_ports,
            },
            RAM: {"sensors": SENSORS_RAM, "method": self._get_data_ram},
            SYSINFO: {
                "sensors": await self._get_sensors_sysinfo(),
                "method": self._get_data_sysinfo,
            },
            TEMPERATURE: {
                "sensors": await self._get_sensors_temperature(),
                "method": self._get_data_temperature,
            },
            VPN: {
                "sensors": await self._get_sensors_vpn(),
                "method": self._get_data_vpn,
            },
            WAN: {"sensors": SENSORS_WAN, "method": self._get_data_wan},
            WLAN: {
                "sensors": await self._get_sensors_wlan(),
                "method": self._get_data_wlan,
            },
        }

        # Cleanup
        sensors = await self.async_cleanup_sensors(sensors)

        return sensors

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
            return self._process_data_generic(raw)
        except AsusRouterError as ex:
            raise UpdateFailed(ex) from ex

    # AiMesh nodes
    async def async_get_aimesh_nodes(self) -> dict[str, AiMeshDevice]:
        """Get dict of AiMesh nodes."""

        return await self._get_data(self.api.async_get_aimesh)

    # Connected devices
    async def async_get_connected_devices(self) -> dict[str, ConnectedDevice]:
        """Get dict of connected devices."""

        return await self._get_data(self.api.async_get_connected_devices)

    # Sensor-specific methods
    async def _get_data_boottime(self) -> dict[str, Any]:
        """Get `boottime` data from the device."""

        return await self._get_data(
            self.api.async_get_boottime, self._process_data_boottime
        )

    async def _get_data_cpu(self) -> dict[str, Any]:
        """Get CPU data from the device."""

        return await self._get_data(self.api.async_get_cpu)

    async def _get_data_firmware(self) -> dict[str, Any]:
        """Get firmware data from the device."""

        return await self._get_data(self.api.async_get_firmware)

    async def _get_data_gwlan(self) -> dict[str, Any]:
        """Get GWLAN data from the device."""

        return await self._get_data(self.api.async_get_gwlan)

    async def _get_data_led(self) -> dict[str, Any]:
        """Get light data from the device."""

        return {"led": self.api.led}

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
    def _process_data_generic(raw: dict[str, Any]) -> dict[str, Any]:
        """Process generic data."""

        return helpers.as_dict(helpers.flatten_dict(raw))

    @staticmethod
    def _process_data_boottime(raw: dict[str, Any]) -> dict[str, Any]:
        """Process `boottime` data"""

        raw[TIMESTAMP] = datetime.fromisoformat(raw[ISO])
        return raw

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

        data = helpers.as_dict(helpers.flatten_dict(raw))

        # This conversion is a legacy
        # Keep untill switching to the new ports sensors
        for port_type in SENSORS_PORTS:
            if port_type in raw:
                data[f"{port_type}_{TOTAL}"] = 0
                for id in raw[port_type]:
                    data[f"{port_type}_{id}"] = raw[port_type][id].get("link_rate")
                    data[f"{port_type}_{TOTAL}"] += data[f"{port_type}_{id}"]

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
            if process is None:
                process = self._process_data_generic
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
            self.api.async_get_cpu,
            self._process_sensors_cpu,
            type=CPU,
            defaults=True,
        )

    async def _get_sensors_gwlan(self) -> list[str]:
        """Get the available GWLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_gwlan,
            type=GWLAN,
        )

    async def _get_sensors_network(self) -> list[str]:
        """Get the available network stat sensors."""

        return await self._get_sensors(
            self.api.async_get_network,
            self._process_sensors_network,
            type=NETWORK_STAT,
        )

    async def _get_sensors_ports(self) -> list[str]:
        """Get the available ports sensors."""

        return await self._get_sensors(
            self.api.async_get_ports,
            self._process_sensors_ports,
            type=PORTS,
        )

    async def _get_sensors_sysinfo(self) -> list[str]:
        """Get the available sysinfo sensors."""

        return await self._get_sensors(
            self.api.async_get_sysinfo,
            self._process_sensors_sysinfo,
            type=SYSINFO,
        )

    async def _get_sensors_temperature(self) -> list[str]:
        """Get the available temperature sensors."""

        return await self._get_sensors(
            self.api.async_get_temperature, type=TEMPERATURE
        )

    async def _get_sensors_vpn(self) -> list[str]:
        """Get the available VPN sensors."""

        return await self._get_sensors(
            self.api.async_get_vpn, self._process_sensors_vpn, type=VPN
        )

    async def _get_sensors_wlan(self) -> list[str]:
        """Get the available WLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_wlan,
            type=WLAN,
        )

    ### <- GET SENSORS LIST

    ### PROCESS SENSORS LIST->
    @staticmethod
    def _process_sensors_generic(raw: dict[str, Any]) -> list[str]:
        """Process generic sensors from the backend library.
        For the most of sensors, which are returned and nested dicts
        and only the top level keys are the one we are looking for.
        """

        flat = helpers.as_dict(helpers.flatten_dict(raw))
        return helpers.list_from_dict(flat)

    @staticmethod
    def _process_sensors_cpu(raw: dict[str, Any]) -> list[str]:
        """Process CPU sensors."""

        sensors = list()
        for label in raw:
            for sensor in SENSORS_CPU:
                sensors.append(f"{label}_{sensor}")

        return sensors

    @staticmethod
    def _process_sensors_network(raw: list[str]) -> list[str]:
        """Process network sensors."""

        sensors = list()
        for label in raw:
            for el in SENSORS_NETWORK:
                sensors.append(f"{label}_{el}")
        return sensors

    @staticmethod
    def _process_sensors_ports(raw: list[str]) -> list[str]:
        """Process ports sensors."""

        # This conversion is a legacy
        # Keep untill switching to the new ports sensors
        sensors = list()
        for port_type in SENSORS_PORTS:
            if port_type in raw:
                sensors.append(f"{port_type}_{TOTAL}")
                for id in raw[port_type]:
                    sensors.append(f"{port_type}_{id}")
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
        if capabilities["api_type"] == GWLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg in args_raw:
                if arg in SERVICE_ALLOWED_ADJUST_GWLAN:
                    args[arg] = (
                        str(SERVICE_ALLOWED_ADJUST_GWLAN[arg](args_raw[arg]))
                        if SERVICE_ALLOWED_ADJUST_GWLAN[arg] is not None
                        else str(args_raw[arg])
                    )

            if PASSWORD in args_raw:
                args["wpa_psk"] = str(args_raw[PASSWORD])
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
        elif capabilities["api_type"] == WLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg in args_raw:
                if arg in SERVICE_ALLOWED_ADJUST_WLAN:
                    args[arg] = (
                        str(SERVICE_ALLOWED_ADJUST_WLAN[arg](args_raw[arg]))
                        if SERVICE_ALLOWED_ADJUST_WLAN[arg] is not None
                        else str(args_raw[arg])
                    )

            if PASSWORD in args_raw:
                args["wpa_psk"] = str(args_raw[PASSWORD])
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
                if MAC in rule:
                    mac = rule[MAC].upper()
                    name = rule.get(NAME, mac)
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
        # Entities are set
        elif "entities" in raw:
            entities = raw["entities"]
            entity_reg = er.async_get(self.hass)
            for entity in entities:
                reg_value = entity_reg.async_get(entity)
                rules_to_change.append(
                    FilterDevice(
                        mac=reg_value.capabilities[MAC].upper(),
                        name=reg_value.capabilities[NAME],
                        state=state,
                    )
                )
        if state == "remove":
            _LOGGER.debug("Removing parental control rules")
            rules = await self.api.async_remove_parental_control_rules(
                rules=rules_to_change
            )
            return True if rules != dict() else False
        elif state in SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS:
            _LOGGER.debug("Setting parental control rules")
            return await self.api.async_set_parental_control_rules(
                rules=rules_to_change
            )
        else:
            return False

    ### <- SERVICES
