"""AsusRouter service actions."""

from __future__ import annotations

from ipaddress import IPv4Address
import re
from typing import Any, cast

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry as er,
    target as target_helpers,
)
import voluptuous as vol

from .client import ARClient
from .const import ASUSROUTER, DOMAIN, IP, MAC, ROUTER
from .router import ARDevice

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_DNS = "dns"
ATTR_ENTITIES = "entities"
ATTR_HOSTNAME = "hostname"

SERVICE_REFRESH_STATIC_DHCP_LEASES = "refresh_static_dhcp_leases"
SERVICE_REMOVE_STATIC_DHCP_LEASE = "remove_static_dhcp_lease"
SERVICE_RESERVE_CURRENT_IP = "reserve_current_ip"
SERVICE_SET_STATIC_DHCP_LEASE = "set_static_dhcp_lease"

MAC_ADDRESS = re.compile(
    r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$|^[0-9A-Fa-f]{12}$"
)


def _strip(value: Any) -> str:
    """Return a stripped string."""

    stripped = str(value).strip()
    if not stripped:
        raise vol.Invalid("value is required")
    return stripped


def _mac_address(value: Any) -> str:
    """Validate a MAC address."""

    normalized = _strip(value)
    if not MAC_ADDRESS.match(normalized):
        raise vol.Invalid("expected MAC address")
    return normalized


def _ipv4_address(value: Any) -> str:
    """Validate an IPv4 address."""

    value = _strip(value)
    try:
        return str(IPv4Address(value))
    except ValueError as ex:
        raise vol.Invalid("expected IPv4 address") from ex


def _optional_string(value: Any) -> str:
    """Return an optional stripped string."""

    if value is None:
        return ""
    return str(value).strip()


def _optional_ipv4_address(value: Any) -> str:
    """Validate an optional IPv4 address."""

    value = _optional_string(value)
    if not value:
        return ""
    return _ipv4_address(value)


def _entity_ids(value: Any) -> list[str]:
    """Normalize one or more entity IDs."""

    return cv.entity_ids(value)


def _reserve_schema(value: dict[str, Any]) -> dict[str, Any]:
    """Validate reserve_current_ip fields."""

    if not any(
        field in value
        for field in (
            ATTR_ENTITY_ID,
            "device_id",
            "area_id",
            "floor_id",
            "label_id",
            ATTR_ENTITIES,
        )
    ):
        raise vol.Invalid("target is required")
    return value


SET_STATIC_DHCP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(MAC): _mac_address,
        vol.Required(IP): _ipv4_address,
        vol.Optional(ATTR_HOSTNAME): _optional_string,
        vol.Optional(ATTR_DNS): _optional_ipv4_address,
    }
)

REMOVE_STATIC_DHCP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(MAC): _mac_address,
    }
)

REFRESH_STATIC_DHCP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)

RESERVE_CURRENT_IP_SCHEMA = vol.Schema(
    vol.All(
        {
            **cv.TARGET_SERVICE_FIELDS,
            vol.Optional(ATTR_ENTITIES): _entity_ids,
        },
        _reserve_schema,
    )
)


def _get_router(hass: HomeAssistant, config_entry_id: str) -> ARDevice:
    """Get a loaded AsusRouter instance by config entry ID."""

    router_data = hass.data.get(DOMAIN, {}).get(config_entry_id)
    if not router_data or ASUSROUTER not in router_data:
        raise HomeAssistantError(
            f"AsusRouter config entry is not loaded: {config_entry_id}"
        )

    router: ARDevice = router_data[ASUSROUTER]
    return router


def _require_router_mode(router: ARDevice) -> None:
    """Require a router-mode entry."""

    if router.mode != ROUTER:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="static_dhcp_router_mode_required",
        )


def _get_entity_ids(hass: HomeAssistant, call: ServiceCall) -> list[str]:
    """Return service target entity IDs."""

    selected = target_helpers.async_extract_referenced_entity_ids(
        hass,
        target_helpers.TargetSelection(call.data),
    )
    entity_ids = set(selected.referenced)
    registry = er.async_get(hass)
    entity_ids.update(
        entity_id
        for entity_id in selected.indirectly_referenced
        if (entry := registry.async_get(entity_id)) is not None
        and entry.domain == "device_tracker"
        and entry.platform == DOMAIN
    )

    legacy_entities = call.data.get(ATTR_ENTITIES, [])
    entity_ids.update(legacy_entities)

    return sorted(entity_ids)


