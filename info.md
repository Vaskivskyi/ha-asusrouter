[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](https://github.com/Vaskivskyi/ha-asusrouter/blob/main/LICENSE) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=blue)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111) [![Installations](https://img.shields.io/endpoint?url=https://vaskivskyi.github.io/ha-custom-analytics/badges/asusrouter/total.json&style=for-the-badge&color=yellow)](https://github.com/Vaskivskyi/ha-custom-analytics)<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 28px !important;" align="right" /></a>

## Monitor and control your AsusWRT-powered router from Home Assistant

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device. Both the stock AsusWRT as well as AsusWRT-Merlin are supported.

## Full documentation

You can find the full documentation on the [official webpage](https://asusrouter.vaskivskyi.com/).

## :loudspeaker: Do you want to add AsusRouter to the default HA Core integrations?

:+1: Vote for the feature request!

[Add AsusRouter integration to HA Core - Feature Requests - Home Assistant Community (home-assistant.io)](https://community.home-assistant.io/t/add-asusrouter-integration-to-ha-core/515756?u=vaskivskyi)

## Features

AsusRouter supports 14+ groups of features, including monitoring of:
- connected device, CPU, guest WLAN, LED, load average, network, OpenVPN, parental control, ports, RAM, temperature, WAN, WLAN.

and control of:
- gues WLAN, LED, OpenVPN, parental control, WLAN.

 as well as the following HA platrorms:
- `binary_sensor`, `button`, `device_tracker`, `light`, `sensor`, `switch`, `update`

and HA events and services.

[Full list of features](https://asusrouter.vaskivskyi.com/features/)

## Supported devices

AsusRouter supports virtually every AsusWRT-powered device. [The full list of tested devices](https://asusrouter.vaskivskyi.com/devices/).

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

Please, refer to the [Setup documentation](https://asusrouter.vaskivskyi.com/guide/getting-started/) if you would like to get detailed information on the configuration flow.

---

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 60px !important;"></a>


