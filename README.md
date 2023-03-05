[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](LICENSE)<a href="https://github.com/Vaskivskyi/ha-asusrouter/actions/workflows/build.yaml"><img src="https://img.shields.io/github/actions/workflow/status/Vaskivskyi/ha-asusrouter/build.yaml?branch=main&style=for-the-badge" alt="Build Status" align="right" /></a><br/>
[![HACS Default](https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge)](https://hacs.xyz) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=yellow)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111)<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://asusrouter.vaskivskyi.com/BuyMeACoffee.png" alt="Buy Me A Coffee" style="height: 28px !important;" align="right" /></a><br/>
[![Installations](https://img.shields.io/endpoint?url=https://ha-analytics.vaskivskyi.com/badges/asusrouter/total.json&style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-custom-analytics)

## Monitor and control your AsusWRT-powered router from Home Assistant

`AsusRouter` is a custom integration for Home Assistant to monitor and control your AsusWRT (and [AsusWRT-Merlin](https://www.asuswrt-merlin.net/))-powered router using the [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device.

## Full documentation

You can find the full documentation on the [official webpage](https://asusrouter.vaskivskyi.com/).

## :loudspeaker: Do you want to add AsusRouter to the default HA Core integrations?

:+1: Vote for the feature request!

[Add AsusRouter integration to HA Core - Feature Requests - Home Assistant Community (home-assistant.io)](https://community.home-assistant.io/t/add-asusrouter-integration-to-ha-core/515756?u=vaskivskyi)

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

### WiFi 7 | 802.11be
|Model|Status|Tested firmware|Find it on Amazon[^amazon]|
|---|---|---|---|
|[GT-BE98](https://asusrouter.vaskivskyi.com/devices/GT-BE98.html)|💛 Expected to work||<a href="https://amzn.to/3vGztgz" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-BE96U](https://asusrouter.vaskivskyi.com/devices/RT-BE96U.html)|💛 Expected to work||<a href="https://amzn.to/3vJu8oD" rel="nofollow sponsored" target="_blank">find it</a>|

### WiFi 6e | 802.11axe
|Model|Status|Tested firmware|Find it on Amazon[^amazon]|
|---|---|---|---|
|[GT-AXE11000](https://asusrouter.vaskivskyi.com/devices/GT-AXE11000.html)|💛 Expected to work||<a href="https://amzn.to/3Gotj9R" rel="nofollow sponsored" target="_blank">find it</a>|
|[GT-AXE16000](https://asusrouter.vaskivskyi.com/devices/GT-AXE16000.html)|💚 Confirmed|Stock:<li>`388.21617`</li>|<a href="https://amzn.to/3vObLyZ" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AXE7800](https://asusrouter.vaskivskyi.com/devices/RT-AXE7800.html)|💛 Expected to work||<a href="https://amzn.to/3jUr2LU" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi ET8](https://asusrouter.vaskivskyi.com/devices/ZenWiFiET8.html)|💛 Expected to work||<a href="https://amzn.to/3Iks0La" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi Pro ET12](https://asusrouter.vaskivskyi.com/devices/ZenWiFiProET12.html)|💛 Expected to work||<a href="https://amzn.to/3GTz68P" rel="nofollow sponsored" target="_blank">find it</a>|

### WiFi 6 | 802.11ax
|Model|Status|Tested firmware|Find it on Amazon[^amazon]|
|---|---|---|---|
|[DSL-AX82U](https://asusrouter.vaskivskyi.com/devices/DSL-AX82U.html)|💚 Confirmed|Merlin:<li>`386.07_0-gnuton0_beta2`</li>|<a href="https://amzn.to/3G87vyR" rel="nofollow sponsored" target="_blank">find it</a>|
|[GT-AX11000](https://asusrouter.vaskivskyi.com/devices/GT-AX11000.html)|💚 Confirmed|Merlin:<li>`386.7_2`</li><li>`388.1_0`</li>|<a href="https://amzn.to/3WDzOMT" rel="nofollow sponsored" target="_blank">find it</a>|
|[GT-AX11000 Pro](https://asusrouter.vaskivskyi.com/devices/GT-AX11000Pro.html)|💛 Expected to work||<a href="https://amzn.to/3VUNbHl" rel="nofollow sponsored" target="_blank">find it</a>|
|[GT-AX6000](https://asusrouter.vaskivskyi.com/devices/GT-AX6000.html)|💛 Expected to work||<a href="https://amzn.to/3GrKHKG" rel="nofollow sponsored" target="_blank">find it</a>|
|[GT6](https://asusrouter.vaskivskyi.com/devices/GT6.html)|💛 Expected to work||<a href="https://amzn.to/3GmPCfR" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX55](https://asusrouter.vaskivskyi.com/devices/RT-AX55.html)|💚 Confirmed|Stock:<li>`386.50410`</li>|<a href="https://amzn.to/3Z2ath5" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX56U](https://asusrouter.vaskivskyi.com/devices/RT-AX56U.html)|💚 Confirmed|Merlin:<li>`386.7_2`</li>|<a href="https://amzn.to/3vrIeuz" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX57](https://asusrouter.vaskivskyi.com/devices/RT-AX57.html)|💛 Expected to work||<a href="https://amzn.to/3IWnZNx" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX58U](https://asusrouter.vaskivskyi.com/devices/RT-AX58U.html)|💚 Confirmed|Stock:<li>`386.49674`</li><li>`388.22237`</li>Merlin:<li>`386.7_2`</li><li>`388.1_0`</li>|<a href="https://amzn.to/3jHri0L" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX59U](https://asusrouter.vaskivskyi.com/devices/RT-AX59U.html)|💛 Expected to work||<a href="https://amzn.to/3CVCVYO" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX68U](https://asusrouter.vaskivskyi.com/devices/RT-AX68U.html)|💚 Confirmed|Stock:<li>`388.21732`</li>|<a href="https://amzn.to/3WzRwk5" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX82U](https://asusrouter.vaskivskyi.com/devices/RT-AX82U.html)|💚 Confirmed|Stock:<li>`386.48664`</li><li>`386.49674`</li>|<a href="https://amzn.to/3Gv2Bxi" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX86S](https://asusrouter.vaskivskyi.com/devices/RT-AX86S.html)|💚 Confirmed|Stock:<li>`386.46061`</li><li>`386.48260`</li><li>`386.49447`</li><li>`388.22525`</li>Merlin:<li>`386.7_2`</li>|<a href="https://amzn.to/3GuKac5" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX86U](https://asusrouter.vaskivskyi.com/devices/RT-AX86U.html)|💚 Confirmed|Stock:<li>`386.46061`</li><li>`386.48260`</li><li>`386.49447`</li><li>`388.22525`</li>Merlin:<li>`386.7_2`</li>|<a href="https://amzn.to/3WCBcPO" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX86U Pro](https://asusrouter.vaskivskyi.com/devices/RT-AX86UPro.html)|💛 Expected to work||<a href="https://amzn.to/3ZDM41T" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX88U](https://asusrouter.vaskivskyi.com/devices/RT-AX88U.html)|💚 Confirmed|Stock:<li>`386.45934`</li><li>`386.48631`</li>Merlin:<li>`386.5_2`</li><li>`386.8_0`</li><li>`388.1_0`</li>|<a href="https://amzn.to/3i2VfYu" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX88U Pro](https://asusrouter.vaskivskyi.com/devices/RT-AX88UPro.html)|💛 Expected to work||<a href="https://amzn.to/3QNDpFZ" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX89X](https://asusrouter.vaskivskyi.com/devices/RT-AX89X.html)|💚 Confirmed||<a href="https://amzn.to/3i55b3S" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AX92U](https://asusrouter.vaskivskyi.com/devices/RT-AX92U.html)|💚 Confirmed|Stock:<li>`386.46061`</li>|<a href="https://amzn.to/3jJJgzt" rel="nofollow sponsored" target="_blank">find it</a>|
|[TUF-AX4200](https://asusrouter.vaskivskyi.com/devices/TUF-AX4200.html)|💛 Expected to work||<a href="https://amzn.to/3kexPjC" rel="nofollow sponsored" target="_blank">find it</a>|
|[TUF-AX5400](https://asusrouter.vaskivskyi.com/devices/TUF-AX5400.html)|💚 Confirmed|Stock:<li>`386.50224`</li><li>`388.21224`</li><li>`388_22525`</li>|<a href="https://amzn.to/3hXgzyQ" rel="nofollow sponsored" target="_blank">find it</a>|
|[TUF-AX6000](https://asusrouter.vaskivskyi.com/devices/TUF-AX6000.html)|💛 Expected to work||<a href="https://amzn.to/3CXqxaG" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi AX (XT8)](https://asusrouter.vaskivskyi.com/devices/ZenWiFiAX(XT8).html)|💚 Confirmed|Stock:<li>`386.48706`</li>Merlin:<li>`386.7_2-gnuton1`</li>|<a href="https://amzn.to/3GuvY2L" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi AX Hybrid (XP4)](https://asusrouter.vaskivskyi.com/devices/ZenWiFiAXHybrid(XP4).html)|💛 Expected to work||<a href="https://amzn.to/3Itxnbb" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi AX Mini (XD4)](https://asusrouter.vaskivskyi.com/devices/ZenWiFiAXMini(XD4).html)|💚 Confirmed|Stock:<li>`386.48790`</li><li>`386.49599`</li>|<a href="https://amzn.to/3hYGuGl" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi Pro XT12](https://asusrouter.vaskivskyi.com/devices/ZenWiFiProXT12.html)|💚 Confirmed|Stock:<li>`388.22127`</li>|<a href="https://amzn.to/3im6UC5" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XD4 Plus](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD4Plus.html)|💛 Expected to work||<a href="https://amzn.to/3XtYOWp" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XD4S](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD4S.html)|💛 Expected to work||<a href="https://amzn.to/3E341xI" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XD5](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD5.html)|💛 Expected to work||<a href="https://amzn.to/3YrhgjM" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XD6](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD6.html)|💚 Confirmed|Stock:<li>`388.21380`</li>|<a href="https://amzn.to/3jW23s4" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XD6S](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXD6S.html)|💚 Confirmed|Stock:<li>`388.21380`</li>|<a href="https://amzn.to/3YMbyIZ" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi XT9](https://asusrouter.vaskivskyi.com/devices/ZenWiFiXT9.html)|💛 Expected to work||<a href="https://amzn.to/3JZOgLF" rel="nofollow sponsored" target="_blank">find it</a>|

### WiFi 5 | 802.11ac
|Model|Status|Tested firmware|Find it on Amazon[^amazon]|
|---|---|---|---|
|[4G-AC55U](https://asusrouter.vaskivskyi.com/devices/4G-AC55U.html)|💚 Confirmed||<a href="https://amzn.to/3jIWQDu" rel="nofollow sponsored" target="_blank">find it</a>|
|[DSL-AC68U](https://asusrouter.vaskivskyi.com/devices/DSL-AC68U.html)|💚 Confirmed|Stock:<li>`386.47534`</li><li>`386.50117`</li>Merlin:<li>`386.4-gnuton2`</li><li>`386.7_2-gnuton1`</li>|<a href="https://amzn.to/3Z5k32H" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC51U](https://asusrouter.vaskivskyi.com/devices/RT-AC51U.html)|💚 Confirmed|Stock:<li>`380.8591`</li>|<a href="https://amzn.to/3WMy2sq" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC52U B1](https://asusrouter.vaskivskyi.com/devices/RT-AC52UB1.html)|💚 Confirmed||<a href="https://amzn.to/3QcrCkk" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC5300](https://asusrouter.vaskivskyi.com/devices/RT-AC5300.html)|💚 Confirmed|Merlin:<li>`386.7_2`</li>|<a href="https://amzn.to/3ZcJQpY" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC57U V3](https://asusrouter.vaskivskyi.com/devices/RT-AC57UV3.html)|💚 Confirmed|Stock:<li>`386.21649`</li>|<a href="https://amzn.to/3VAxDbx" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC58U](https://asusrouter.vaskivskyi.com/devices/RT-AC58U.html)|💚 Confirmed||<a href="https://amzn.to/3G98Mpl" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC66U](https://asusrouter.vaskivskyi.com/devices/RT-AC66U.html)|💚 Confirmed|Merlin:<li>`380.70_0`</li>|<a href="https://amzn.to/3WTtTD8" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC66U B1](https://asusrouter.vaskivskyi.com/devices/RT-AC66UB1.html)|💚 Confirmed|Stock:<li>`386.51255`</li>|<a href="https://amzn.to/3vtZ4Jm" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC68U](https://asusrouter.vaskivskyi.com/devices/RT-AC68U.html)|💚 Confirmed|Stock:<li>`386.49703`</li>Merlin:<li>`386.5_2`</li><li>`386.7_0`</li>|<a href="https://amzn.to/3i6dQTE" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC85P](https://asusrouter.vaskivskyi.com/devices/RT-AC85P.html)|💚 Confirmed|Stock:<li>`382.52516`</li>|<a href="https://amzn.to/3kMiDdU" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC86U](https://asusrouter.vaskivskyi.com/devices/RT-AC86U.html)|💚 Confirmed|Stock:<li>`386.48260`</li><li>`386.49709`</li>Merlin:<li>`386.7_0`</li><li>`386.7_2`</li><li>`386.9_0`</li>|<a href="https://amzn.to/3CbRarK" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC87U](https://asusrouter.vaskivskyi.com/devices/RT-AC87U.html)|💚 Confirmed|Merlin:<li>`384.13_10`</li>|<a href="https://amzn.to/3i4sUkE" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-AC88U](https://asusrouter.vaskivskyi.com/devices/RT-AC88U.html)|💚 Confirmed|Stock:<li>`386.48260`</li>Merlin:<li>`386.7_beta1`</li>|<a href="https://amzn.to/3FYRYBy" rel="nofollow sponsored" target="_blank">find it</a>|
|[RT-ACRH17](https://asusrouter.vaskivskyi.com/devices/RT-ACRH17.html)|💚 Confirmed|Stock:<li>`382.52517`</li>|<a href="https://amzn.to/3i6dWL0" rel="nofollow sponsored" target="_blank">find it</a>|
|[ZenWiFi AC Mini(CD6)](https://asusrouter.vaskivskyi.com/devices/ZenWiFiACMini(CD6).html)|💛 Expected to work||<a href="https://amzn.to/3RU7vrL" rel="nofollow sponsored" target="_blank">find it</a>|

### WiFi 4 | 802.11n
|Model|Status|Tested firmware|Find it on Amazon[^amazon]|
|---|---|---|---|
|[RT-N66U](https://asusrouter.vaskivskyi.com/devices/RT-N66U.html)|💚 Confirmed||<a href="https://amzn.to/3i7eP5Z" rel="nofollow sponsored" target="_blank">find it</a>|

## New features development

Here is the list of features being in process of development or considered for the future development. If you cannot find the feature you would like to have in the integration, please, open a [new feature request](https://github.com/Vaskivskyi/ha-asusrouter/issues/new/choose).

<table>

<tr><th>Group</th><th>Feature</th><th>Status</th></tr>

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
