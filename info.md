[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](https://github.com/Vaskivskyi/ha-asusrouter/blob/main/LICENSE) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=blue)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111) [![Installations](https://img.shields.io/endpoint?url=https://vaskivskyi.github.io/ha-custom-analytics/badges/asusrouter/total.json&style=for-the-badge&color=yellow)](https://github.com/Vaskivskyi/ha-custom-analytics)

## Monitor and control your AsusWRT-powered router from Home Assistant

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device. Both the stock AsusWRT as well as AsusWRT-Merlin are supported.

## Monitoring

#### Binary sensors and Sensors

- Boot time
- Connected devices
- CPU and RAM usage
- Load average sensors (FW: **Merlin-only**)
- Network traffic and speed
- OpenVPN clients
- Ports (LAN/WAN) connection
- Temperatures
- WAN IP and status
- WiFi networks status

#### Device trackers

## Control

All the following entities require `Device control` to be enabled in the integration settings. Some of the entities may not be available for your device because of their firmware limitation.

#### Lights

- LED (`on`/`off`)

#### Switches

- OpenVPN clients (`on`/`off`)
- WiFi networks (`on`/`off`)

Please, refer to the GitHub [Readme](https://github.com/Vaskivskyi/ha-asusrouter/) for detailed information on the available sensors and controls.

## Installation

1. Click Install
2. Restart Home Assistant
3. In the Home Assistant UI:
   `Configuration -> Devices & Services -> Integrations -> Add integration -> AsusRouter`

## Configuration

You would need to provide the minimum information:
- Hostname or IP address of the device
- Username
- Password

Please, refer to the GitHub [Setup documentation](https://github.com/Vaskivskyi/ha-asusrouter/blob/main/docs/setup.md) if you would like to get detailed information on the configuration flow.

---

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;"></a>


