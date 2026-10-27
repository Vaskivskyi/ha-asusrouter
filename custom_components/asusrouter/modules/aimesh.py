"""AsusRouter AiMesh module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asusrouter.modules.aimesh import (
    ARAiMeshMedium,
    ARAiMeshNode,
    ARAiMeshSourceUniversal,
    ARAiMeshTopology,
)
from asusrouter.modules.ports import ARPortSpeed
from asusrouter.modules.wifi import ARWiFiBand
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfDataRate,
)
from homeassistant.helpers.device_registry import format_mac

from ..entity import ARBinarySensorDescription, ARSensorDescription
from ..topology import TOPOLOGY_INTERVAL

if TYPE_CHECKING:
    from ..bridge import ARBridge


def _serves_mesh(bridge: ARBridge) -> bool:
    """Check whether the AiMesh is served through the device."""

    return bridge.serves_mesh


# Every AiMesh entity is read from the topology of the router
_MESH: dict[str, Any] = {
    "source": ARAiMeshSourceUniversal,
    "update_interval": TOPOLOGY_INTERVAL,
    "supported_fn": _serves_mesh,
}
_NODE: dict[str, Any] = {
    **_MESH,
    "node_source": lambda _: ARAiMeshSourceUniversal,
    "covers_mesh": True,
}


def _get_wireless(band: ARWiFiBand) -> str:
    """Get the backhaul option of a wireless band."""

    return f"{ARAiMeshMedium.WIRELESS.value}_{band.value}"


# Wireless options carry the band, so a band switch changes the state
_BACKHAUL_OPTIONS = [
    *(
        medium.value
        for medium in ARAiMeshMedium
        if medium not in (ARAiMeshMedium.UNKNOWN, ARAiMeshMedium.WIRELESS)
    ),
    *(
        _get_wireless(band)
        for band in ARWiFiBand
        if band is not ARWiFiBand.UNKNOWN
    ),
]


def _get_aimesh_attributes(topology: ARAiMeshTopology) -> dict[str, Any]:
    """Get the AiMesh attributes of the topology."""

    return {"total": len(topology.nodes)}


def _get_backhaul(node: ARAiMeshNode) -> str | None:
    """Get the backhaul of the node, None when not a known option."""

    backhaul = node.backhaul
    if backhaul is None:
        return None
    if backhaul.medium is not ARAiMeshMedium.WIRELESS:
        value = backhaul.medium.value
    elif backhaul.band is None:
        return None
    else:
        value = _get_wireless(backhaul.band)

    return value if value in _BACKHAUL_OPTIONS else None


def _get_backhaul_attributes(node: ARAiMeshNode) -> dict[str, Any]:
    """Get the backhaul attributes of the node."""

    backhaul = node.backhaul
    parent = None if backhaul is None else backhaul.mac_parent

    return {"parent": None if parent is None else format_mac(str(parent))}


def _get_ip(node: ARAiMeshNode) -> str | None:
    """Get the IP address of the node."""

    return None if node.ip is None else str(node.ip)


def _get_link_rate(node: ARAiMeshNode) -> int | None:
    """Get the backhaul link rate of the node in Mbit/s."""

    backhaul = node.backhaul
    if backhaul is None or backhaul.link_rate is ARPortSpeed.UNKNOWN:
        return None

    return backhaul.link_rate.value


def _get_link_rate_attributes(node: ARAiMeshNode) -> dict[str, Any]:
    """Get the wired backhaul attributes of the node."""

    return {"port": None if node.backhaul is None else node.backhaul.port}


def _get_online(topology: ARAiMeshTopology) -> int:
    """Get the number of online AiMesh devices, the router included."""

    return sum(node.online for node in topology.nodes.values())


def _get_rssi(node: ARAiMeshNode) -> int | None:
    """Get the backhaul signal strength of the node."""

    return None if node.backhaul is None else node.backhaul.rssi


def _has_link_rate(node: ARAiMeshNode) -> bool:
    """Check whether the node is online over a backhaul with a link rate."""

    return node.online and _get_link_rate(node) is not None


def _has_rssi(node: ARAiMeshNode) -> bool:
    """Check whether the node is online over a wireless backhaul."""

    backhaul = node.backhaul
    return (
        node.online
        and backhaul is not None
        and backhaul.medium is ARAiMeshMedium.WIRELESS
    )


def _is_online(node: ARAiMeshNode) -> bool:
    """Check whether the node is online."""

    return node.online


BINARY_SENSORS: tuple[ARBinarySensorDescription, ...] = (
    ARBinarySensorDescription(
        key="connected",
        translation_key="connected",
        unique_id_name="Connected",
        value_fn=_is_online,
        # The router is online whenever its topology is read
        on_device=False,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        **_NODE,
    ),
)

SENSORS: tuple[ARSensorDescription, ...] = (
    ARSensorDescription(
        key="aimesh",
        translation_key="aimesh",
        unique_id_name="AiMesh",
        data_fn=lambda topology: topology,
        value_fn=_get_online,
        attributes_fn=_get_aimesh_attributes,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_MESH,
    ),
    ARSensorDescription(
        key="backhaul",
        translation_key="backhaul",
        unique_id_name="Backhaul",
        value_fn=_get_backhaul,
        attributes_fn=_get_backhaul_attributes,
        # An offline node has no backhaul
        available_fn=_is_online,
        # The router has no backhaul
        on_device=False,
        device_class=SensorDeviceClass.ENUM,
        options=_BACKHAUL_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        **_NODE,
    ),
    ARSensorDescription(
        key="backhaul_link_rate",
        translation_key="backhaul_link_rate",
        unique_id_name="Backhaul link rate",
        value_fn=_get_link_rate,
        attributes_fn=_get_link_rate_attributes,
        # Only a wired backhaul reports its link rate
        available_fn=_has_link_rate,
        on_device=False,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        **_NODE,
    ),
    ARSensorDescription(
        key="backhaul_rssi",
        translation_key="backhaul_rssi",
        unique_id_name="Backhaul RSSI",
        value_fn=_get_rssi,
        # Only a wireless backhaul reports its signal
        available_fn=_has_rssi,
        on_device=False,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        **_NODE,
    ),
    ARSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        unique_id_name="IP address",
        value_fn=_get_ip,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        **_NODE,
    ),
)
