"""Tests for the bridge module / Part 99 / Properties."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from custom_components.asusrouter import bridge as bridge_module
from custom_components.asusrouter.bridge import ARBridge
from custom_components.asusrouter.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
import pytest

from tests.helpers import AsyncPatch, SyncPatch

DEFAULT_BRAND = "ASUSTek"
DEFAULT_NAME = "AsusRouter"


FAKE_HOSTNAME = "hostname"
FAKE_USERNAME = "username"
FAKE_PASSWORD = "password"
FAKE_SSL = True
FAKE_PORT = 8443

FAKE_MAC = "00:11:22:33:44:55"
FAKE_SERIAL = "123456789"
FAKE_BRAND = "ASUSTek"
FAKE_MODEL = "model"
FAKE_PRODUCT_ID = "product_id"
FAKE_FIRMWARE = "1.0.0"

FAKE_CONFIGS: dict[str, Any] = {
    CONF_HOST: FAKE_HOSTNAME,
    CONF_USERNAME: FAKE_USERNAME,
    CONF_PASSWORD: FAKE_PASSWORD,
    CONF_SSL: FAKE_SSL,
    CONF_PORT: FAKE_PORT,
}
FAKE_OPTIONS: dict[str, Any] = {}


def mock_identity(
    brand: Any = FAKE_BRAND,
    firmware: Any = FAKE_FIRMWARE,
    mac: Any = FAKE_MAC,
    model: Any = FAKE_MODEL,
    product_id: Any = FAKE_PRODUCT_ID,
    serial: Any = FAKE_SERIAL,
) -> Mock:
    """Mock an identity."""

    identity = Mock()
    identity.brand = brand
    identity.firmware = firmware
    identity.mac = mac
    identity.model = model
    identity.product_id = product_id
    identity.serial = serial
    return identity


@pytest.mark.parametrize(
    ("api_connected"),
    [
        (True),
        (False),
    ],
)
def test_api(api_connected: bool) -> None:
    """Test the api property."""

    def mock_api(connected: bool) -> Mock:
        """Make a mock api."""

        api = Mock()
        api.connected = connected
        return api

    with (
        patch(
            "custom_components.asusrouter.bridge.async_create_clientsession"
        ),
        patch("custom_components.asusrouter.bridge.get_cookie_jar"),
        patch.object(
            ARBridge, "_get_api", return_value=mock_api(api_connected)
        ),
    ):
        bridge = ARBridge(
            Mock(),
            FAKE_CONFIGS,
            FAKE_OPTIONS,
        )

        assert bridge.api.connected is api_connected
        assert bridge.connected is api_connected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mac", "serial", "expected"),
    [
        (FAKE_MAC, FAKE_SERIAL, {(DOMAIN, FAKE_MAC), (DOMAIN, FAKE_SERIAL)}),
        (None, FAKE_SERIAL, {(DOMAIN, FAKE_SERIAL)}),
        (FAKE_MAC, None, {(DOMAIN, FAKE_MAC)}),
        (None, None, set()),
    ],
    ids=[
        "mac_and_serial",
        "no_mac_serial",
        "mac_no_serial",
        "no_mac_no_serial",
    ],
)
async def test_identifiers(
    mac: str | None,
    serial: str | None,
    expected: set[tuple[str, str]],
    create_clientsession: AsyncPatch,
    get_cookie_jar: SyncPatch,
    format_mac: SyncPatch,
) -> None:
    """Test the identifiers property."""

    identity = mock_identity(mac=mac, serial=serial)

    def mock_api() -> Mock:
        """Make a mock api."""

        api = Mock()
        api.async_connect = AsyncMock()
        api.async_get_identity = AsyncMock(return_value=identity)
        return api

    mock_create_clientsession = create_clientsession(bridge_module)
    mock_format_mac = format_mac()
    mock_get_cookie_jar = get_cookie_jar()

    with patch.object(ARBridge, "_get_api", return_value=mock_api()):
        bridge = ARBridge(
            Mock(),
            FAKE_CONFIGS,
            FAKE_OPTIONS,
        )
        await bridge.async_connect()

        assert bridge.identifiers == expected

        mock_create_clientsession.assert_called_once()
        if mac is not None:
            mock_format_mac.assert_called_once()
        mock_get_cookie_jar.assert_called_once()


@pytest.mark.asyncio
async def test_before_connect(
    create_clientsession: AsyncPatch,
    get_cookie_jar: SyncPatch,
) -> None:
    """Test the properties before connecting."""

    mock_create_clientsession = create_clientsession(bridge_module)
    mock_get_cookie_jar = get_cookie_jar()

    with patch.object(ARBridge, "_get_api"):
        bridge = ARBridge(
            Mock(),
            FAKE_CONFIGS,
            FAKE_OPTIONS,
        )

        expected_configuration_url = (
            f"http{'s' if FAKE_SSL else ''}://{FAKE_HOSTNAME}:{FAKE_PORT}"
        )

        assert bridge.configuration_url == expected_configuration_url
        assert bridge.identity is None
        assert bridge.manufacturer == DEFAULT_BRAND
        assert bridge.model is None
        assert bridge.model_id is None
        assert bridge.name == DEFAULT_NAME
        assert bridge.serial_number is None
        assert bridge.sw_version is None

        mock_create_clientsession.assert_called_once()
        mock_get_cookie_jar.assert_called_once()


@pytest.mark.asyncio
async def test_after_connect(
    create_clientsession: AsyncPatch,
    get_cookie_jar: SyncPatch,
    format_mac: SyncPatch,
) -> None:
    """Test the properties after connecting."""

    webpanel = "webpanel"
    identity = mock_identity()

    def _mock_api() -> Mock:
        """Make a mock api."""

        api = Mock()
        api.async_connect = AsyncMock()
        api.async_get_identity = AsyncMock(return_value=identity)
        api.webpanel = webpanel
        return api

    mock_create_clientsession = create_clientsession(bridge_module)
    mock_format_mac = format_mac()
    mock_get_cookie_jar = get_cookie_jar()

    mock_api = _mock_api()

    with patch.object(ARBridge, "_get_api", return_value=mock_api):
        bridge = ARBridge(
            Mock(),
            FAKE_CONFIGS,
            FAKE_OPTIONS,
        )
        await bridge.async_connect()

        assert bridge.configuration_url == webpanel
        assert bridge.identity == identity
        assert bridge.manufacturer == FAKE_BRAND
        assert bridge.model == FAKE_MODEL
        assert bridge.model_id == FAKE_PRODUCT_ID
        assert bridge.name == FAKE_MODEL
        assert bridge.serial_number == FAKE_SERIAL
        assert bridge.sw_version == FAKE_FIRMWARE

        mock_create_clientsession.assert_called_once()
        mock_get_cookie_jar.assert_called_once()

        mock_api.async_connect.assert_awaited_once()
        mock_api.async_get_identity.assert_awaited_once()

        mock_format_mac.assert_called_once_with(identity.mac)
