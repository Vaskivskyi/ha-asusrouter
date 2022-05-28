[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](https://github.com/Vaskivskyi/ha-asusrouter/blob/main/LICENSE) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=blue)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111)

## AsusRouter - Monitor and control your Asus router from Home Assistant

The integration uses the native Asus HTTP(S) API - the same way the web panel or mobile app works and relies on direct communications with your device.

## Features

AsusRouters provides a wide range of sensors and controls for advanced device monitoring and control. The list includes, but is not limited to:

### Monitoring

#### Binary sensors and Sensors

- Traffic and speed sensors for user-selected network interfaces, including WAN, USB, LAN, WLAN and more
- CPU, RAM usage
- WAN and LAN status
- Boot time sensor
- Connected devices sensor

#### Device trackers

### Control

#### Lights

- LED state (`on`/`off`) can be controlled for the devices that support the feature

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

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;"></a>


