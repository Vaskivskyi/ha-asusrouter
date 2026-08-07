# AsusRouter Static DHCP Fork

This is a focused Home Assistant fork of
[Vaskivskyi/ha-asusrouter](https://github.com/Vaskivskyi/ha-asusrouter).
It exists to add reliable fixed-IP management for ASUS routers while keeping
the upstream integration's monitoring and control features.

Current fork release: **v1.0.0-jgassens.1**.

## Problem

The upstream integration can discover and monitor router clients, but it does
not expose ASUS manual DHCP reservations in Home Assistant. Assigning a fixed
IP therefore requires opening the router WebUI and editing each client there.

## Solution

This fork adds static DHCP controls backed by the router's native HTTP(S)
WebUI API. It reads and writes the same **dhcp_staticlist** configuration used
by stock ASUS firmware, enables **dhcp_static_x**, and applies changes with
**restart_dnsmasq**. Router SSH access is not required.

The integration adds:

- A **Static DHCP reservations** sensor with the current reservation count and
  lease list.
- A **Reserve current IP** button on eligible tracked client devices.
- **asusrouter.set_static_dhcp_lease** to create or replace a reservation.
- **asusrouter.remove_static_dhcp_lease** to remove a reservation.
- **asusrouter.reserve_current_ip** to reserve selected clients at their
  currently reported addresses.
- **asusrouter.refresh_static_dhcp_leases** to refresh Home Assistant's cached
  reservation state.

Writes are guarded against duplicate IP assignments and are read back from the
router after apply. Reserving the current IP will not silently move an existing
reservation to a different address.

## Internet Access Action

The existing **asusrouter.device_internet_access** action is retained and
hardened in this release. In the Home Assistant action editor, select one or
more AsusRouter device trackers and choose:

- **block** to enable a parental-control block.
- **allow** to disable the block while retaining the rule.
- **remove** to delete the parental-control rule.

The action now validates its targets, routes each target through its owning
router entry, and raises a visible Home Assistant error when the router does
not accept the write or its state cannot be refreshed. Direct API callers may
also provide **devices** containing **mac** and optional **name**; when more
than one router entry is loaded, they must also provide **config_entry_id**.

## HACS Installation

This fork and the upstream repository use the same Home Assistant integration
domain, so install only one of them.

1. Back up Home Assistant.
2. Remove the official AsusRouter repository from HACS. Do not delete the
   AsusRouter integration configuration or entities.
3. In HACS, open **Custom repositories**.
4. Add **https://github.com/jgassens/ha-asusrouter** as an **Integration**.
5. Download **v1.0.0-jgassens.1** and restart Home Assistant.

Existing AsusRouter config entries and entity IDs remain in place because the
domain is still **asusrouter**.

## Compatibility

- Home Assistant **2026.7.4** or newer for this release.
- Stock AsusWRT **3.0.0.4.x** and **3.0.0.6.x**: expected and primary target.
  Static DHCP was validated through the stock-compatible HTTP(S) WebUI path;
  it does not depend on Merlin-only SSH commands.
- AsusWRT-Merlin: expected to work where the upstream integration works,
  because it exposes the same WebUI fields and apply action.
- Asus firmware **5.x.x**: not supported, matching the upstream integration.

Router models and firmware vary. Make a router configuration backup before the
first write and verify the resulting reservation in the ASUS WebUI.

## Upstream And Maintenance

The fork is periodically rebased onto the current upstream **dev** branch. The
static DHCP implementation depends on the companion
[jgassens/asusrouter](https://github.com/jgassens/asusrouter) library fork,
pinned to a tested commit in **manifest.json**.

General AsusRouter behavior and device support come from the upstream project.
Fork-specific DHCP or release issues belong in
[jgassens/ha-asusrouter issues](https://github.com/jgassens/ha-asusrouter/issues).

## Development

Run the test suite and lint checks before publishing:

    uv run pytest
    uv run ruff check custom_components/asusrouter tests
    uv run ruff format --check custom_components/asusrouter tests

This project remains licensed under Apache-2.0. Upstream authorship and history
are preserved in Git.
