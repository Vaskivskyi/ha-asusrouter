[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](LICENSE) [![HACS Default](https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge)](https://hacs.xyz)

## AsusRouter - a custom Home Assistant integration

AsusRouter is a custom integration for Home Assistant to monitor and control your Asus router using [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

Please note, that this integration is in the early development stage and may contain some errors. You could always help with its development by providing your feedback.


## Installation

#### HACS

You can add this repository in your HACS:
`HACS -> Integrations -> Explore & Download Repositories -> AsusRouter`

#### Manual

Copy content of `custom_components/asusrouter/` to `custom_components/asusrouter/` in your Home Assistant folder.


## Usage

After AsusRouter is installed, you can add your device from Home Assistant UI.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=asusrouter)

#### Sensors

Integration provides several types of sensors:

- WAN traffic and speed sensors (enabled by default):
  - `wan_download` / `wan_upload` [^traffic]
    units: `GB` [^units]
    attributes:
    - `Bytes` - raw data from device
  - `wan_download_speed` / `wan_upload_speed`
    units: `Mb/s`
    attributes:
    - `Bits/s` - raw data from device
- Secondary (USB) WAN (if dual-WAN is supported by the device) traffic and speed sensors (disabled):
  - `usb_download` / `usb_upload` / `usb_download_speed` / `usb_upload_speed`
- CPU usage sensor (disabled): `cpu`
  units: `%`
- RAM usage sensor (disabled): `ram`
  units: `%`
  attributes (all in `KB`, as device reports):
  - `Total`
  - `Free`
  - `Used`
- Connected devices sensor (enabled): `connected_devices`
- Boot time sensor (disabled): `boot_time`

[^traffic]: Asus routers calculate traffic as an 8-digit HEX, so it overflows each 4 294 967 296 bytes (4 GB). One can either use [Long-term statistics](#long-term-statistics) or create a [`utility_meter`](https://www.home-assistant.io/integrations/utility_meter/) for more control and the possibility to monitor traffic above the limitation.
[^units]: The integration uses 2^10 conversion factors in calculations - the same way as native Asus software. If you would like to use 10^3 factors, all the sensors provide raw data in bytes or bits/s.

#### Device trackers

Device trackers are disabled by default if HA doesn't know the device. The generated `device_tracker.device_name` entities include `device_name` as reported by AsusRouter library according to the priority list:
- Friendly name of the device (if set in the router admin panel)
- Name as reported by the connected device
- MAC address if neither of the above is known

Attributes:
- IP address
- MAC
- Hostname (name of the connected device as stated before)
- Last time reachable
- Connection time (for WiFi devices only)

**Important**

If the connected device MAC address is known to Home Assistant (e.g. it was set up by another integration `ABC`), its `device_tracker` will be added to that device in enabled state. Moreover, this device will be showing for both integrations: `AsusRouter` and `ABC`

#### Long-term statistics

The long-term statistics is supported for all the sensors, but `boot_time`.


## More features

#### Secondary WAN (USB)

If your device supports the dual-WAN feature, the [corresponding sensors](#sensors) will be created. They will be showing the correct values when USB WAN is connected and `unknown`, when a phone / USB modem is disconnected.

This is expected behaviour and should be handled by integration automatically (without the need for a user to restart the integration).

#### Reboot handle

Integration does support automatic handling of the device reboots. Most of the routers reboot in approximately 1-1.5 min. After that time, a new connection will be done automatically.

There will be an error in your log in this case.

If you are experiencing multiple errors in your log (more than 5 in a row) or integration does not provide any data 5 minutes after a reboot, please report it to the Issues. The more data you provide, the easier it will be to fix the problem.


## Support the integration

### Issues and Pull requests

If you have found an issue working with the integration or just want to ask for a new feature, please fill in a new [issue](https://github.com/Vaskivskyi/ha-asusrouter/issues).

You are also welcome to submit [pull requests](https://github.com/Vaskivskyi/ha-asusrouter/pulls) to the repository!

### Check it with your device

Testing the integration with different devices would help a lot in the development process. Unfortunately, currently, I have only one device available, so your help would be much appreciated.

### Other support

This integration is a free-time project. If you like it, you can support me by buying a coffee.

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;"></a>


## Thanks to

The initial codebase for this integration is highly based on Home Assistant core integration [AsusWRT](https://www.home-assistant.io/integrations/asuswrt/) and [ollo69/ha_asuswrt_custom](https://github.com/ollo69/ha_asuswrt_custom).

