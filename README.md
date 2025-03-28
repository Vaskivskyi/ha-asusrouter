[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](LICENSE)<a href="https://github.com/Vaskivskyi/ha-asusrouter/actions/workflows/build.yaml"><img src="https://img.shields.io/github/actions/workflow/status/Vaskivskyi/ha-asusrouter/build.yaml?branch=main&style=for-the-badge" alt="Build Status" align="right" /></a><br/>
[![HACS Default](https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge)](https://hacs.xyz) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=yellow)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111)<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 28px !important;" align="right" /></a><br/>
[![Installations](https://img.shields.io/endpoint?url=https://ha-analytics.vaskivskyi.com/badges/asusrouter/total.json&style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-custom-analytics)

<div align=center><img src="https://asusrouter.vaskivskyi.com/logo.svg" width="300px"></div>

## Monitor and control your AsusWRT-powered router from Home Assistant

`AsusRouter` is a custom integration for Home Assistant to monitor and control your AsusWRT (and [AsusWRT-Merlin](https://www.asuswrt-merlin.net/))-powered router using the [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device.

## Documentation and tips

You can find the full documentation on the [official webpage](https://asusrouter.vaskivskyi.com/).

### Use HTTPS connection

It is recommended to use an HTTPS connection to your router (SSL). While both the SSL and non-SSL connections are fully supported, some devices might have issues with disconnects on HTTP. In order to use SSL, you need to enable it in the router settings: `Administration -> System -> Local Access Config -> Authentication Method`. Put it to `BOTH` (recommended) or `HTTPS`. Make note of the port number (default is `8443`).

### Connected devices number

The integration might show a different number of connected devices compared to the WebUI network map. In this case, refer to the number of devices shown in the `AiMesh` section of the WebUI. Those two are different regardless of the actual use of AiMesh.

## :loudspeaker: Do you want to add AsusRouter to the default HA Core integrations?

:+1: Vote for the feature request!

[Add AsusRouter integration to HA Core - Feature Requests - Home Assistant Community (home-assistant.io)](https://community.home-assistant.io/t/add-asusrouter-integration-to-ha-core/515756?u=vaskivskyi)

## Firmware limitations

Firmware versions `3.0.0.4.x` and `3.0.0.6.x` are fully supported (older versions might have a limited amount of sensors available). When talking about the FW, `3.0.0.4` might be missed since it is the same all the time. Important is only the last part, e.g. `386.48631` or `102.xxxxx` for the stock or `386.7` for Merlin FW.

Firmware `5.x.x` (some DSL models) is **NOT supported** (not AsusWRT).

[More about firmware versions](https://asusrouter.vaskivskyi.com/guide/faq/#firmware)

## Installation

#### HACS

You can add this repository to your HACS:
`HACS -> Integrations -> Explore & Download Repositories -> AsusRouter`

#### Manual

Copy content of the [stable branch](https://github.com/Vaskivskyi/ha-asusrouter/tree/stable) `custom_components/asusrouter/` to `custom_components/asusrouter/` in your Home Assistant folder.

## Usage

After AsusRouter is installed, you can add your device from Home Assistant UI.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=asusrouter)

To connect to the device you need to provide the following data:

- IP address or hostname
- Username (the one you use to log into the WebUI)
- Password
- Whether to use an SSL connection

Almost all the integration settings can be reconfigured later via the `Configure` button on the Integrations' page without the need to remove your device and add it again.

[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

## Features

AsusRouter supports 14+ groups of features, including monitoring of:

- connected device, CPU, guest WLAN, LED, Aura RGB, load average, network, OpenVPN, parental control, ports, RAM, temperature, WAN, WLAN.

and control of:

- guest WLAN, LED, Aura RGB, OpenVPN, parental control, WLAN.

as well as the following HA platforms:

- `binary_sensor`, `button`, `device_tracker`, `light`, `sensor`, `switch`, `update`

and HA events and services.

[Full list of features](https://asusrouter.vaskivskyi.com/features/)

## Supported devices

AsusRouter supports virtually every AsusWRT-powered device. This list is purely based on the reports from the users. Other devices with the compatible firmware should work as well.

### WiFi 7 | 802.11be

| Model                                                                           | Status              | Tested firmware            | Find it on Amazon[^amazon]                                                             |
| ------------------------------------------------------------------------------- | ------------------- | -------------------------- | -------------------------------------------------------------------------------------- |
| [GT-BE19000](https://asusrouter.vaskivskyi.com/devices/GT-BE19000.md)           | 💛 Expected to work |                            | <a href="https://amzn.to/3yGFU7U" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-BE98](https://asusrouter.vaskivskyi.com/devices/GT-BE98.md)                 | 💚 Confirmed        | Stock:<li>`102_34372`</li> | <a href="https://amzn.to/3vGztgz" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-BE98 Pro](https://asusrouter.vaskivskyi.com/devices/GT-BE98Pro.md)          | 💛 Expected to work |                            | <a href="https://amzn.to/3uoSjeR" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-BE58U](https://asusrouter.vaskivskyi.com/devices/RT-BE58U.md)               | 💛 Expected to work |                            | <a href="https://amzn.to/4bHsdo4" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-BE88U](https://asusrouter.vaskivskyi.com/devices/RT-BE88U.md)               | 💛 Expected to work |                            | <a href="https://amzn.to/3TAGCKY" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-BE92U](https://asusrouter.vaskivskyi.com/devices/RT-BE92U.md)               | 💛 Expected to work |                            | <a href="https://amzn.to/4c1E8gg" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-BE96U](https://asusrouter.vaskivskyi.com/devices/RT-BE96U.md)               | 💛 Expected to work |                            | <a href="https://amzn.to/3vJu8oD" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-BE3600](https://asusrouter.vaskivskyi.com/devices/TUF-BE3600.md)           | 💛 Expected to work |                            | <a href="https://amzn.to/3VhHoyt" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-BE6500](https://asusrouter.vaskivskyi.com/devices/TUF-BE6500.md)           | 💛 Expected to work |                            | <a href="https://amzn.to/3X3Xltv" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi BD4](https://asusrouter.vaskivskyi.com/devices/ZenWiFiBD4.md)          | 💛 Expected to work |                            | <a href="https://amzn.to/3Kfulr1" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi BQ16](https://asusrouter.vaskivskyi.com/devices/ZenWiFiBQ16.md)        | 💛 Expected to work |                            | <a href="https://amzn.to/4bgVvdo" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi BQ16 Pro](https://asusrouter.vaskivskyi.com/devices/ZenWiFiBQ16Pro.md) | 💛 Expected to work |                            | <a href="https://amzn.to/3MNcw48" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi BT10](https://asusrouter.vaskivskyi.com/devices/ZenWiFiBT10.md)        | 💛 Expected to work |                            | <a href="https://amzn.to/48F5wiB" rel="nofollow sponsored" target="_blank">find it</a> |

### WiFi 6e | 802.11axe

| Model                                                                           | Status              | Tested firmware                                                                   | Find it on Amazon[^amazon]                                                             |
| ------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [GT-AXE11000](https://asusrouter.vaskivskyi.com/devices/GT-AXE11000.md)         | 💛 Expected to work |                                                                                   | <a href="https://amzn.to/3Gotj9R" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-AXE16000](https://asusrouter.vaskivskyi.com/devices/GT-AXE16000.md)         | 💚 Confirmed        | Stock:<li>`388.21617`</li>Merlin:<li>`388.7_beta1_rog`</li><li>`388.7_0_rog`</li> | <a href="https://amzn.to/3vObLyZ" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AXE7800](https://asusrouter.vaskivskyi.com/devices/RT-AXE7800.md)           | 💚 Confirmed        | Stock:<li>`388_22068`</li>                                                        | <a href="https://amzn.to/3jUr2LU" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi ET8](https://asusrouter.vaskivskyi.com/devices/ZenWiFiET8.md)          | 💚 Confirmed        | Stock:<li>`388.23759`</li>                                                        | <a href="https://amzn.to/3Iks0La" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi ET9](https://asusrouter.vaskivskyi.com/devices/ZenWiFiET9.md)          | 💛 Expected to work |                                                                                   | <a href="https://amzn.to/3RbMKJa" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi Pro ET12](https://asusrouter.vaskivskyi.com/devices/ZenWiFiProET12.md) | 💚 Confirmed        | Stock:<li>`388.23013`</li>                                                        | <a href="https://amzn.to/3GTz68P" rel="nofollow sponsored" target="_blank">find it</a> |

### WiFi 6 | 802.11ax

| Model                                                                                          | Status              | Tested firmware                                                                                                                                                                       | Find it on Amazon[^amazon]                                                             |
| ---------------------------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [DSL-AX82U](https://asusrouter.vaskivskyi.com/devices/DSL-AX82U.md)                            | 💚 Confirmed        | Merlin:<li>`386.07_0-gnuton0_beta2`</li>                                                                                                                                              | <a href="https://amzn.to/3G87vyR" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-AX11000](https://asusrouter.vaskivskyi.com/devices/GT-AX11000.md)                          | 💚 Confirmed        | Merlin:<li>`386.7_2`</li><li>`388.1_0`</li><li>`388.4_0`</li><li>`388.7_0_rog`</li>                                                                                                   | <a href="https://amzn.to/3WDzOMT" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-AX11000 Pro](https://asusrouter.vaskivskyi.com/devices/GT-AX11000Pro.md)                   | 💚 Confirmed        | Stock:<li>`388.24198`</li>Merlin:<li>`388.7_0_rog`</li>                                                                                                                               | <a href="https://amzn.to/3VUNbHl" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT-AX6000](https://asusrouter.vaskivskyi.com/devices/GT-AX6000.md)                            | 💛 Expected to work | Merlin:<li>`388.7_beta1`</li>                                                                                                                                                         | <a href="https://amzn.to/3GrKHKG" rel="nofollow sponsored" target="_blank">find it</a> |
| [GT6](https://asusrouter.vaskivskyi.com/devices/GT6.md)                                        | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3GmPCfR" rel="nofollow sponsored" target="_blank">find it</a> |
| [RP-AX56](https://asusrouter.vaskivskyi.com/devices/RP-AX56.md)                                | 💚 Confirmed        |                                                                                                                                                                                       | <a href="https://amzn.to/3MpZSY8" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX3000P](https://asusrouter.vaskivskyi.com/devices/RT-AX3000P.md)                          | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3RPa2UO" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX52](https://asusrouter.vaskivskyi.com/devices/RT-AX52.md)                                | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/40Ph3sO" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX53U](https://asusrouter.vaskivskyi.com/devices/RT-AX53U.md)                              | 💚 Confirmed        | Stock:<li>`386.69061`</li>                                                                                                                                                            | <a href="https://amzn.to/49jEgqO" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX5400](https://asusrouter.vaskivskyi.com/devices/RT-AX5400.md)                            | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/4aCdvyu" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX55](https://asusrouter.vaskivskyi.com/devices/RT-AX55.md)                                | 💚 Confirmed        | Stock:<li>`386.50410`</li><li>`386.52041`</li>                                                                                                                                        | <a href="https://amzn.to/3Z2ath5" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX56U](https://asusrouter.vaskivskyi.com/devices/RT-AX56U.md)                              | 💚 Confirmed        | Merlin:<li>`386.7_2`</li><li>`388.1_0`</li><li>`388.2_2`</li>                                                                                                                         | <a href="https://amzn.to/3vrIeuz" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX57](https://asusrouter.vaskivskyi.com/devices/RT-AX57.md)                                | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3IWnZNx" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX57 Go](https://asusrouter.vaskivskyi.com/devices/RT-AX57Go.md)                           | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/47kE9db" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX57M](https://asusrouter.vaskivskyi.com/devices/RT-AX57M.md)                              | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3vbVl6k" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX58U](https://asusrouter.vaskivskyi.com/devices/RT-AX58U.md)                              | 💚 Confirmed        | Stock:<li>`386.49674`</li><li>`388.22237`</li>Merlin:<li>`386.7_2`</li><li>`388.1_0`</li><li>`388.4_0`</li><li>`388.7.0`</li>                                                         | <a href="https://amzn.to/3jHri0L" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX59U](https://asusrouter.vaskivskyi.com/devices/RT-AX59U.md)                              | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3CVCVYO" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX68U](https://asusrouter.vaskivskyi.com/devices/RT-AX68U.md)                              | 💚 Confirmed        | Stock:<li>`388.21732`</li>                                                                                                                                                            | <a href="https://amzn.to/3WzRwk5" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX82U](https://asusrouter.vaskivskyi.com/devices/RT-AX82U.md)                              | 💚 Confirmed        | Stock:<li>`386.48664`</li><li>`386.49674`</li>Merlin:<li>`388.8_4-gnuton1`</li>                                                                                                       | <a href="https://amzn.to/3Gv2Bxi" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX86S](https://asusrouter.vaskivskyi.com/devices/RT-AX86S.md)                              | 💚 Confirmed        | Stock:<li>`386.46061`</li><li>`386.48260`</li><li>`386.49447`</li><li>`388.22525`</li>Merlin:<li>`386.7_2`</li>                                                                       | <a href="https://amzn.to/3GuKac5" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX86U](https://asusrouter.vaskivskyi.com/devices/RT-AX86U.md)                              | 💚 Confirmed        | Stock:<li>`386.46061`</li><li>`386.48260`</li><li>`386.49447`</li><li>`388.22525`</li>Merlin:<li>`386.7_2`</li><li>`388.4_0`</li><li>`388.7_beta1`</li>                               | <a href="https://amzn.to/3WCBcPO" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX86U Pro](https://asusrouter.vaskivskyi.com/devices/RT-AX86UPro.md)                       | 💚 Confirmed        | Stock:<li>`388.23565`</li>                                                                                                                                                            | <a href="https://amzn.to/3ZDM41T" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX88U](https://asusrouter.vaskivskyi.com/devices/RT-AX88U.md)                              | 💚 Confirmed        | Stock:<li>`386.45934`</li><li>`386.48631`</li><li>`388.24198`</li>Merlin:<li>`386.5_2`</li><li>`386.8_0`</li><li>`388.1_0`</li><li>`388.2_0`</li><li>`388.4_0`</li><li>`388.7_0`</li> | <a href="https://amzn.to/3i2VfYu" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX88U Pro](https://asusrouter.vaskivskyi.com/devices/RT-AX88UPro.md)                       | 💚 Confirmed        | Merlin:<li>`388.4_0`</li>                                                                                                                                                             | <a href="https://amzn.to/3QNDpFZ" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX89X](https://asusrouter.vaskivskyi.com/devices/RT-AX89X.md)                              | 💚 Confirmed        |                                                                                                                                                                                       | <a href="https://amzn.to/3i55b3S" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AX92U](https://asusrouter.vaskivskyi.com/devices/RT-AX92U.md)                              | 💚 Confirmed        | Stock:<li>`386.46061`</li>                                                                                                                                                            | <a href="https://amzn.to/3jJJgzt" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-AX3000 V2](https://asusrouter.vaskivskyi.com/devices/TUF-AX3000V2.md)                     | 💚 Confirmed        | Stock:<li>`388.23785`</li>                                                                                                                                                            | <a href="https://amzn.to/3QzzD4C" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-AX4200](https://asusrouter.vaskivskyi.com/devices/TUF-AX4200.md)                          | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3kexPjC" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-AX5400](https://asusrouter.vaskivskyi.com/devices/TUF-AX5400.md)                          | 💚 Confirmed        | Stock:<li>`386.50224`</li><li>`388.21224`</li><li>`388.22525`</li><li>`388.23285`</li><li>`388.24121`</li>Merlin:<li>`388.4_0`</li>                                                   | <a href="https://amzn.to/3hXgzyQ" rel="nofollow sponsored" target="_blank">find it</a> |
| [TUF-AX6000](https://asusrouter.vaskivskyi.com/devices/TUF-AX6000.md)                          | 💚 Confirmed        | Stock:<li>`388.32432`</li>                                                                                                                                                            | <a href="https://amzn.to/3CXqxaG" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi AX (XT8)](<https://asusrouter.vaskivskyi.com/devices/ZenWiFiAX(XT8).md>)              | 💚 Confirmed        | Stock:<li>`386.48706`</li><li>`388.23285`</li>Merlin:<li>`386.7_2-gnuton1`</li>                                                                                                       | <a href="https://amzn.to/3GuvY2L" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi AX Hybrid (XP4)](<https://asusrouter.vaskivskyi.com/devices/ZenWiFiAXHybrid(XP4).md>) | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3Itxnbb" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi AX Mini (XD4)](<https://asusrouter.vaskivskyi.com/devices/ZenWiFiAXMini(XD4).md>)     | 💚 Confirmed        | Stock:<li>`386.48790`</li><li>`386.49599`</li>                                                                                                                                        | <a href="https://amzn.to/3hYGuGl" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi Pro XT12](https://asusrouter.vaskivskyi.com/devices/ZenWiFiProXT12.md)                | 💚 Confirmed        | Stock:<li>`388.22127`</li>                                                                                                                                                            | <a href="https://amzn.to/3im6UC5" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XD4 Plus](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD4Plus.md)                | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3XtYOWp" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XD4S](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD4S.md)                       | 💛 Expected to work |                                                                                                                                                                                       | <a href="https://amzn.to/3E341xI" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XD5](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD5.md)                         | 💚 Confirmed        | Stock:<li>`388.23949`</li>                                                                                                                                                            | <a href="https://amzn.to/3YrhgjM" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XD6](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD6.md)                         | 💚 Confirmed        | Stock:<li>`388.21380`</li>                                                                                                                                                            | <a href="https://amzn.to/3jW23s4" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XD6S](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD6S.md)                       | 💚 Confirmed        | Stock:<li>`388.21380`</li>                                                                                                                                                            | <a href="https://amzn.to/3YMbyIZ" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi XT9](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXT9.md)                         | 💚 Confirmed        | Stock:<li>`388_23285`</li>                                                                                                                                                            | <a href="https://amzn.to/3JZOgLF" rel="nofollow sponsored" target="_blank">find it</a> |

### WiFi 5 | 802.11ac

| Model                                                                                     | Status              | Tested firmware                                                                                             | Find it on Amazon[^amazon]                                                             |
| ----------------------------------------------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| [4G-AC55U](https://asusrouter.vaskivskyi.com/devices/4G-AC55U.md)                         | 💚 Confirmed        | Stock:<li>`380.8102`</li>                                                                                   | <a href="https://amzn.to/3jIWQDu" rel="nofollow sponsored" target="_blank">find it</a> |
| [BRT-AC828](https://asusrouter.vaskivskyi.com/devices/BRT-AC828.md)                       | 💚 Confirmed        | Stock:<li>`382_70348`</li>                                                                                  | <a href="https://amzn.to/3X2wSL5" rel="nofollow sponsored" target="_blank">find it</a> |
| [DSL-AC68U](https://asusrouter.vaskivskyi.com/devices/DSL-AC68U.md)                       | 💚 Confirmed        | Stock:<li>`386.47534`</li><li>`386.50117`</li>Merlin:<li>`386.4-gnuton2`</li><li>`386.7_2-gnuton1`</li>     | <a href="https://amzn.to/3Z5k32H" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC51U](https://asusrouter.vaskivskyi.com/devices/RT-AC51U.md)                         | 💚 Confirmed        | Stock:<li>`380.8591`</li>                                                                                   | <a href="https://amzn.to/3WMy2sq" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC52U B1](https://asusrouter.vaskivskyi.com/devices/RT-AC52UB1.md)                    | 💚 Confirmed        |                                                                                                             | <a href="https://amzn.to/3QcrCkk" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC5300](https://asusrouter.vaskivskyi.com/devices/RT-AC5300.md)                       | 💚 Confirmed        | Merlin:<li>`386.7_2`</li>                                                                                   | <a href="https://amzn.to/3ZcJQpY" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC57U V3](https://asusrouter.vaskivskyi.com/devices/RT-AC57UV3.md)                    | 💚 Confirmed        | Stock:<li>`386.21649`</li>                                                                                  | <a href="https://amzn.to/3VAxDbx" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC58U](https://asusrouter.vaskivskyi.com/devices/RT-AC58U.md)                         | 💚 Confirmed        |                                                                                                             | <a href="https://amzn.to/3G98Mpl" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC66U](https://asusrouter.vaskivskyi.com/devices/RT-AC66U.md)                         | 💚 Confirmed        | Merlin:<li>`380.70_0`</li>                                                                                  | <a href="https://amzn.to/3WTtTD8" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC66U B1](https://asusrouter.vaskivskyi.com/devices/RT-AC66UB1.md)                    | 💚 Confirmed        | Stock:<li>`386.51255`</li>                                                                                  | <a href="https://amzn.to/3vtZ4Jm" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC68U](https://asusrouter.vaskivskyi.com/devices/RT-AC68U.md)                         | 💚 Confirmed        | Stock:<li>`386.49703`</li>Merlin:<li>`386.5_2`</li><li>`386.7_0`</li>                                       | <a href="https://amzn.to/3i6dQTE" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC85P](https://asusrouter.vaskivskyi.com/devices/RT-AC85P.md)                         | 💚 Confirmed        | Stock:<li>`382.52516`</li>                                                                                  | <a href="https://amzn.to/3kMiDdU" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC86U](https://asusrouter.vaskivskyi.com/devices/RT-AC86U.md)                         | 💚 Confirmed        | Stock:<li>`386.48260`</li><li>`386.49709`</li>Merlin:<li>`386.7_0`</li><li>`386.7_2`</li><li>`386.9_0`</li> | <a href="https://amzn.to/3CbRarK" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC87U](https://asusrouter.vaskivskyi.com/devices/RT-AC87U.md)                         | 💚 Confirmed        | Merlin:<li>`384.13_10`</li>                                                                                 | <a href="https://amzn.to/3i4sUkE" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-AC88U](https://asusrouter.vaskivskyi.com/devices/RT-AC88U.md)                         | 💚 Confirmed        | Stock:<li>`386.48260`</li>Merlin:<li>`386.5_0`</li><li>`386.7_beta1`</li><li>`386.12_2`</li>                | <a href="https://amzn.to/3FYRYBy" rel="nofollow sponsored" target="_blank">find it</a> |
| [RT-ACRH17](https://asusrouter.vaskivskyi.com/devices/RT-ACRH17.md)                       | 💚 Confirmed        | Stock:<li>`382.52517`</li>                                                                                  | <a href="https://amzn.to/3i6dWL0" rel="nofollow sponsored" target="_blank">find it</a> |
| [ZenWiFi AC Mini(CD6)](<https://asusrouter.vaskivskyi.com/devices/ZenWiFiACMini(CD6).md>) | 💛 Expected to work |                                                                                                             | <a href="https://amzn.to/3RU7vrL" rel="nofollow sponsored" target="_blank">find it</a> |

### WiFi 4 | 802.11n

| Model                                                           | Status       | Tested firmware | Find it on Amazon[^amazon]                                                             |
| --------------------------------------------------------------- | ------------ | --------------- | -------------------------------------------------------------------------------------- |
| [RT-N66U](https://asusrouter.vaskivskyi.com/devices/RT-N66U.md) | 💚 Confirmed |                 | <a href="https://amzn.to/3i7eP5Z" rel="nofollow sponsored" target="_blank">find it</a> |

## New features development

Here is the list of features being in process of development or considered for the future development. If you cannot find the feature you would like to have in the integration, please, open a [new feature request](https://github.com/Vaskivskyi/ha-asusrouter/issues/new/choose).

<table>

<tr><th>Group</th><th>Feature</th><th>Status</th></tr>

<tr><td>Connected device</td><td><ol>
<li>Per-device traffic monitoring (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/220">#220</a>)</li>
<li>Possibility to use DHCP `hostname` value for device tracking (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/119">#119</a>)</li>
</ol></td><td>
<b>considered</b>
</td></tr>

</table>

## Support the integration

### Issues and Pull requests

If you have found an issue working with the integration or just want to ask for a new feature, please fill in a new [issue](https://github.com/Vaskivskyi/ha-asusrouter/issues/new/choose).

You are also welcome to submit [pull requests](https://github.com/Vaskivskyi/ha-asusrouter/pulls) to the repository!

### Other support

This integration is a free-time project. If you like it, you can support me by buying a coffee.

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 60px !important;"></a>

Moreover, you can support the integration by using the Amazon links provided in the device lists. Any purchase (even not related to the exact product) might bring a small commission to the project.

## Thanks to

The initial codebase (from April 2022) for this integration is highly based on Home Assistant core integration [AsusWRT](https://www.home-assistant.io/integrations/asuswrt/) and [ollo69/ha_asuswrt_custom](https://github.com/ollo69/ha_asuswrt_custom).

[^amazon]: As an Amazon Associate I earn from qualifying purchases. Not like I ever got anything yet (:
