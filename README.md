[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](LICENSE)<a href="https://github.com/Vaskivskyi/ha-asusrouter/actions/workflows/build.yaml"><img src="https://img.shields.io/github/actions/workflow/status/Vaskivskyi/ha-asusrouter/build.yaml?branch=main&style=for-the-badge" alt="Build Status" align="right" /></a><br/>
[![HACS Default](https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge)](https://hacs.xyz) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=yellow)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111)<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 28px !important;" align="right" /></a><br/>
[![Installations](https://img.shields.io/endpoint?url=https://vaskivskyi.github.io/ha-custom-analytics/badges/asusrouter/total.json&style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-custom-analytics)

## Monitor and control your AsusWRT-powered router from Home Assistant

`AsusRouter` is a custom integration for Home Assistant to monitor and control your AsusWRT (and [AsusWRT-Merlin](https://www.asuswrt-merlin.net/))-powered router using the [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device.

## Full documentation

You can find the full documentation on the [official webpage](https://asusrouter.vaskivskyi.com/).

## Firmware limitations

Firmware versions `3.0.0.4.x` are fully supported (older versions might have a limited amount of sensors available). When talking about the FW, `3.0.0.4` might be missed since it is the same all the time. Important is only the last part, e.g. `386.48631` for the stock or `386.7` for Merlin FW.

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

Almost all the integration settings can be reconfigured later via the `Configure` button on the Integrations page without the need to remove your device and add it again.

[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

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

AsusRouter supports virtually every AsusWRT-powered device.

All the devices which were tested (also by the integration users) are explicitly marked as so, as well as the firmware type(s) / version(s).

### Tested

#### 802.11ax

|                                                                                              Model|Stock|Merlin / GNUton|Find it on Amazon[^amazon]|
|---------------------------------------------------------------------------------------------------|-----|---------------|------------------|
|[DSL-AX82U](https://asusrouter.vaskivskyi.com/devices/tested/DSL-AX82U.md)                         | |`386.07_0-gnuton0_beta2`|<a href="https://amzn.to/3G87vyR" rel="nofollow sponsored" target="_blank">link</a>|
|[GT-AX11000](https://asusrouter.vaskivskyi.com/devices/tested/GT-AX11000.md)                       | |`386.7_2`|<a href="https://amzn.to/3WDzOMT" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX55](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX55.md)                             | | |<a href="https://amzn.to/3Z2ath5" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX56U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX56U.md)                           | |`386.7_2`|<a href="https://amzn.to/3vrIeuz" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX58U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX58U.md)                           |`386_49674`|`386.7_2`|<a href="https://amzn.to/3jHri0L" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX68U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX68U.md)                           | | |<a href="https://amzn.to/3WzRwk5" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX82U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX82U.md)                           |`386_48664`, `386.49674`| |<a href="https://amzn.to/3Gv2Bxi" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX86S](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX86S.md)                           |`386_49447`| |<a href="https://amzn.to/3GuKac5" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX86U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX86U.md)                           |`386_46061`, `386_48260`|`386.7_2`|<a href="https://amzn.to/3WCBcPO" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX88U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX88U.md) (testing device)          |`386_45934`, `386_48631`|`386.5_2`|<a href="https://amzn.to/3i2VfYu" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX89X](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX89X.md)                           | | |<a href="https://amzn.to/3i55b3S" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AX92U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AX92U.md)                           |`386_46061`| |<a href="https://amzn.to/3jJJgzt" rel="nofollow sponsored" target="_blank">link</a>|
|[TUF-AX5400](https://asusrouter.vaskivskyi.com/devices/tested/TUF-AX5400.md)                       | | |<a href="https://amzn.to/3hXgzyQ" rel="nofollow sponsored" target="_blank">link</a>|
|[ZenWiFi AX (XT8)](https://asusrouter.vaskivskyi.com/devices/tested/ZenWiFiAX(XT8).md)             |`386_48706`|`386.07_2-gnuton1`|<a href="https://amzn.to/3GuvY2L" rel="nofollow sponsored" target="_blank">link</a>|
|[ZenWiFi AX Mini (XD4)](https://asusrouter.vaskivskyi.com/devices/tested/ZenWiFiAXMini(XD4).md)    |`386_48790`, `386_49599`| |<a href="https://amzn.to/3hYGuGl" rel="nofollow sponsored" target="_blank">link</a>|

#### 802.11ac

|                                                                                Model|Stock|Merlin / GNUton|Find it on Amazon[^amazon]|
|-------------------------------------------------------------------------------------|-----|---------------|------------------|
|[4G-AC55U](https://asusrouter.vaskivskyi.com/devices/tested/4G-AC55U.md)             | | |<a href="https://amzn.to/3jIWQDu" rel="nofollow sponsored" target="_blank">link</a>|
|[DSL-AC68U](https://asusrouter.vaskivskyi.com/devices/tested/DSL-AC68U.md)           |`386_47534`|`386.04-gnuton2`|<a href="https://amzn.to/3Z5k32H" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC51U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC51U.md)             |`380_8591`| |<a href="https://amzn.to/3WMy2sq" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC52U B1](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC52UB1.md)        | | |<a href="https://amzn.to/3QcrCkk" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC5300](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC5300.md)           | |`386.7_2`|<a href="https://amzn.to/3ZcJQpY" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC57U V3](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC57UV3.md)        |`386_21649`| |<a href="https://amzn.to/3VAxDbx" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC58U / RT-ACRH13](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC58U.md) | | |<a href="https://amzn.to/3G98Mpl" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC66R / RT-AC66U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC66U.md)  | |`380.70_0`|<a href="https://amzn.to/3WTtTD8" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC66U B1](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC66UB1.md)        | | |<a href="https://amzn.to/3vtZ4Jm" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC68U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC68U.md)             | |`386.5_2`, `386.7_0`|<a href="https://amzn.to/3i6dQTE" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC86U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC86U.md)             |`386_48260`|`386.7_0`, `386.7_2`|<a href="https://amzn.to/3CbRarK" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC87U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC87U.md)             | |`384.13_10`|<a href="https://amzn.to/3i4sUkE" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-AC88U](https://asusrouter.vaskivskyi.com/devices/tested/RT-AC88U.md)             | |`386.7_beta1`|<a href="https://amzn.to/3FYRYBy" rel="nofollow sponsored" target="_blank">link</a>|
|[RT-ACRH17](https://asusrouter.vaskivskyi.com/devices/tested/RT-ACRH17.md)           |`382.52517`| |<a href="https://amzn.to/3i6dWL0" rel="nofollow sponsored" target="_blank">link</a>|

#### 802.11n

|                                                                  Model|Stock|Merlin / GNUton|Find it on Amazon[^amazon]|
|-----------------------------------------------------------------------|-----|---------------|------------------|
|[RT-N66U](https://asusrouter.vaskivskyi.com/devices/tested/RT-N66U.md) | | |<a href="https://amzn.to/3i7eP5Z" rel="nofollow sponsored" target="_blank">link</a>|

#### Else

**Usage of AsusWRT-Merlin on non-Asus devices is ILLEGAL**
As stated by developers of Merlin ([link](https://www.snbforums.com/threads/announcement-running-asuswrt-merlin-and-forks-on-non-asus-devices-is-illegal.44636/))

|          Model|Merlin / GNUton|
|---------------|---------------|
|Netgear R6300V2|`380.70`|
|Netgear R7000  |`386.2_4`, `380.70_0-X7.9`|

## New features development

Here is the list of features being in process of development or considered for the future development. If you cannot find the feature you would like to have in the integration, please, open a [new feature request](https://github.com/Vaskivskyi/ha-asusrouter/issues/new/choose).

<table>

<tr><th>Group</th><th>Feature</th><th>Status</th></tr>

<tr><td>Access Point mode</td><td><ol>
<li>Full support (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/156">#156</a>)</li>
</ol></td><td>
<b>on hold</b><br/>(a device is required for development and testing)
</td></tr>

<tr><td>AiMesh</td><td><ol>
<li>Full support (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/16">#16</a>, <a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/161">#161</a>, <a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/203">#203</a>, <a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/261">#261</a>)</li>
</ol></td><td>
<b>on hold</b><br/>(a device with AiMesh support is required for development and testing)
</td></tr>

<tr><td>Aura RGB</td><td><ol>
<li>Full support (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/82">#82</a>)</li>
</ol></td><td>
<b>on hold</b><br/>(a device with Aura RGB support is required for development and testing)
</td></tr>

<tr><td>Connected device</td><td><ol>
<li>Per-device traffic monitoring (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/220">#220</a>)</li>
<li>Possibility to use DHCP `hostname` value for device tracking (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/119">#119</a>)</li>
</ol></td><td>
<b>considered</b>
</td></tr>

<tr><td>Port forwarding</td><td><ol>
<li>Full support (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/136">#136</a>)</li>
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

## Thanks to

The initial codebase for this integration is highly based on Home Assistant core integration [AsusWRT](https://www.home-assistant.io/integrations/asuswrt/) and [ollo69/ha_asuswrt_custom](https://github.com/ollo69/ha_asuswrt_custom).

[^amazon]: As an Amazon Associate I earn from qualifying purchases. Not like I ever got anything yet (:
