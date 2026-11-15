"""AsusRouter network module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

from asusrouter.modules.network import (
    ARNetworkAction,
    ARNetworkBackend,
    ARNetworkField,
    ARNetworkHandle,
    ARNetworkSchedule,
    ARNetworkSourceUniversal,
    ARNetworkType,
)
from asusrouter.modules.wifi import ARWiFiMacFilterMode
from homeassistant.const import EntityCategory

from ..entity import ARBinarySensorDescription, ARSwitchDescription
from ..helpers import to_str, to_value

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)

_SDN = "sdn"
_LEGACY = "legacy"


class _Network(NamedTuple):
    """A network profile with its type."""

    type: ARNetworkType
    profile: dict[ARNetworkField, Any]


def _get_key(handle: ARNetworkHandle) -> tuple[Any, ...] | None:
    """Get the key of a network by its handle, None without a switch."""

    if handle.backend is ARNetworkBackend.SDN and handle.sdn_idx is not None:
        return (_SDN, handle.sdn_idx)
    # A legacy network is keyed by the first unit of its bands, its main
    # network has no slot and is switched by its radio
    if handle.backend is ARNetworkBackend.LEGACY and handle.units:
        unit, slot = handle.units[0]
        if slot is not None:
            return (_LEGACY, unit, slot)

    return None


def _get_networks(data: Any) -> dict[tuple[Any, ...], _Network]:
    """Get the networks with a switch by their key."""

    networks: dict[tuple[Any, ...], _Network] = {}
    if not isinstance(data, dict):
        return networks

    for network_type, profiles in data.items():
        # Turning the backhaul off breaks the AiMesh
        if network_type is ARNetworkType.MAINBH:
            continue
        for profile in profiles:
            handle = profile.get(ARNetworkField.HANDLE)
            if isinstance(handle, ARNetworkHandle) and (
                key := _get_key(handle)
            ):
                networks[key] = _Network(network_type, profile)

    return networks


def _get_label(key: tuple[Any, ...]) -> str:
    """Get the label of a network key."""

    if key[0] == _SDN:
        return f"SDN {key[1]}"

    return f"{key[1]}.{key[2]}"


def _is_served(bridge: ARBridge) -> bool:
    """Check whether the device serves its own networks."""

    return not bridge.is_node


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
    ARSwitchDescription(
        key="network",
        translation_key="network",
        source=ARNetworkSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        # The device reports its networks, not keyed by its MAC
        data_fn=lambda data: data,
        keys_fn=_get_networks,
        item_fn=lambda data, key: _get_networks(data).get(key),
        unique_id_fn=lambda key: f"Network {_get_label(key)}",
        # The handle names the network until its SSID is read
        placeholders_fn=lambda key: {"name": _get_label(key)},
        value_fn=lambda network: network.profile.get(ARNetworkField.ENABLED),
        attributes_fn=_get_attributes,
        name_fn=_get_name,
        action_fn=_get_action,
        remove_missing=True,
        supported_fn=_is_served,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)
