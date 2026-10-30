"""AsusRouter network module."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

from asusrouter.modules.common.device import AROperationMode
from asusrouter.modules.network import (
    ARNetworkAction,
    ARNetworkBackend,
    ARNetworkField,
    ARNetworkHandle,
    ARNetworkSchedule,
    ARNetworkSourceUniversal,
    ARNetworkType,
)
from asusrouter.modules.wifi import ARWiFiBand, ARWiFiMacFilterMode
from homeassistant.const import EntityCategory

from ..entity import ARBinarySensorDescription, ARSwitchDescription
from ..helpers import to_str, to_value

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)

# Indexes of SDN networks, above the firmware default of 19 rules
_SDN_INDEXES = range(1, 33)
# A wireless unit per band and the guest slots of each unit
_LEGACY_UNITS = range(len(ARWiFiBand) - 1)
_LEGACY_SLOTS = range(1, 8)


class _Network(NamedTuple):
    """A network profile with its type."""

    type: ARNetworkType
    profile: dict[ARNetworkField, Any]


def _find(
    data: Any, match: Callable[[ARNetworkHandle], bool]
) -> _Network | None:
    """Find the network whose handle matches, None when not reported."""

    if not isinstance(data, dict):
        return None

    for network_type, profiles in data.items():
        for profile in profiles:
            handle = profile.get(ARNetworkField.HANDLE)
            if isinstance(handle, ARNetworkHandle) and match(handle):
                return _Network(network_type, profile)

    return None


def _is_served(bridge: ARBridge) -> bool:
    """Check whether the device serves its own networks."""

    return bridge.identity.operation_mode is not AROperationMode.AIMESH_NODE


def _get_name(network: _Network) -> str | None:
    """Get the SSID of a network."""

    return to_str(network.profile.get(ARNetworkField.SSID))


def _get_backhaul(data: Any) -> _Network | None:
    """Get the backhaul network, None when not reported."""

    profiles = (
        data.get(ARNetworkType.MAINBH) if isinstance(data, dict) else None
    )
    return _Network(ARNetworkType.MAINBH, profiles[0]) if profiles else None


def _get_attributes(network: _Network) -> dict[str, Any]:
    """Get the attributes of a network."""

    profile = network.profile
    schedule = profile.get(ARNetworkField.SCHEDULE_MODE)

    return {
        "ap_isolate": profile.get(ARNetworkField.AP_ISOLATE),
        "bands": [
            band.value for band in profile.get(ARNetworkField.BANDS, [])
        ],
        "hidden": profile.get(ARNetworkField.HIDDEN),
        "lan_access": profile.get(ARNetworkField.LAN_ACCESS),
        "mac_filter_mode": to_value(
            profile.get(ARNetworkField.MAC_FILTER_MODE), ARWiFiMacFilterMode
        ),
        "schedule_mode": (
            schedule.name.lower()
            if isinstance(schedule, ARNetworkSchedule)
            and schedule is not ARNetworkSchedule.UNKNOWN
            else None
        ),
        "type": (
            None
            if network.type is ARNetworkType.UNKNOWN
            else network.type.value
        ),
        "wifi7": profile.get(ARNetworkField.WIFI7),
    }


def _get_action(state: bool, network: _Network) -> ARNetworkAction:
    """Get the action turning a network on or off."""

    return ARNetworkAction(network.profile[ARNetworkField.HANDLE], state)


def _get_switch(
    key: str, unique_id_name: str, match: Callable[[ARNetworkHandle], bool]
) -> ARSwitchDescription:
    """Get the description of the switch of a network."""

    return ARSwitchDescription(
        key=key,
        translation_key="network",
        source=ARNetworkSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        # The device reports its networks, not keyed by its MAC
        data_fn=lambda data: _find(data, match),
        value_fn=lambda network: network.profile.get(ARNetworkField.ENABLED),
        attributes_fn=_get_attributes,
        name_fn=_get_name,
        action_fn=_get_action,
        # Turning the backhaul off breaks the AiMesh
        exists_fn=lambda network: network.type is not ARNetworkType.MAINBH,
        supported_fn=_is_served,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    )


def _get_sdn_switch(index: int) -> ARSwitchDescription:
    """Get the description of the switch of an SDN network."""

    return _get_switch(
        f"network_sdn_{index}",
        f"Network SDN {index}",
        lambda handle: (
            handle.backend is ARNetworkBackend.SDN and handle.sdn_idx == index
        ),
    )


def _get_legacy_switch(unit: int, slot: int) -> ARSwitchDescription:
    """Get the description of the switch of a legacy guest network."""

    # A network is keyed by the first unit of its bands
    return _get_switch(
        f"network_{unit}_{slot}",
        f"Network {unit}.{slot}",
        lambda handle: (
            handle.backend is ARNetworkBackend.LEGACY
            and bool(handle.units)
            and handle.units[0] == (unit, slot)
        ),
    )


BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    ARBinarySensorDescription(
        key="backhaul_network",
        translation_key="backhaul_network",
        source=ARNetworkSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name="Backhaul network",
        # The device reports its networks, not keyed by its MAC
        data_fn=_get_backhaul,
        value_fn=lambda network: network.profile.get(ARNetworkField.ENABLED),
        attributes_fn=_get_attributes,
        supported_fn=_is_served,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)

SWITCHES: tuple[ARSwitchDescription, ...] = (
    *(_get_sdn_switch(index) for index in _SDN_INDEXES),
    *(
        _get_legacy_switch(unit, slot)
        for unit in _LEGACY_UNITS
        for slot in _LEGACY_SLOTS
    ),
)
