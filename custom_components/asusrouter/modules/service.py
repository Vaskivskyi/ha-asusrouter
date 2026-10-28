"""AsusRouter service module."""

from __future__ import annotations

from asusrouter.modules.common.command import ARService
from asusrouter.modules.service import ARServiceAction
from asusrouter.modules.system_status import ARSystemStatusSourceUniversal
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.const import EntityCategory

from ..entity import ARButtonDescription
from .system_status import UPDATE_INTERVAL


def _get_service_button(
    key: str,
    unique_id_name: str,
    service: ARService,
    *,
    enabled: bool = False,
    device_class: ButtonDeviceClass | None = None,
) -> ARButtonDescription:
    """Get the description of a button running a device service."""

    return ARButtonDescription(
        key=key,
        translation_key=key,
        # The buttons are available while the device answers
        source=ARSystemStatusSourceUniversal,
        update_interval=UPDATE_INTERVAL,
        unique_id_name=unique_id_name,
        action_fn=lambda: ARServiceAction(service),
        device_class=device_class,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=enabled,
    )


BUTTONS: tuple[ARButtonDescription, ...] = (
    _get_service_button(
        "reboot",
        "Reboot",
        ARService.REBOOT,
        enabled=True,
        device_class=ButtonDeviceClass.RESTART,
    ),
    _get_service_button(
        "restart_firewall", "Restart firewall", ARService.FIREWALL_RESTART
    ),
    _get_service_button(
        "restart_httpd", "Restart HTTP daemon", ARService.WEBUI_RESTART
    ),
    _get_service_button(
        "restart_wired",
        "Restart wired",
        ARService.NETWORK_RESTART,
        enabled=True,
    ),
    _get_service_button(
        "restart_wireless", "Restart wireless", ARService.WIRELESS_RESTART
    ),
)
