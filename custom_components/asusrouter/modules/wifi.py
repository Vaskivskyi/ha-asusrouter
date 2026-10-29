"""AsusRouter WiFi module."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from asusrouter.modules.wifi import (
    ARWiFiAction,
    ARWiFiBand,
    ARWiFiBandwidth,
    ARWiFiField,
    ARWiFiSourceUniversal,
)
from homeassistant.const import EntityCategory

from ..entity import ARSwitchDescription

if TYPE_CHECKING:
    from ..bridge import ARBridge

UPDATE_INTERVAL = timedelta(seconds=30)

# Label of every band in the unique_id names
_LABELS: dict[ARWiFiBand, str] = {
    ARWiFiBand.BAND_2G1: "2.4 GHz",
    ARWiFiBand.BAND_2G2: "2.4 GHz-2",
    ARWiFiBand.BAND_5G1: "5 GHz",
    ARWiFiBand.BAND_5G2: "5 GHz-2",
    ARWiFiBand.BAND_6G1: "6 GHz",
    ARWiFiBand.BAND_6G2: "6 GHz-2",
}


def _get_bandwidth(bandwidth: ARWiFiBandwidth | None) -> int | str | None:
    """Get the channel bandwidth in MHz, `auto` when the radio decides."""

    if bandwidth is None or bandwidth is ARWiFiBandwidth.UNKNOWN:
        return None
    if bandwidth is ARWiFiBandwidth.AUTO:
        return "auto"
    return bandwidth.value


def _get_attributes(radio: dict[ARWiFiField, Any]) -> dict[str, Any]:
    """Get the attributes of a radio."""

    return {
        "channel": radio.get(ARWiFiField.CHANNEL),
        "channel_bandwidth": _get_bandwidth(radio.get(ARWiFiField.BANDWIDTH)),
        "chanspec": radio.get(ARWiFiField.CHANNEL_SPEC),
        "country_code": radio.get(ARWiFiField.COUNTRY),
    }


def _get_radio_switch(band: ARWiFiBand, label: str) -> ARSwitchDescription:
    """Get the description of the switch of a radio."""

    def _has_band(bridge: ARBridge) -> bool:
        """Check whether the device has the band."""

        return band in bridge.identity.wifi

    return ARSwitchDescription(
        key=f"wifi_{band.value}",
        translation_key=f"wifi_{band.value}",
        source=ARWiFiSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=f"Wireless {label}",
        # The device reports its radios by band, not keyed by its MAC
        data_fn=lambda data: (
            data.get(band) if isinstance(data, dict) else None
        ),
        value_fn=lambda radio: radio.get(ARWiFiField.STATE),
        attributes_fn=_get_attributes,
        action_fn=lambda state, _: ARWiFiAction(band, state),
        supported_fn=_has_band,
        entity_category=EntityCategory.CONFIG,
    )


SWITCHES: tuple[ARSwitchDescription, ...] = tuple(
    _get_radio_switch(band, label) for band, label in _LABELS.items()
)
