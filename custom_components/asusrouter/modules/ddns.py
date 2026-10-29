"""AsusRouter DDNS module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.ddns import (
    ACTIVE_STATUSES,
    ARDdnsField,
    ARDdnsServer,
    ARDdnsSourceUniversal,
    ARDdnsStatus,
)
from homeassistant.const import EntityCategory

from ..entity import ARBinarySensorDescription
from ..helpers import to_str

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)


def _get_ddns(data: Any) -> dict[ARDdnsField, Any] | None:
    """Get the DDNS state, None when nothing was read."""

    return data if isinstance(data, dict) and data else None


def _is_router(bridge: ARBridge) -> bool:
    """Check whether the device works as a router."""

    return bridge.identity.operation_mode is AROperationMode.ROUTER


def _get_server(server: ARDdnsServer | None) -> str | None:
    """Get the device string of the DDNS server."""

    if server is None or server is ARDdnsServer.UNKNOWN:
        return None
    return server.value


def _get_status(status: ARDdnsStatus | None) -> str | None:
    """Get the device code of the DDNS status."""

    if status in (None, ARDdnsStatus.NONE, ARDdnsStatus.UNKNOWN):
        return None
    return status.value


def _get_attributes(ddns: dict[ARDdnsField, Any]) -> dict[str, Any]:
    """Get the attributes of the DDNS."""

    return {
        "enabled": ddns.get(ARDdnsField.STATE),
        "hostname": to_str(ddns.get(ARDdnsField.HOSTNAME)),
        "ip_address": to_str(ddns.get(ARDdnsField.IP_ADDRESS)),
        "old_name": to_str(ddns.get(ARDdnsField.HOSTNAME_OLD)),
        "replace_status": ddns.get(ARDdnsField.REPLACE_STATUS),
        "server": _get_server(ddns.get(ARDdnsField.SERVER)),
        "status": _get_status(ddns.get(ARDdnsField.STATUS)),
        "updated": ddns.get(ARDdnsField.UPDATED),
    }


BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    ARBinarySensorDescription(
        key="ddns",
        translation_key="ddns",
        source=ARDdnsSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="DDNS",
        # The device reports its DDNS, not keyed by its MAC
        data_fn=_get_ddns,
        value_fn=lambda ddns: bool(
            ddns.get(ARDdnsField.STATE)
            and ddns.get(ARDdnsField.STATUS) in ACTIVE_STATUSES
        ),
        attributes_fn=_get_attributes,
        supported_fn=_is_router,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)
