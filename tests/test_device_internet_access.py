"""Tests for device internet-access control."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

from asusrouter.modules.parental_control import ParentalControlRule, PCRuleType
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import pytest
import voluptuous as vol

from custom_components.asusrouter.bridge import ARBridge
from custom_components.asusrouter.const import ASUSROUTER, DOMAIN, ROUTER
from custom_components.asusrouter.services import (
    DEVICE_INTERNET_ACCESS_SCHEMA,
    SERVICE_DEVICE_INTERNET_ACCESS,
    _reload_parental_control_switches,
    async_setup_services,
)


def _bridge(*results: bool) -> ARBridge:
    """Create a bridge shell with mocked router writes."""

    bridge = ARBridge.__new__(ARBridge)
    bridge._api = Mock()
    bridge.api.async_set_state = AsyncMock(side_effect=results)
    return bridge


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state", "rule_type"),
    [
        ("allow", PCRuleType.DISABLE),
        ("block", PCRuleType.BLOCK),
        ("remove", PCRuleType.REMOVE),
    ],
)
async def test_pc_rule_maps_state_and_normalizes_mac(
    state: str,
    rule_type: PCRuleType,
) -> None:
    """Each public state should produce the matching router rule."""

    bridge = _bridge(True)

    assert await bridge.async_pc_rule(
        state=state,
        devices=[{"mac": "aa:bb:cc:dd:ee:ff", "name": "Console"}],
    )

    rule = bridge.api.async_set_state.await_args.args[0]
    assert rule.mac == "AA:BB:CC:DD:EE:FF"
    assert rule.name == "Console"
    assert rule.type == rule_type


@pytest.mark.asyncio
async def test_pc_rule_rejects_empty_targets() -> None:
    """An empty action must not report success."""

    bridge = _bridge()

    assert not await bridge.async_pc_rule(state="block", devices=[])
    bridge.api.async_set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_pc_rule_reports_partial_router_failure() -> None:
    """Any failed router write should fail the whole action."""

    bridge = _bridge(True, False)

    assert not await bridge.async_pc_rule(
        state="block",
        devices=[
            {"mac": "00:11:22:33:44:55"},
            {"mac": "AA:BB:CC:DD:EE:FF"},
        ],
    )


def test_service_schema_requires_target() -> None:
    """The action should reject calls that cannot identify a device."""

    with pytest.raises(vol.MultipleInvalid, match="target is required"):
        DEVICE_INTERNET_ACCESS_SCHEMA({"state": "block"})


def _service_hass(router: Mock) -> tuple[Mock, dict[str, object]]:
    """Create a Home Assistant shell and capture service handlers."""

    handlers: dict[str, object] = {}
    hass = Mock()
    hass.data = {DOMAIN: {"router-1": {ASUSROUTER: router}}}
    hass.services.has_service.return_value = False
    hass.services.async_register.side_effect = (
        lambda _domain, service, handler, **_kwargs: handlers.__setitem__(
            service, handler
        )
    )
    return hass, handlers


def _router() -> Mock:
    """Create a router-mode service target."""

    router = Mock()
    router.mode = ROUTER
    router.mac = "24:4b:fe:f5:ee:20"
    router.pc_rules = {}
    router._static_dhcp_mac.side_effect = lambda mac: str(mac).lower()

    async def apply_rule(*, state: str, devices: list[dict[str, str]]) -> bool:
        for device in devices:
            mac = str(device["mac"]).lower()
            if state == "remove":
                router.pc_rules.pop(mac, None)
                continue
            router.pc_rules[mac] = ParentalControlRule(
                mac=mac,
                name=device.get("name", ""),
                type={
                    "allow": PCRuleType.DISABLE,
                    "block": PCRuleType.BLOCK,
                }[state],
            )
        return True

    router.bridge.async_pc_rule = AsyncMock(side_effect=apply_rule)
    router.update_pc_rules = AsyncMock(return_value=True)
    return router


@pytest.mark.asyncio
async def test_service_routes_direct_devices_to_only_router() -> None:
    """A direct MAC target should safely resolve the only loaded router."""

    router = _router()
    hass, handlers = _service_hass(router)
    await async_setup_services(hass)
    handler = handlers[SERVICE_DEVICE_INTERNET_ACCESS]
    call = Mock(
        data={
            "devices": [{"mac": "AA:BB:CC:DD:EE:FF", "name": "Console"}],
            "state": "block",
        }
    )

    with patch(
        "custom_components.asusrouter.services._get_entity_ids",
        return_value=[],
    ):
        await handler(call)

    router.bridge.async_pc_rule.assert_awaited_once_with(
        state="block",
        devices=[{"mac": "AA:BB:CC:DD:EE:FF", "name": "Console"}],
    )
    router.update_pc_rules.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_routes_entity_target_to_own_router() -> None:
    """The GUI entity target should select its owning router."""

    router = _router()
    hass, handlers = _service_hass(router)
    await async_setup_services(hass)
    handler = handlers[SERVICE_DEVICE_INTERNET_ACCESS]
    device = {"mac": "AA:BB:CC:DD:EE:FF", "name": "Console"}
    call = Mock(
        data={
            "entity_id": ["device_tracker.console"],
            "state": "allow",
        }
    )

    with (
        patch(
            "custom_components.asusrouter.services._get_entity_ids",
            return_value=["device_tracker.console"],
        ),
        patch(
            "custom_components.asusrouter.services."
            "_internet_access_entity_data",
            return_value=(router, device),
        ),
    ):
        await handler(call)

    router.bridge.async_pc_rule.assert_awaited_once_with(
        state="allow",
        devices=[device],
    )


@pytest.mark.asyncio
async def test_direct_devices_require_router_for_multiple_entries() -> None:
    """Direct MAC targets must not be sent through an arbitrary router."""

    router = _router()
    second_router = _router()
    hass, handlers = _service_hass(router)
    hass.data[DOMAIN]["router-2"] = {ASUSROUTER: second_router}
    await async_setup_services(hass)
    handler = handlers[SERVICE_DEVICE_INTERNET_ACCESS]
    call = Mock(
        data={
            "devices": [{"mac": "AA:BB:CC:DD:EE:FF"}],
            "state": "block",
        }
    )

    with (
        patch(
            "custom_components.asusrouter.services._get_entity_ids",
            return_value=[],
        ),
        pytest.raises(ServiceValidationError, match="config_entry_id"),
    ):
        await handler(call)

    router.bridge.async_pc_rule.assert_not_awaited()
    second_router.bridge.async_pc_rule.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirmed_idempotent_remove_reloads_switches() -> None:
    """An already-removed rule should still clean up switch entities."""

    router = _router()
    router.bridge.async_pc_rule.side_effect = None
    router.bridge.async_pc_rule.return_value = False
    hass, handlers = _service_hass(router)
    await async_setup_services(hass)
    handler = handlers[SERVICE_DEVICE_INTERNET_ACCESS]
    call = Mock(
        data={
            "config_entry_id": "router-1",
            "devices": [{"mac": "AA:BB:CC:DD:EE:FF"}],
            "state": "remove",
        }
    )

    with (
        patch(
            "custom_components.asusrouter.services._get_entity_ids",
            return_value=[],
        ),
        patch(
            "custom_components.asusrouter.services."
            "_reload_parental_control_switches",
            new_callable=AsyncMock,
        ) as reload_switches,
    ):
        await handler(call)

    reload_switches.assert_awaited_once_with(router, call.data["devices"])


@pytest.mark.asyncio
async def test_remove_deletes_matching_switch_registry_entry() -> None:
    """Removing a rule should not leave an unavailable GUI entity."""

    router = _router()
    router._config_entry = Mock(entry_id="router-1")
    router.hass.config_entries.async_unload_platforms = AsyncMock(
        return_value=True
    )
    router.hass.config_entries.async_forward_entry_setups = AsyncMock()
    registry = Mock()
    matching = Mock(
        domain=Platform.SWITCH,
        platform=DOMAIN,
        unique_id=("24:4b:fe:f5:ee:20_aa:bb:cc:dd:ee:ff_block_internet"),
        entity_id="switch.console_block_internet",
    )
    unrelated = Mock(
        domain=Platform.SWITCH,
        platform=DOMAIN,
        unique_id="24:4b:fe:f5:ee:20_block_internet",
        entity_id="switch.router_block_internet",
    )

    with (
        patch(
            "custom_components.asusrouter.services.er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.asusrouter.services.er."
            "async_entries_for_config_entry",
            return_value=[matching, unrelated],
        ),
    ):
        await _reload_parental_control_switches(
            router, [{"mac": "AA:BB:CC:DD:EE:FF"}]
        )

    registry.async_remove.assert_called_once_with(
        "switch.console_block_internet"
    )


@pytest.mark.asyncio
async def test_service_surfaces_unconfirmed_router_write() -> None:
    """A failed router write must become a visible Home Assistant error."""

    router = _router()
    router.bridge.async_pc_rule.side_effect = None
    router.bridge.async_pc_rule.return_value = False
    hass, handlers = _service_hass(router)
    await async_setup_services(hass)
    handler = handlers[SERVICE_DEVICE_INTERNET_ACCESS]
    call = Mock(
        data={
            "config_entry_id": "router-1",
            "devices": [{"mac": "AA:BB:CC:DD:EE:FF"}],
            "state": "block",
        }
    )

    with (
        patch(
            "custom_components.asusrouter.services._get_entity_ids",
            return_value=[],
        ),
        pytest.raises(HomeAssistantError, match="could not be confirmed"),
    ):
        await handler(call)
