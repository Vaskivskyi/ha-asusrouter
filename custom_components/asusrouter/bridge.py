"""AsusRouter bridge module."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import dataclasses
from datetime import datetime
import logging
from typing import Any

import aiohttp
from asusrouter import (
    AiMeshDevice,
    AsusDevice,
    AsusRouter,
    AsusRouterError,
    ConnectedDevice,
    FilterDevice,
    PortForwarding,
)
from asusrouter.util import converters

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import helpers
from .const import (
    ACTION,
    BOOTTIME,
    CONF_CACHE_TIME,
    CONF_DEFAULT_CACHE_TIME,
    CONF_DEFAULT_MODE,
    CONF_DEFAULT_PORT,
    CONF_MODE,
    CPU,
    DEFAULT_SENSORS,
    FIRMWARE,
    GWLAN,
    IP,
    IP_EXTERNAL,
    IPS,
    ISO,
    KEY_OVPN_CLIENT,
    KEY_OVPN_SERVER,
    LED,
    LIST,
    LIST_PORTS,
    MAC,
    METHOD,
    MODE_SENSORS,
    NAME,
    NETWORK,
    NETWORK_STAT,
    PARENTAL_CONTROL,
    PASSWORD,
    PORT,
    PORT_EXTERNAL,
    PORT_FORWARDING,
    PORTS,
    PROTOCOL,
    RAM,
    SENSORS,
    SENSORS_BOOTTIME,
    SENSORS_CPU,
    SENSORS_FIRMWARE,
    SENSORS_LED,
    SENSORS_NETWORK,
    SENSORS_PARENTAL_CONTROL,
    SENSORS_PORT_FORWARDING,
    SENSORS_RAM,
    SENSORS_SYSINFO,
    SENSORS_VPN,
    SENSORS_VPN_SERVER,
    SENSORS_WAN,
    SERVICE_ALLOWED_ADJUST_GWLAN,
    SERVICE_ALLOWED_ADJUST_WLAN,
    SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS,
    SERVICE_ALLOWED_PORT_FORWARDING_PROTOCOL,
    STATE,
    SYSINFO,
    TEMPERATURE,
    TIMESTAMP,
    VPN,
    WAN,
    WLAN,
)

_LOGGER = logging.getLogger(__name__)


class ARBridge:
    """Bridge to the AsusRouter library."""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize bridge to the library."""

        self.hass = hass

        # Save all the HA configs and options
        self._configs = configs.copy()
        if options:
            self._configs.update(options)

        # Get session from HA
        session = async_get_clientsession(hass)

        # Initialize API
        self._api = self._get_api(self._configs, session)

        self._host = self._configs[CONF_HOST]
        self._identity: AsusDevice | None = None

        self._active: bool = False

    @staticmethod
    def _get_api(configs: dict[str, Any], session: aiohttp.ClientSession) -> AsusRouter:
        """Get AsusRouter API."""

        return AsusRouter(
            host=configs[CONF_HOST],
            username=configs[CONF_USERNAME],
            password=configs[CONF_PASSWORD],
            port=configs.get(CONF_PORT, CONF_DEFAULT_PORT),
            use_ssl=configs[CONF_SSL],
            cache_time=configs.get(CONF_CACHE_TIME, CONF_DEFAULT_CACHE_TIME),
            session=session,
        )

    @property
    def active(self) -> bool:
        """Return activity state of the bridge."""

        return self._active

    @property
    def api(self) -> AsusRouter:
        """Return API."""

        return self._api

    @property
    def connected(self) -> bool:
        """Return connection state."""

        return self.api.connected

    @property
    def identity(self) -> AsusDevice:
        """Return device identity."""

        return self._identity

    # CONNECTION ->
    async def async_connect(self) -> None:
        """Connect to the device."""

        _LOGGER.debug("Connecting to the API")

        await self.api.async_connect()
        self._identity = await self.api.async_get_identity()
        self._active = True

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""

        _LOGGER.debug("Disconnecting from the API")

        await self.api.async_disconnect()
        self._active = False

    async def async_clean(self) -> None:
        """Cleanup."""

        _LOGGER.debug("Cleaning up")

        await self.api.connection.async_cleanup()

    # <- CONNECTION

    async def async_cleanup_sensors(self, sensors: dict[str, Any]) -> dict[str, Any]:
        """Cleanup sensors depending on the device mode."""

        mode = self._configs.get(CONF_MODE, CONF_DEFAULT_MODE)
        available = MODE_SENSORS[mode]
        _LOGGER.debug("Available sensors for mode=`%s`: %s", mode, available)
        sensors = {
            group: details for group, details in sensors.items() if group in available
        }

        return sensors

    async def async_get_available_sensors(self) -> dict[str, dict[str, Any]]:
        """Get available sensors."""

        sensors = {
            BOOTTIME: {SENSORS: SENSORS_BOOTTIME, METHOD: self._get_data_boottime},
            CPU: {
                SENSORS: await self._get_sensors_cpu(),
                METHOD: self._get_data_cpu,
            },
            FIRMWARE: {
                SENSORS: SENSORS_FIRMWARE,
                METHOD: self._get_data_firmware,
            },
            GWLAN: {
                SENSORS: await self._get_sensors_gwlan(),
                METHOD: self._get_data_gwlan,
            },
            LED: {
                SENSORS: SENSORS_LED,
                METHOD: self._get_data_led,
            },
            NETWORK: {
                SENSORS: await self._get_sensors_network(),
                METHOD: self._get_data_network,
            },
            PARENTAL_CONTROL: {
                SENSORS: SENSORS_PARENTAL_CONTROL,
                METHOD: self._get_data_parental_control,
            },
            PORT_FORWARDING: {
                SENSORS: SENSORS_PORT_FORWARDING,
                METHOD: self._get_data_port_forwarding,
            },
            PORTS: {
                SENSORS: await self._get_sensors_ports(),
                METHOD: self._get_data_ports,
            },
            RAM: {SENSORS: SENSORS_RAM, METHOD: self._get_data_ram},
            SYSINFO: {
                SENSORS: await self._get_sensors_sysinfo(),
                METHOD: self._get_data_sysinfo,
            },
            TEMPERATURE: {
                SENSORS: await self._get_sensors_temperature(),
                METHOD: self._get_data_temperature,
            },
            VPN: {
                SENSORS: await self._get_sensors_vpn(),
                METHOD: self._get_data_vpn,
            },
            WAN: {
                SENSORS: SENSORS_WAN,
                METHOD: self._get_data_wan,
            },
            WLAN: {
                SENSORS: await self._get_sensors_wlan(),
                METHOD: self._get_data_wlan,
            },
        }

        # Cleanup sensors if needed
        sensors = await self.async_cleanup_sensors(sensors)

        return sensors

    # GET DATA FROM DEVICE ->
    # General method
    async def _get_data(
        self,
        method: Callable[[], Awaitable[dict[str, Any]]],
        process: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Get data from the device. This is a generic method."""

        try:
            raw = await method()
            if process is not None:
                return process(raw)
            return self._process_data(raw)
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

        return await self._get_data(self.api.async_get_led)

    async def _get_data_network(self) -> dict[str, Any]:
        """Get network data from device."""

        return await self._get_data(self.api.async_get_network)

    async def _get_data_parental_control(self) -> dict[str, dict[str, int]]:
        """Get parental control data from the device."""

        return await self._get_data(
            self.api.async_get_parental_control, self._process_data_parental_control
        )

    async def _get_data_port_forwarding(self) -> dict[str, Any]:
        """Get port forwarding data from the device."""

        return await self._get_data(
            self.api.async_get_port_forwarding, self._process_data_port_forwarding
        )

    async def _get_data_ports(self) -> dict[str, dict[str, int]]:
        """Get ports data from the device."""

        return await self._get_data(self.api.async_get_ports, self._process_data_ports)

    async def _get_data_ram(self) -> dict[str, Any]:
        """Get RAM data from the device."""

        return await self._get_data(self.api.async_get_ram)

    async def _get_data_sysinfo(self) -> dict[str, Any]:
        """Get sysinfo data from the device."""

        return await self._get_data(self.api.async_get_sysinfo)

    async def _get_data_temperature(self) -> dict[str, Any]:
        """Get temperarture data from the device."""

        return await self._get_data(self.api.async_get_temperature)

    async def _get_data_vpn(self) -> dict[str, Any]:
        """Get VPN data from the device."""

        return await self._get_data(self.api.async_get_vpn)

    async def _get_data_wan(self) -> dict[str, Any]:
        """Get WAN data from the device."""

        return await self._get_data(self.api.async_get_wan)

    async def _get_data_wlan(self) -> dict[str, Any]:
        """Get WLAN data from the device."""

        return await self._get_data(self.api.async_get_wlan)

    # <- GET DATA FROM DEVICE

    # PROCESS DATA ->
    @staticmethod
    def _process_data(raw: dict[str, Any]) -> dict[str, Any]:
        """Process data received from the device. This is a generic method."""

        return helpers.as_dict(helpers.flatten_dict(raw))

    @staticmethod
    def _process_data_boottime(raw: dict[str, Any]) -> dict[str, Any]:
        """Process `boottime` data."""

        raw[TIMESTAMP] = datetime.fromisoformat(raw[ISO])
        return raw

    @staticmethod
    def _process_data_parental_control(raw: dict[str, Any]) -> dict[str, Any]:
        """Process `parental control` data."""

        data = {}
        data[STATE] = raw.get(STATE)
        devices = []
        for rule in raw["rules"]:
            device = dataclasses.asdict(raw["rules"][rule])
            device.pop("timemap")
            devices.append(device)
        data[LIST] = devices.copy()
        return data

    @staticmethod
    def _process_data_port_forwarding(raw: dict[str, Any]) -> dict[str, Any]:
        """Process `port forwarding` data."""

        data = {}
        data[STATE] = raw.get(STATE)
        devices = []
        for rule in raw["rules"]:
            device = dataclasses.asdict(rule)
            devices.append(device)
        data[LIST] = devices.copy()
        return data

    @staticmethod
    def _process_data_ports(raw: dict[str, Any]) -> dict[str, Any]:
        """Process `ports` data."""

        data: dict[str, Any] = {}

        for port_type in LIST_PORTS:
            # Mark port type as disconnected
            data[port_type] = False
            # Skip if no data is provided from API
            if port_type not in raw:
                continue
            # Create ports list
            data[f"{port_type}_{LIST}"] = {}
            ports_by_type: dict[int, dict[str, Any]] = raw[port_type]
            for port_number, port_description in ports_by_type.items():
                # Mark port type connected
                if port_description.get(STATE):
                    data[port_type] = True
                # Copy port data to the list
                data[f"{port_type}_{LIST}"][port_number] = port_description

        return data

    # <- PROCESS DATA

    # GET SENSORS LIST ->
    async def _get_sensors(
        self,
        method: Callable[[], Awaitable[dict[str, Any]]],
        process: Callable[[dict[str, Any]], list[str]] | None = None,
        sensor_type: str | None = None,
        defaults: bool = False,
    ) -> list[str]:
        """Get the available sensors. This is a generic method."""

        sensors = []
        try:
            data = await method()
            sensors = (
                process(data) if process is not None else self._process_sensors(data)
            )
            _LOGGER.debug("Available `%s` sensors: %s", sensor_type, sensors)
        except AsusRouterError as ex:
            if sensor_type in DEFAULT_SENSORS and defaults:
                sensors = DEFAULT_SENSORS[sensor_type]
            _LOGGER.debug(
                "Cannot get available `%s` sensors with exception: %s. \
                    Will use the following list: {sensors}",
                sensor_type,
                ex,
            )
        return sensors

    async def _get_sensors_cpu(self) -> list[str]:
        """Get the available CPU sensors."""

        return await self._get_sensors(
            self.api.async_get_cpu,
            self._process_sensors_cpu,
            sensor_type=CPU,
            defaults=True,
        )

    async def _get_sensors_gwlan(self) -> list[str]:
        """Get the available GWLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_gwlan,
            sensor_type=GWLAN,
        )

    async def _get_sensors_network(self) -> list[str]:
        """Get the available network stat sensors."""

        return await self._get_sensors(
            self.api.async_get_network,
            self._process_sensors_network,
            sensor_type=NETWORK_STAT,
        )

    async def _get_sensors_ports(self) -> list[str]:
        """Get the available ports sensors."""

        return await self._get_sensors(
            self.api.async_get_ports,
            self._process_sensors_ports,
            sensor_type=PORTS,
        )

    async def _get_sensors_sysinfo(self) -> list[str]:
        """Get the available sysinfo sensors."""

        return await self._get_sensors(
            self.api.async_get_sysinfo,
            self._process_sensors_sysinfo,
            sensor_type=SYSINFO,
        )

    async def _get_sensors_temperature(self) -> list[str]:
        """Get the available temperature sensors."""

        return await self._get_sensors(
            self.api.async_get_temperature, sensor_type=TEMPERATURE
        )

    async def _get_sensors_vpn(self) -> list[str]:
        """Get the available VPN sensors."""

        return await self._get_sensors(
            self.api.async_get_vpn, self._process_sensors_vpn, sensor_type=VPN
        )

    async def _get_sensors_wlan(self) -> list[str]:
        """Get the available WLAN sensors."""

        return await self._get_sensors(
            self.api.async_get_wlan,
            sensor_type=WLAN,
        )

    # <- GET SENSORS LIST

    # PROCESS SENSORS LIST->
    @staticmethod
    def _process_sensors(raw: dict[str, Any]) -> list[str]:
        """Process sensors from the backend library. This is a generic method.

        For the most of sensors which are returned as nested dicts
        and only the top level keys are the one we are looking for.
        """

        flat = helpers.as_dict(helpers.flatten_dict(raw))
        return helpers.list_from_dict(flat)

    @staticmethod
    def _process_sensors_cpu(raw: dict[str, Any]) -> list[str]:
        """Process CPU sensors."""

        sensors = []
        for label in raw:
            for sensor in SENSORS_CPU:
                sensors.append(f"{label}_{sensor}")

        return sensors

    @staticmethod
    def _process_sensors_network(raw: dict[str, Any]) -> list[str]:
        """Process network sensors."""

        sensors = []
        for label in raw:
            for sensor_type in SENSORS_NETWORK:
                sensors.append(f"{label}_{sensor_type}")
        return sensors

    @staticmethod
    def _process_sensors_ports(raw: dict[str, Any]) -> list[str]:
        """Process ports sensors."""

        sensors = []

        for port_type in LIST_PORTS:
            sensors.append(port_type)
            sensors.append(f"{port_type}_{LIST}")

        return sensors

    @staticmethod
    def _process_sensors_sysinfo(raw: dict[str, Any]) -> list[str]:
        """Process SysInfo sensors."""

        sensors = []
        for sensor_type in SENSORS_SYSINFO:
            if sensor_type in raw:
                sensors.append(sensor_type)
        return sensors

    @staticmethod
    def _process_sensors_vpn(raw: dict[str, Any]) -> list[str]:
        """Process VPN sensors."""

        sensors = []
        for vpn in raw:
            if KEY_OVPN_CLIENT in vpn:
                for sensor in SENSORS_VPN:
                    sensors.append(f"{vpn}_{sensor}")
            elif KEY_OVPN_SERVER in vpn:
                for sensor in SENSORS_VPN_SERVER:
                    sensors.append(f"{vpn}_{sensor}")
            sensors.append(f"{vpn}_state")
        return sensors

    # <- PROCESS SENSORS LIST

    # SERVICES ->

    async def async_adjust_wlan(self, **kwargs: Any) -> bool:
        """Adjust WLAN settings."""

        if "raw" not in kwargs:
            return False

        raw = kwargs["raw"]

        # Check entity
        entity_reg = er.async_get(self.hass)
        entity = entity_reg.async_get(raw["entity_id"])
        if not isinstance(entity, er.RegistryEntry):
            return False

        # WLAN capabilities
        capabilities: dict[str, Any] = helpers.as_dict(entity.capabilities)

        args_raw = raw.copy()

        args = {}

        prefix = ""
        if capabilities["api_type"] == GWLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg, value in args_raw.items():
                if arg in SERVICE_ALLOWED_ADJUST_GWLAN:
                    args[arg] = str(value)
                    method = SERVICE_ALLOWED_ADJUST_GWLAN[arg]
                    if method:
                        args[arg] = method(value)

            if PASSWORD in args_raw:
                args["wpa_psk"] = str(args_raw[PASSWORD])
            if STATE in args_raw:
                args["bss_enabled"] = str(converters.int_from_bool(args_raw[STATE]))
            if "expire" in args_raw:
                args["expire_tmp"] = str(0)

            # Name arguments correctly
            service_args = {f"{prefix}_{arg}": value for arg, value in args.items()}

            # We need to specify unit/subunit, otherwise expiry timer will not reset
            service_args["wl_unit"] = str(capabilities["api_id"][0])
            service_args["wl_subunit"] = str(capabilities["api_id"][-1])

            return await self.api.async_service_generic(
                service="restart_wireless;restart_firewall",
                arguments=service_args,
                expect_modify=True,
            )
        if capabilities["api_type"] == WLAN:
            prefix = f"wl{capabilities['api_id']}"

            for arg, value in args_raw.items():
                if arg in SERVICE_ALLOWED_ADJUST_WLAN:
                    args[arg] = str(value)
                    method = SERVICE_ALLOWED_ADJUST_WLAN[arg]
                    if method:
                        args[arg] = method(value)

            if PASSWORD in args_raw:
                args["wpa_psk"] = str(args_raw[PASSWORD])
            if STATE in args_raw:
                args["radio"] = str(converters.int_from_bool(args_raw[STATE]))

            # Name arguments correctly
            service_args = {f"{prefix}_{arg}": value for arg, value in args.items()}

            return await self.api.async_service_generic(
                service="restart_wireless",
                arguments=service_args,
                expect_modify=True,
            )
        return False

    async def async_parental_control(self, **kwargs: Any) -> bool:
        """Adjust parental control rules."""

        raw = kwargs.get("raw", None)
        if raw is None:
            return False

        rules_to_change = []

        state = raw.get(STATE)

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
                            type=state,
                        )
                    )
                else:
                    _LOGGER.warning(
                        "Parental control rule is missing MAC address. This rule is skipped"
                    )
        # Entities are set
        elif "entities" in raw:
            entities = raw["entities"]
            entity_reg = er.async_get(self.hass)
            for entity in entities:
                reg_value = entity_reg.async_get(entity)
                if not isinstance(reg_value, er.RegistryEntry):
                    continue
                capabilities: dict[str, Any] = helpers.as_dict(reg_value.capabilities)
                rules_to_change.append(
                    FilterDevice(
                        mac=capabilities[MAC].upper(),
                        name=capabilities[NAME],
                        type=state,
                    )
                )
        if state == "remove":
            _LOGGER.debug("Removing parental control rules")
            rules = await self.api.async_remove_parental_control_rules(
                rules=rules_to_change
            )
            return rules != {}
        if state in SERVICE_ALLOWED_DEVICE_INTERNET_ACCCESS:
            _LOGGER.debug("Setting parental control rules")
            return await self.api.async_set_parental_control_rules(
                rules=rules_to_change
            )
        return False

    async def async_port_forwarding(self, **kwargs: Any) -> bool:
        """Adjust port forwarding rules."""

        raw = kwargs.get("raw", None)
        if raw is None or ACTION not in raw:
            return False

        action = raw[ACTION]

        # Remove all for IP
        if action == "remove_ip":
            ips = None
            # IP or IPs list set
            if IPS in raw:
                ips = raw[IPS]
            elif IP in raw:
                ips = raw[IP]

            # IP(s) not found
            if ips is None:
                return False

            # Remove all the rules for IP(s)
            await self.api.async_remove_port_forwarding_rules(ips=ips)
            return True

        # If not enough data provided
        if IP not in raw or PORT_EXTERNAL not in raw or PROTOCOL not in raw:
            _LOGGER.warning("Port forwarding service did not receive enough parameters")
            return False

        # Check that protocol is correct
        protocol = raw[PROTOCOL].upper()
        if protocol not in SERVICE_ALLOWED_PORT_FORWARDING_PROTOCOL:
            _LOGGER.warning(
                "Wrong protocol %s set for port forwarding service. Please use one of %s",
                protocol,
                SERVICE_ALLOWED_PORT_FORWARDING_PROTOCOL,
            )

        # Create new rule
        rule = PortForwarding(
            name=raw.get(NAME),
            ip=raw[IP],
            port=raw.get(PORT),
            protocol=raw[PROTOCOL],
            ip_external=raw.get(IP_EXTERNAL),
            port_external=raw[PORT_EXTERNAL],
        )

        # Apply the action
        if action == "set":
            return await self.api.async_set_port_forwarding_rules(rules=rule)
        if action == "remove":
            await self.api.async_remove_port_forwarding_rules(rules=rule)
            return True

        return False

    # <- SERVICES