def _get_client_field(
    router: ARDevice,
    mac: str,
    field: str,
) -> str | None:
    """Get a field from the router client cache."""

    client = cast(
        ARClient | None, router.devices.get(router._static_dhcp_mac(mac))
    )
    if client is None:
        return None

    match field:
        case "ip":
            return client.ip_address
        case "name":
            return client.name
        case _:
            return None


def _client_entity_data(
    hass: HomeAssistant,
    entity_id: str,
) -> tuple[ARDevice, str, str, str | None]:
    """Get router, MAC, current IP, and hostname from a device tracker."""

    registry = er.async_get(hass)
    entry = registry.async_get(entity_id)
    if entry is None:
        raise ServiceValidationError(f"Entity not found: {entity_id}")
    if entry.config_entry_id is None:
        raise ServiceValidationError(
            f"Entity is not tied to a config entry: {entity_id}"
        )

    router = _get_router(hass, entry.config_entry_id)
    _require_router_mode(router)

    capabilities = entry.capabilities or {}
    mac = capabilities.get(MAC)
    if mac is None:
        state = hass.states.get(entity_id)
        mac = state.attributes.get(MAC) if state is not None else None
    if mac is None:
        raise ServiceValidationError(
            f"Device tracker has no MAC address: {entity_id}"
        )

    state = hass.states.get(entity_id)
    ip = _get_client_field(router, mac, "ip")
    if ip is None and state is not None:
        ip = state.attributes.get(IP) or state.attributes.get("ip_address")
    if ip is None:
        raise ServiceValidationError(
            f"Device tracker has no current IP address: {entity_id}"
        )

    hostname = _get_client_field(router, mac, "name")
    if hostname is None:
        hostname = capabilities.get("name")
    if hostname is None and state is not None:
        hostname = state.attributes.get("host_name") or state.attributes.get(
            "friendly_name"
        )

    return router, mac, ip, hostname


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up AsusRouter service actions."""

    async def async_set_static_dhcp_lease(call: ServiceCall) -> None:
        """Set a static DHCP lease."""

        router = _get_router(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        _require_router_mode(router)
        await router.async_set_static_dhcp_lease(
            mac=call.data[MAC],
            ip=call.data[IP],
            hostname=call.data.get(ATTR_HOSTNAME),
            dns=call.data.get(ATTR_DNS),
        )

    async def async_remove_static_dhcp_lease(call: ServiceCall) -> None:
        """Remove a static DHCP lease."""

        router = _get_router(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        _require_router_mode(router)
        await router.async_remove_static_dhcp_lease(call.data[MAC])

    async def async_reserve_current_ip(call: ServiceCall) -> None:
        """Reserve the current IP for one or more device trackers."""

        for entity_id in _get_entity_ids(hass, call):
            router, mac, ip, hostname = _client_entity_data(hass, entity_id)
            await router.async_reserve_current_ip(
                mac=mac,
                ip=ip,
                hostname=hostname,
            )

    async def async_refresh_static_dhcp_leases(call: ServiceCall) -> None:
        """Refresh static DHCP leases."""

        router = _get_router(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        _require_router_mode(router)
        await router.async_refresh_static_dhcp_leases()

    if hass.services.has_service(DOMAIN, SERVICE_SET_STATIC_DHCP_LEASE):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STATIC_DHCP_LEASE,
        async_set_static_dhcp_lease,
        schema=SET_STATIC_DHCP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_STATIC_DHCP_LEASE,
        async_remove_static_dhcp_lease,
        schema=REMOVE_STATIC_DHCP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESERVE_CURRENT_IP,
        async_reserve_current_ip,
        schema=RESERVE_CURRENT_IP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_STATIC_DHCP_LEASES,
        async_refresh_static_dhcp_leases,
        schema=REFRESH_STATIC_DHCP_SCHEMA,
    )
