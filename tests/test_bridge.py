"""Tests for the bridge module."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

from asusrouter import AsusRouter
from asusrouter.config import ARConfigKey as ARConfKey
from asusrouter.const import DEFAULT_IDENTITY_BRAND
from asusrouter.modules.firmware.version import ARFirmware
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.helpers.device_registry import DeviceInfo
import pytest

from custom_components.asusrouter.bridge import ARBridge
from custom_components.asusrouter.const import (
    CONF_DEFAULT_PORT,
    DEFAULT_IDENTITY_NAME,
    DOMAIN,
)
from tests.conftest import UniversalMockPatcher
from tests.helpers import SyncPatch

pytestmark = pytest.mark.asyncio

CONFIGS: dict[str, Any] = {
    CONF_HOST: "192.168.1.1",
    CONF_USERNAME: "user",
    CONF_PASSWORD: "password",
    CONF_SSL: True,
}

MAC = "AA:BB:CC:DD:EE:FF"
PORT = 1234
SERIAL = "SERIAL123"


async def _get_bridge(
    configs: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> ARBridge:
    """Create a bridge with the library API replaced by a mock."""

    with (
        patch(
            "custom_components.asusrouter.bridge.async_create_clientsession",
            Mock(),
        ),
        patch.object(ARBridge, "_get_api", Mock(spec=AsusRouter)),
    ):
        return ARBridge(Mock(), configs if configs else CONFIGS, options)


def _get_identity(
    mac: str | None = MAC,
    serial: str | None = SERIAL,
    firmware: ARFirmware | None = None,
) -> Mock:
    """Create a device identity mock."""

    return Mock(
        brand="Brand",
        firmware=firmware if firmware else ARFirmware(),
        mac=mac,
        model="Model",
        model_original="MODEL_ORIGINAL",
        serial=serial,
    )


async def test_init_stores_configs_and_options() -> None:
    """Test that options overwrite the configs on init."""

    bridge = await _get_bridge(CONFIGS, {CONF_PORT: PORT})

    assert bridge._configs[CONF_PORT] == PORT
    assert bridge._configs[CONF_HOST] == CONFIGS[CONF_HOST]
    # The original configs are not mutated
    assert CONF_PORT not in CONFIGS


async def test_init_defines_default_properties() -> None:
    """Test the properties available before connecting."""

    bridge = await _get_bridge()

    assert bridge.identifiers == set()
    assert bridge.manufacturer == DEFAULT_IDENTITY_BRAND
    assert bridge.model is None
    assert bridge.model_id is None
    assert bridge.name == DEFAULT_IDENTITY_NAME
    assert bridge.serial_number is None
    assert bridge.sw_version is None


async def test_get_api_config() -> None:
    """Test the instance configuration passed to the library."""

    bridge = await _get_bridge()

    assert bridge._get_api_config() == {
        ARConfKey.OPTIMISTIC_TEMPERATURE: True,
        ARConfKey.NOTIFIED_OPTIMISTIC_TEMPERATURE: True,
    }


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
    config = {ARConfKey.OPTIMISTIC_TEMPERATURE: True}

    with patch("custom_components.asusrouter.bridge.AsusRouter") as mock_api:
        ARBridge._get_api(configs, session, config)

    mock_api.assert_called_once_with(
        hostname=configs[CONF_HOST],
        username=configs[CONF_USERNAME],
        password=configs[CONF_PASSWORD],
        port=expected_port,
        use_ssl=configs[CONF_SSL],
        session=session,
        config=config,
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


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("api", "_api"),
        ("configuration_url", "webpanel"),
        ("connected", "connected"),
    ],
)
async def test_properties_from_api(attribute: str, value: str) -> None:
    """Test the properties served directly by the library API."""

    bridge = await _get_bridge()
    bridge._api = Mock(webpanel="https://192.168.1.1:8443", connected=True)

    expected = bridge._api if value == "_api" else getattr(bridge._api, value)

    assert getattr(bridge, attribute) == expected


async def test_identity_property() -> None:
    """Test that the identity is the library device description."""

    bridge = await _get_bridge()
    identity = _get_identity()
    bridge._api = Mock(description=identity)

    assert bridge.identity is identity


async def test_device_info(format_mac: SyncPatch) -> None:
    """Test that the device information is built from the identity."""

    format_mac()

    bridge = await _get_bridge()
    bridge._api = Mock(
        async_connect=AsyncMock(), webpanel="https://192.168.1.1:8443"
    )

    with patch.object(
        ARBridge,
        "identity",
        new_callable=PropertyMock,
        return_value=_get_identity(
            firmware=ARFirmware((3, 0, 0, 4), 388, 1, 0)
        ),
    ):
        await bridge.async_connect()

    assert bridge.device_info == DeviceInfo(
        configuration_url="https://192.168.1.1:8443",
        identifiers={(DOMAIN, MAC), (DOMAIN, SERIAL)},
        manufacturer="Brand",
        model="Model",
        model_id="MODEL_ORIGINAL",
        name="Model",
        serial_number=SERIAL,
        sw_version="3.0.0.4.388.1_0",
    )


async def test_async_connect(
    universal_mock: UniversalMockPatcher,
    format_mac: SyncPatch,
) -> None:
    """Test that connecting fills the device properties."""

    format_mac()

    bridge = await _get_bridge()
    bridge._api = Mock(async_connect=AsyncMock())
    identity = _get_identity(firmware=ARFirmware((3, 0, 0, 4), 388, 1, 0))

    with patch.object(
        ARBridge, "identity", new_callable=PropertyMock, return_value=identity
    ):
        await bridge.async_connect()

    bridge._api.async_connect.assert_awaited_once()
    assert bridge.identifiers == {(DOMAIN, MAC), (DOMAIN, SERIAL)}
    assert bridge.manufacturer == "Brand"
    assert bridge.model == "Model"
    assert bridge.model_id == "MODEL_ORIGINAL"
    assert bridge.name == "Model"
    assert bridge.serial_number == SERIAL
    assert bridge.sw_version == "3.0.0.4.388.1_0"


@pytest.mark.parametrize(
    ("mac", "serial", "expected"),
    [
        (MAC, SERIAL, {(DOMAIN, MAC), (DOMAIN, SERIAL)}),
        (None, SERIAL, {(DOMAIN, SERIAL)}),
        (MAC, None, {(DOMAIN, MAC)}),
        (None, None, set()),
    ],
)
async def test_async_connect_identifiers(
    format_mac: SyncPatch,
    mac: str | None,
    serial: str | None,
    expected: set[tuple[str, str]],
) -> None:
    """Test that only the known identifiers are reported."""

    format_mac()

    bridge = await _get_bridge()
    bridge._api = Mock(async_connect=AsyncMock())

    with patch.object(
        ARBridge,
        "identity",
        new_callable=PropertyMock,
        return_value=_get_identity(mac=mac, serial=serial),
    ):
        await bridge.async_connect()

    assert bridge.identifiers == expected


async def test_async_connect_no_model(format_mac: SyncPatch) -> None:
    """Test the fallback name when the device reports no model."""

    format_mac()

    bridge = await _get_bridge()
    bridge._api = Mock(async_connect=AsyncMock())
    identity = _get_identity()
    identity.model = None

    with patch.object(
        ARBridge, "identity", new_callable=PropertyMock, return_value=identity
    ):
        await bridge.async_connect()

    assert bridge.name == DEFAULT_IDENTITY_NAME


async def test_async_connect_empty_firmware(format_mac: SyncPatch) -> None:
    """Test that an unknown firmware is reported as no version."""

    format_mac()

    bridge = await _get_bridge()
    bridge._api = Mock(async_connect=AsyncMock())

    with patch.object(
        ARBridge,
        "identity",
        new_callable=PropertyMock,
        return_value=_get_identity(),
    ):
        await bridge.async_connect()

    assert bridge.sw_version is None


@pytest.mark.parametrize(
    ("method", "api_method"),
    [
        ("async_disconnect", "async_disconnect"),
        ("async_clean", "async_close"),
    ],
)
async def test_connection_methods(method: str, api_method: str) -> None:
    """Test that the connection methods are delegated to the library."""

    bridge = await _get_bridge()
    bridge._api = Mock(**{api_method: AsyncMock()})

    await getattr(bridge, method)()

    getattr(bridge._api, api_method).assert_awaited_once()
