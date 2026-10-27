"""Bridge module for AsusRouter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
from asusrouter import AsusRouter
from asusrouter.config import ARConfigKey
from asusrouter.modules.aimesh import ARAiMeshNode, ARAiMeshTopology
from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.device.identity import ARDeviceIdentity
from asusrouter.modules.firmware import ARFirmware
from asusrouter.tools.identifiers import MacAddress
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_DEFAULT_PORT, DEFAULT_IDENTITY_NAME, DOMAIN
from .helpers import to_identifier

API_CONFIG: dict[ARConfigKey, Any] = {
    # Enable automatic temperature fix and disable the notification
    ARConfigKey.OPTIMISTIC_TEMPERATURE: True,
    ARConfigKey.NOTIFIED_OPTIMISTIC_TEMPERATURE: True,
}


class ARBridge:
    """Bridge to the AsusRouter library."""

    def __init__(
        self,
        hass: HomeAssistant,
        configs: Mapping[str, Any],
    ) -> None:
        """Initialize bridge to the library."""

        session = async_create_clientsession(
            hass,
            # TODO: implement proper SSL verification eventually
            verify_ssl=False,
            # Routers set cookies for a bare IP and do not quote them
            cookie_jar=aiohttp.CookieJar(unsafe=True, quote_cookie=False),
        )

        self._api = self._get_api(configs, session)

    # ---------------------------
    # Properties -->
    # ---------------------------

    @property
    def api(self) -> AsusRouter:
        """Return API."""

        return self._api

    @property
    def identity(self) -> ARDeviceIdentity:
        """Return device identity."""

        return self._api.description

    @property
    def serves_mesh(self) -> bool:
        """Return whether the AiMesh nodes are served through this device."""

        # A node reports the whole mesh, but only the router serves its data
        return self.identity.operation_mode is not AROperationMode.AIMESH_NODE

    # ---------------------------
    # <-- Properties
    # ---------------------------

    # ---------------------------
    # AiMesh -->
    # ---------------------------

    def get_nodes(self, topology: ARAiMeshTopology) -> list[ARAiMeshNode]:
        """Return the nodes of the topology served through this device."""

        if not self.serves_mesh:
            return []

        mac = self.identity.mac
        # An offline node is reported as a router, so the role is not used
        return [node for node in topology.nodes.values() if node.mac != mac]

    # ---------------------------
    # <-- AiMesh
    # ---------------------------

    # ---------------------------
    # Connection -->
    # ---------------------------

    @staticmethod
    def _get_api(
        configs: Mapping[str, Any],
        session: aiohttp.ClientSession,
    ) -> AsusRouter:
        """Get AsusRouter API."""

        return AsusRouter(
            hostname=configs[CONF_HOST],
            username=configs[CONF_USERNAME],
            password=configs[CONF_PASSWORD],
            port=configs.get(CONF_PORT, CONF_DEFAULT_PORT),
            use_ssl=configs[CONF_SSL],
            session=session,
            config=API_CONFIG,
        )

    async def async_connect(self) -> None:
        """Connect to the device and read its identity."""

        await self._api.async_connect()

    async def async_close(self) -> None:
        """Log out from the device and release the connection."""

        await self._api.async_close()

    # ---------------------------
    # <-- Connection
    # ---------------------------

    # ---------------------------
    # Device -->
    # ---------------------------

    @staticmethod
    def _get_identifiers(identity: ARDeviceIdentity) -> set[tuple[str, str]]:
        """Get device identifiers."""

        identifiers: set[tuple[str, str]] = set()
        if identity.mac is not None:
            identifiers.add(to_identifier(identity.mac))
        if identity.serial is not None:
            identifiers.add((DOMAIN, identity.serial))

        return identifiers

    def get_device_info(self, mesh_node: ARAiMeshNode | None) -> DeviceInfo:
        """Return device information, named after its AiMesh node if known."""

        identity = self.identity
        model = self._get_model(
            mesh_node.model_display if mesh_node else None,
            identity.model_original,
            identity.model,
        )

        return DeviceInfo(
            configuration_url=self._api.webpanel,
            identifiers=self._get_identifiers(identity),
            manufacturer=identity.brand,
            model=model,
            model_id=identity.model,
            name=self._get_name(model, mesh_node.alias if mesh_node else None),
            serial_number=identity.serial,
            sw_version=self._get_sw_version(identity.firmware),
        )

    @staticmethod
    def _get_model(*models: str | None) -> str | None:
        """Get the first reported model, the friendliest first."""

        return next((model for model in models if model), None)

    @staticmethod
    def _get_name(model: str | None, alias: str | MacAddress | None) -> str:
        """Get the device name from its model and alias."""

        model = model or DEFAULT_IDENTITY_NAME
        # An alias never set by the user is reported as the node MAC
        if isinstance(alias, str) and alias != model:
            return f"{model} ({alias})"

        return model

    @staticmethod
    def _get_sw_version(firmware: ARFirmware) -> str | None:
        """Get the firmware version, None when unknown."""

        # Safelock against placeholders-filled string
        return str(firmware) if firmware.major is not None else None

    @classmethod
    def get_node_naming(cls, node: ARAiMeshNode) -> tuple[str | None, str]:
        """Return the model and the device name of an AiMesh node."""

        model = cls._get_model(
            node.model_display, node.model_original, node.model
        )

        return model, cls._get_name(model, node.alias)

    def get_node_device_info(
        self, node: ARAiMeshNode, via_device_id: str
    ) -> DeviceInfo:
        """Return device information of an AiMesh node."""

        model, name = self.get_node_naming(node)

        return DeviceInfo(
            identifiers={to_identifier(node.mac)},
            manufacturer=self.identity.brand,
            model=model,
            model_id=node.model,
            name=name,
            sw_version=self._get_sw_version(node.firmware),
            via_device_id=via_device_id,
        )

    # ---------------------------
    # <-- Device
    # ---------------------------
