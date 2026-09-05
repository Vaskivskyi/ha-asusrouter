"""Tests for the bridge module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from asusrouter import AsusRouter
from asusrouter.const import DEFAULT_IDENTITY_BRAND
from asusrouter.modules.device.identity import ARDeviceIdentity
from asusrouter.modules.firmware.version import ARFirmware
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


# ---------------------------
# <-- API
# ---------------------------

# ---------------------------
# DEVICE -->
# ---------------------------


async def test_device_info_without_identity() -> None:
    """Test the device information available before connecting."""

    bridge = await _get_bridge()

    assert bridge.device_info == DeviceInfo(
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

    assert bridge.device_info == DeviceInfo(
        configuration_url=WEBPANEL,
        identifiers={(DOMAIN, MAC_FORMATTED), (DOMAIN, SERIAL)},
        manufacturer="Brand",
        model="Model",
        model_id="MODEL_ORIGINAL",
        name="Model",
        serial_number=SERIAL,
        sw_version=FIRMWARE_STRING,
    )


async def test_device_info_without_model() -> None:
    """Test the fallback name when the device reports no model."""

    bridge = await _get_bridge(_get_identity(model=None))

    assert bridge.device_info["name"] == DEFAULT_IDENTITY_NAME


async def test_device_info_unknown_firmware() -> None:
    """Test that an unknown firmware is reported as no version."""

    bridge = await _get_bridge(_get_identity())

    assert bridge.device_info["sw_version"] is None


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
