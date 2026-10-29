"""Tests for the service module."""

from __future__ import annotations

from asusrouter.modules.common.command import ARService
from asusrouter.modules.service import ARServiceAction
from asusrouter.modules.system_status import ARSystemStatusSourceUniversal
import pytest

from custom_components.asusrouter.modules.service import BUTTONS

DESCRIPTIONS = {description.key: description for description in BUTTONS}


@pytest.mark.parametrize(
    ("key", "unique_id_name", "service", "enabled"),
    [
        ("reboot", "Reboot", ARService.REBOOT, True),
        (
            "restart_firewall",
            "Restart firewall",
            ARService.FIREWALL_RESTART,
            False,
        ),
        (
            "restart_httpd",
            "Restart HTTP daemon",
            ARService.WEBUI_RESTART,
            False,
        ),
        ("restart_wired", "Restart wired", ARService.NETWORK_RESTART, True),
        (
            "restart_wireless",
            "Restart wireless",
            ARService.WIRELESS_RESTART,
            False,
        ),
    ],
)
def test_button(
    key: str, unique_id_name: str, service: ARService, enabled: bool
) -> None:
    """Test that every button keeps its unique_id and runs its service."""

    description = DESCRIPTIONS[key]
    action = description.action_fn()

    assert description.unique_id_name == unique_id_name
    assert isinstance(action, ARServiceAction)
    assert action.services == [service]
    assert description.entity_registry_enabled_default is enabled
    assert description.source is ARSystemStatusSourceUniversal
    # Only the router runs its services
    assert description.node_source is None
