"""Tests for the bridge module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouter
from asusrouter.const import DEFAULT_IDENTITY_BRAND
from asusrouter.modules.aimesh import (
    ARAiMeshNode,
    ARAiMeshRole,
    ARAiMeshTopology,
)
from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.device.identity import ARDeviceIdentity
from asusrouter.modules.firmware.version import ARFirmware
from asusrouter.modules.support import ARSupportType
from asusrouter.tools.identifiers.mac import MacAddress
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.helpers.device_registry import DeviceInfo
import pytest

from custom_components.asusrouter.bridge import API_CONFIG, ARBridge
from custom_components.asusrouter.const import (
    CONF_DEFAULT_PORT,
    DEFAULT_IDENTITY_NAME,
    DOMAIN,
)
from tests.helpers import SyncPatch

pytestmark = pytest.mark.asyncio

CONFIGS: dict[str, Any] = {
    CONF_HOST: "192.168.1.1",
    CONF_USERNAME: "user",
    CONF_PASSWORD: "password",
    CONF_SSL: True,
}

MAC = MacAddress("AA:BB:CC:DD:EE:FF")
# The library normalises the MAC, and format_mac keeps that form
MAC_FORMATTED = str(MAC)
SERIAL = "SERIAL123"
WEBPANEL = "https://192.168.1.1:8443"

FIRMWARE = ARFirmware((3, 0, 0, 4), 388, 1, 0)
FIRMWARE_STRING = "3.0.0.4.388.1_0"

NODE_MAC = MacAddress("AA:BB:CC:DD:EE:01")
OTHER_NODE_MAC = MacAddress("AA:BB:CC:DD:EE:02")
ROOT_MAC = MacAddress("AA:BB:CC:DD:EE:03")
VIA_DEVICE_ID = "router_device_id"


def _get_node(
    mac: MacAddress = NODE_MAC,
    role: ARAiMeshRole = ARAiMeshRole.NODE,
    alias: str | MacAddress | None = None,
    model: str | None = "Node",
) -> ARAiMeshNode:
    """Create an AiMesh node as the library reports it."""

    return ARAiMeshNode(mac=mac, alias=alias, model=model, role=role)


def _get_identity(
    mac: MacAddress | None = MAC,
    serial: str | None = SERIAL,
    model: str | None = "Model",
    firmware: ARFirmware | None = None,
) -> ARDeviceIdentity:
    """Create a device identity as the library reports it."""

    identity = ARDeviceIdentity()
    identity._brand = "Brand"
    identity._firmware = firmware if firmware else ARFirmware()
    identity._mac = mac
    identity._model = model
    identity._model_original = "MODEL_ORIGINAL"
    identity._serial = serial
    identity._support = {ARSupportType.AIMESH: True}

    return identity


async def _get_bridge(
    identity: ARDeviceIdentity | None = None,
    configs: dict[str, Any] | None = None,
) -> ARBridge:
    """Create a bridge with the library API replaced by a mock."""

    with (
        patch(
            "custom_components.asusrouter.bridge.async_create_clientsession",
            Mock(),
        ),
        patch.object(ARBridge, "_get_api", Mock(spec=AsusRouter)),
    ):
        bridge = ARBridge(Mock(), configs if configs else CONFIGS)

    bridge._api = Mock(
        async_connect=AsyncMock(),
        async_close=AsyncMock(),
        description=identity if identity else ARDeviceIdentity(),
        webpanel=WEBPANEL,
    )

    return bridge


# ---------------------------
# API -->
# ---------------------------


@pytest.mark.parametrize(
    ("configs", "expected_port"),
    [
        (CONFIGS, CONF_DEFAULT_PORT),
        ({**CONFIGS, CONF_PORT: 8443}, 8443),
    ],
)
async def test_get_api(configs: dict[str, Any], expected_port: int) -> None:
    """Test that the library API is created with the HA configs."""

    session = Mock()

    with patch("custom_components.asusrouter.bridge.AsusRouter") as mock_api:
        ARBridge._get_api(configs, session)

    mock_api.assert_called_once_with(
        hostname=configs[CONF_HOST],
        username=configs[CONF_USERNAME],
        password=configs[CONF_PASSWORD],
        port=expected_port,
        use_ssl=configs[CONF_SSL],
        session=session,
        config=API_CONFIG,
    )


async def test_init_creates_unsafe_cookie_jar() -> None:
    """Test that the session is created with a router-compatible jar."""

    with (
        patch(
            "custom_components.asusrouter.bridge.async_create_clientsession"
        ) as mock_session,
        patch.object(ARBridge, "_get_api", Mock(spec=AsusRouter)),
    ):
        ARBridge(Mock(), CONFIGS)

    cookie_jar = mock_session.call_args.kwargs["cookie_jar"]

    assert mock_session.call_args.kwargs["verify_ssl"] is False
    assert cookie_jar._unsafe is True
    assert cookie_jar._quote_cookie is False


async def test_api_property() -> None:
    """Test that the API is served as it is."""

    bridge = await _get_bridge()

    assert bridge.api is bridge._api


async def test_identity_property() -> None:
    """Test that the identity is the library device description."""

    identity = _get_identity()
    bridge = await _get_bridge(identity)

    assert bridge.identity is identity


def _get_topology() -> ARAiMeshTopology:
    """Create a topology listing the device among its nodes."""

    nodes = [
        _get_node(MAC, ARAiMeshRole.ROUTER),
        _get_node(NODE_MAC),
        # An offline node is reported as a router
        _get_node(ROOT_MAC, ARAiMeshRole.ROUTER),
    ]

    return ARAiMeshTopology(nodes={node.mac: node for node in nodes})


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (AROperationMode.ROUTER, [NODE_MAC, ROOT_MAC]),
        (AROperationMode.UNKNOWN, [NODE_MAC, ROOT_MAC]),
        # A node sees the whole mesh but cannot serve the others
        (AROperationMode.AIMESH_NODE, []),
    ],
)
async def test_get_nodes(
    mode: AROperationMode, expected: list[MacAddress]
) -> None:
    """Test that every node but the device itself is served through it."""

    identity = _get_identity()
    identity._operation_mode = mode

    bridge = await _get_bridge(identity)

    nodes = bridge.get_nodes(_get_topology())
    assert [node.mac for node in nodes] == expected


@pytest.mark.parametrize(
    ("mode", "support", "expected"),
    [
        (AROperationMode.ROUTER, True, True),
        (AROperationMode.UNKNOWN, True, True),
        (AROperationMode.AIMESH_NODE, True, False),
        # No AiMesh to serve
        (AROperationMode.ROUTER, False, False),
        (AROperationMode.ROUTER, None, False),
    ],
)
async def test_serves_mesh(
    mode: AROperationMode, support: bool | None, expected: bool
) -> None:
    """Test that only a router supporting AiMesh serves it."""

    identity = _get_identity()
    identity._operation_mode = mode
    identity._support = (
        {} if support is None else {ARSupportType.AIMESH: support}
    )

    bridge = await _get_bridge(identity)

    assert bridge.serves_mesh is expected


# ---------------------------
# <-- API
# ---------------------------

# ---------------------------
# DEVICE -->
# ---------------------------


async def test_device_info_without_identity() -> None:
    """Test the device information available before connecting."""

    bridge = await _get_bridge()

    assert bridge.get_device_info(None) == DeviceInfo(
        configuration_url=WEBPANEL,
        identifiers=set(),
        # The library already defaults the brand
        manufacturer=DEFAULT_IDENTITY_BRAND,
        model=None,
        model_id=None,
        name=DEFAULT_IDENTITY_NAME,
        serial_number=None,
        sw_version=None,
    )


async def test_device_info(format_mac: SyncPatch) -> None:
    """Test that the device information is built from the identity."""

    format_mac()

    bridge = await _get_bridge(_get_identity(firmware=FIRMWARE))

    assert bridge.get_device_info(None) == DeviceInfo(
        configuration_url=WEBPANEL,
        identifiers={(DOMAIN, MAC_FORMATTED), (DOMAIN, SERIAL)},
        manufacturer="Brand",
        model="MODEL_ORIGINAL",
        model_id="Model",
        name="MODEL_ORIGINAL",
        serial_number=SERIAL,
        sw_version=FIRMWARE_STRING,
    )


async def test_device_info_mesh_node() -> None:
    """Test that the device takes its name from its AiMesh node."""

    mesh_node = _get_node(MAC, alias="Office")
    mesh_node.model_display = "Model Display"

    bridge = await _get_bridge(_get_identity())
    device_info = bridge.get_device_info(mesh_node)

    assert device_info["model"] == "Model Display"
    assert device_info["model_id"] == "Model"
    assert device_info["name"] == "Model Display (Office)"


async def test_device_info_without_model() -> None:
    """Test the fallback name when the device reports no model."""

    identity = _get_identity(model=None)
    identity._model_original = None

    bridge = await _get_bridge(identity)

    assert bridge.get_device_info(None)["name"] == DEFAULT_IDENTITY_NAME


async def test_device_info_unknown_firmware() -> None:
    """Test that an unknown firmware is reported as no version."""

    bridge = await _get_bridge(_get_identity())

    assert bridge.get_device_info(None)["sw_version"] is None


@pytest.mark.parametrize(
    ("mac", "serial", "expected"),
    [
        (MAC, SERIAL, {(DOMAIN, MAC_FORMATTED), (DOMAIN, SERIAL)}),
        (None, SERIAL, {(DOMAIN, SERIAL)}),
        (MAC, None, {(DOMAIN, MAC_FORMATTED)}),
        (None, None, set()),
    ],
)
async def test_get_identifiers(
    format_mac: SyncPatch,
    mac: MacAddress | None,
    serial: str | None,
    expected: set[tuple[str, str]],
) -> None:
    """Test that only the known identifiers are reported."""

    format_mac()

    identity = _get_identity(mac=mac, serial=serial)

    assert ARBridge._get_identifiers(identity) == expected


@pytest.mark.parametrize(
    ("models", "expected"),
    [
        (("Display", "Original", "Model"), "Display"),
        ((None, "Original", "Model"), "Original"),
        # Some nodes report an empty product id
        ((None, None, ""), None),
        ((), None),
    ],
)
async def test_get_model(
    models: tuple[str | None, ...], expected: str | None
) -> None:
    """Test that the first reported model is used."""

    assert ARBridge._get_model(*models) == expected


@pytest.mark.parametrize(
    ("alias", "model", "expected"),
    [
        ("Living room", "Node", "Node (Living room)"),
        # An alias never set by the user is the node MAC
        (NODE_MAC, "Node", "Node"),
        (None, "Node", "Node"),
        ("Node", "Node", "Node"),
        ("Living room", None, f"{DEFAULT_IDENTITY_NAME} (Living room)"),
    ],
)
async def test_get_name(
    alias: str | MacAddress | None, model: str | None, expected: str
) -> None:
    """Test that the name keeps the model and adds a real alias."""

    assert ARBridge._get_name(model, alias) == expected


@pytest.mark.parametrize(
    ("firmware", "expected"),
    [
        (FIRMWARE, FIRMWARE_STRING),
        # Placeholders of an unknown firmware
        (ARFirmware(), None),
    ],
)
async def test_get_sw_version(
    firmware: ARFirmware, expected: str | None
) -> None:
    """Test that only a known firmware is reported as the version."""

    assert ARBridge._get_sw_version(firmware) == expected


@pytest.mark.parametrize(
    ("firmware", "sw_version"),
    [
        (FIRMWARE, FIRMWARE_STRING),
        (ARFirmware(), None),
    ],
)
async def test_get_node_device_info(
    firmware: ARFirmware, sw_version: str | None
) -> None:
    """Test that a node is a device linked to its router."""

    node = _get_node(alias="Living room")
    node.model_original = "NODE_ORIGINAL"
    node.model_display = "Node Display"
    node.firmware = firmware

    bridge = await _get_bridge(_get_identity())

    assert bridge.get_node_device_info(node, VIA_DEVICE_ID) == DeviceInfo(
        identifiers={(DOMAIN, str(NODE_MAC))},
        manufacturer="Brand",
        model="Node Display",
        model_id="Node",
        name="Node Display (Living room)",
        sw_version=sw_version,
        via_device_id=VIA_DEVICE_ID,
    )


# ---------------------------
# <-- DEVICE
# ---------------------------

# ---------------------------
# CONNECTION -->
# ---------------------------


@pytest.mark.parametrize("method", ["async_connect", "async_close"])
async def test_connection_methods(method: str) -> None:
    """Test that the connection methods are delegated to the library."""

    bridge = await _get_bridge()

    await getattr(bridge, method)()

    getattr(bridge._api, method).assert_awaited_once()


# ---------------------------
# <-- CONNECTION
# ---------------------------
