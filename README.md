[![GitHub Release](https://img.shields.io/github/release/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=blue)](https://github.com/Vaskivskyi/ha-asusrouter/releases) [![License](https://img.shields.io/github/license/Vaskivskyi/ha-asusrouter.svg?style=for-the-badge&color=yellow)](LICENSE)<a href="https://github.com/Vaskivskyi/ha-asusrouter/actions/workflows/build.yaml"><img src="https://img.shields.io/github/workflow/status/Vaskivskyi/ha-asusrouter/Build?style=for-the-badge" alt="Build Status" align="right" /></a><br/>
[![HACS Default](https://img.shields.io/badge/HACS-default-blue.svg?style=for-the-badge)](https://hacs.xyz) [![Community forum discussion](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge&color=yellow)](https://community.home-assistant.io/t/custom-component-asusrouter-integration/416111)<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 28px !important;" align="right" /></a>

## Monitor and control your AsusWRT-powered router from Home Assistant

`AsusRouter` is a custom integration for Home Assistant to monitor and control your AsusWRT (and [AsusWRT-Merlin](https://www.asuswrt-merlin.net/))-powered router using the [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

The integration uses the native HTTP(S) API (the same way as WebUI) and relies on direct communication with your device.

#### Firmware limitations

Firmware versions `3.0.0.4.x` are fully supported (older versions might have a limited amount of sensors available). When talking about the FW, `3.0.0.4` might be missed since it is the same all the time. Important is only the last part, e.g. `386.48631` for the stock or `386.7` for Merlin FW.

Firmware `5.x.x` (some DSL models) is **NOT supported** (not AsusWRT).

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

Our [Setup documentation](https://github.com/Vaskivskyi/ha-asusrouter/blob/main/docs/setup.md) may provide you with detailed information on the configuration flow and all the possible options.

Almost all the integration settings can be reconfigured later via the `Configure` button on the Integrations page without the need to remove your device and add it again.

[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/)

### Monitoring

#### Binary sensors

<details>
<summary>OpenVPN Client (<b>non-control mode only</b>)</summary>

*(enabled by default)*
  - name: `openvpn_client_x`
  - attributes:
    - `error_code`
    - `status` - status of the connection (`disconnected`, `connecting`, `connected`)
  - attributes **(FW: Merlin-only)**:
    - `auth_read`
    - `local_ip`
    - `post_compress_bytes`
    - `post_decompress_bytes`
    - `pre_compress_bytes`
    - `pre_decompress_bytes`
    - `public_ip`
    - `server_auth`
    - `server_ip`
    - `server_port`
    - `tcp_udp_read_bytes`
    - `tcp_udp_write_bytes`
    - `tun_tap_read_bytes`
    - `tun_tap_write_bytes`
    - `update_time`
  - description: Sensor value represents the current state of the OpenVPN client. Please, note, that both `connected` and `connecting` status will correspond to the switch being in the `On` state
</details>

<details>
<summary>WAN status</summary>

*(disabled by default)*

  - name: `wan`
  - attributes:
    - `dns`
    - `gateway`
    - `ip`
    - `ip_type` - type of the IP (can be `static`, `dhcp` and more)
    - `mask`
    - `private_subnet`
  - description: Sensor value represents the internet connection of the device
</details>

<details>
<summary>WiFi (<b>non-control mode only</b>)</summary>

*(enabled by default)*
  - name: `wireless_{}`, where `{}` can be `2_4_ghz`, `5_ghz`, `5_ghz_2`, `6_ghz`
  - attributes:
    - `auth_method`
    - `channel`
    - `channel_bandwidth`
    - `chanspec`
    - `country_code`
    - `gmode_check`
    - `group_key_rotation`
    - `hidden`
    - `maclist_x`
    - `macmode`
    - `mbo_enable`
    - `mfp`
    - `mode`
    - `password`
    - `radius_ipaddr`
    - `radius_key`
    - `radius_port`
    - `ssid`
    - `wpa_encryption`
    - `xbox_optimized`
  - description: Sensor value represents the current value of the WiFi network
</details>

#### Device trackers

Device trackers are disabled by default if HA doesn't know the device. The generated `device_tracker.device_name` entities include `device_name` as reported by AsusRouter library according to the priority list:
- Friendly name of the device (if set in the router admin panel)
- Name as reported by the connected device
- MAC address if neither of the above is known

<details>
<summary>Attributes</summary>

- `connection_time` - time of connection to the router (only wireless devices)
- `connection_type` - type of connection (`Wired`, `2.4 GHz`, `5 GHz`). Implementation of `6 GHz` requires a test device.
- `host_name` - the name of the connected device as stated before
- `internet` - internet connection of the device, boolean: `true` - connected, `false` - disconnected
- `internet_mode` - internet mode of the device: `allow` - internet access alowed, `block` - internet access blocked, `time` - parental control is enabled with schedule
- `ip`
- `ip_type` - (`Manual`, `DHCP` and other)
- `last_activity` - last time the device was seen online in HA
- `mac`
- `rssi` - (only wireless devices)
- `rx_speed` - (only wireless devices)
- `tx_speed` - (only wireless devices)
</details>

If the connected device's MAC address is known to Home Assistant (e.g. it was set up by another integration `ABC`), its `device_tracker` will be added to that device in the enabled state. Moreover, this device will be showing for both integrations: `AsusRouter` and `ABC`

#### Sensors

<details>
<summary>Boot time sensor</summary>

*(disabled by default)*
  - name: `boot_time`
  - units: ` `
  - description: The sensor represents the last time the device was rebooted.
</details>

<details>
<summary>Connected devices sensor</summary>

*(enabled by default)*
  - name: `connected_devices`
  - units: ` `
  - attributes:
    - `devices` - represents a list of all connected (active) devices as their `MAC/IP/Hostname`
  - description: The sensor shows the total number of devices connected.
</details>

<details>
<summary>CPU usage sensor</summary>

*(disabled by default)*
  - name: `cpu`
  - units: `%`
  - attributes:
    - `core_X` - usage by corer `x`
  - description: Sensor shows average CPU usage.
</details>

<details>
<summary>Load average sensors (FW: <b>Merlin-only</b>)</summary>

*(disabled by default)*
  - names: `load_average_{}_min` for `1`, `5` and `15` minutes
  - description: Sensors represent average load in the usual Linux way. Sensors rely on the `sysinfo`, available only with the Merlin firmware.

</details>

<details>
<summary>Network traffic and speed</summary>

*(enabled by default)*

- **Traffic**:
  - names: `{}_download` / `{}_upload`
  - units: `GB` [^units] (default) ([important note](#keep-in-mind)). Can be selected during/after the integration configuration.
  - attributes:
    - `bytes` - raw data from the device
- **Speed**:
  - names: `{}_download_speed` / `{}_upload_speed`
  - units: `Mb/s` (default). Can be selected during/after the integration configuration.
  - attributes:
    - `bits/s` - raw data from device

Possible network interfaces (can be changed via the `Configure` button for the configuration):
- `WAN` - traffic to your ISP (*Some of the devices do not report WAN data, refer to the [issue](https://github.com/Vaskivskyi/ha-asusrouter/issues/30). If your device also doesn't show such sensors, please add your information to this issue*)
- `USB` - traffic to the USB modem / mobile phone connected via USB. Will be showing the correct values when USB WAN is connected and `unknown` when a phone / USB modem is disconnected.
- `LAN` - local wired traffic
- `WLANx` - wireless traffic: `0` - 2.4 GHz WiFi, `1` and `2` - 5 GHz WiFi
- and more
</details>

<details>
<summary>Ports connection sensors</summary>

*(disabled by default)*

  - names: `lan_speed` / `wan_speed`
  - units: `Mb/s`
  - attributes:
    - `lan_X` / `wan_X` - represents speed of each port `x` in `Mb/s`
  - description: Sensor value represents the total speed on all the connected LAN / WAN ports. E.g. if 2 ports are connected in `1 Gb/s` mode and 1 - in `100 Mb/s` mode, this value will be `2100 Mb/s`.
</details>

<details>
<summary>RAM usage sensor</summary>

*(disabled by default)*
  - name: `ram`
  - units: `%`
  - attributes (all in `KB`, as device reports):
    - `free`
    - `total`
    - `used`
  - description: Sensor represents RAM usage of the device. In most cases, it slowly increases with time. On reboot, RAM usage drops. 
</details>

<details>
<summary>Temperature sensors</summary>

*(disabled by default)*

**Availability of sensors depends on your device and firmware**

  - names: `temperature_{}` for `cpu` (CPU), `2_4_ghz` (2.4 GHz module), `5_ghz` (5 GHz module)
  - units: `°C` (native)
  - description: Sensors represent the temperature value of the corresponding module. Entities are created only for the sensors available for your device and firmware.
</details>

<details>
<summary>WAN IP sensor</summary>

*(disabled by default)*

  - name: `wan_ip`
  - attributes:
    - `dns`
    - `gateway`
    - `ip_type` - type of the IP (can be `static`, `dhcp` and more)
    - `mask`
    - `private_subnet`
  - description: Sensor value represents the current external IP address of the device
</details>

#### Keep in mind

- If your device supports the dual-WAN feature, the [corresponding sensors](#sensors) for traffic and speed can be created. They will be showing the correct values when USB WAN is connected and `unknown`, when a phone / USB modem is disconnected.
- AsusWRT firmware calculates traffic as an N-digit HEX, so it overflows and resets to zero. On older devices, it can overflow at only 4 294 967 296 bytes (4 GB). The newer devices have limits between 100 and 1000 GB, depending on the interface. One can either use [Long-term statistics](#long-term-statistics) or create a [`utility_meter`](https://www.home-assistant.io/integrations/utility_meter/) for more control and the possibility to monitor traffic above the limitation.
- The integration uses `2^10` conversion factors in calculations - the same way as native Asus software. If you would like to use `10^3` factors, all the sensors provide raw data in bytes or bits/s.

### Control

All the following entities require `Device control` to be enabled in the integration settings. Some of the entities may not be available for your device because of their firmware limitation.

Please, keep this in mind. Some `lights` / `switches` might require processing time (especially for older devices). In the Home Assistant, this may look like the switch didn't work and clicked back to the initial state. But it will get the correct value on the next state update (mostly not more than several seconds).

#### Lights

<details>
<summary>LED</summary>

*(enabled by default)*
  - name: `led`
  - description: Light entity allows user to control LED state of the device
  - not available for: `RT-AC66U`
</details>

#### Switches

<details>
<summary>OpenVPN Client</summary>

*(enabled by default)*
  - name: `openvpn_client_x`
  - attributes:
    - `error_code`
    - `status` - status of the connection (`disconnected`, `connecting`, `connected`)
  - attributes **(FW: Merlin-only)**:
    - `auth_read`
    - `local_ip`
    - `post_compress_bytes`
    - `post_decompress_bytes`
    - `pre_compress_bytes`
    - `pre_decompress_bytes`
    - `public_ip`
    - `server_auth`
    - `server_ip`
    - `server_port`
    - `tcp_udp_read_bytes`
    - `tcp_udp_write_bytes`
    - `tun_tap_read_bytes`
    - `tun_tap_write_bytes`
    - `update_time`
  - description: Switch entity allows turning on / off available OpenVPN client. Please, note, that both `connected` and `connecting` status will correspond to the switch being in the `On` state
</details>

<details>
<summary>WiFi</summary>

*(enabled by default)*
  - name: `wireless_{}`, where `{}` can be `2_4_ghz`, `5_ghz`, `5_ghz_2`, `6_ghz`
  - attributes:
    - `auth_method`
    - `channel`
    - `channel_bandwidth`
    - `chanspec`
    - `country_code`
    - `gmode_check`
    - `group_key_rotation`
    - `hidden`
    - `maclist_x`
    - `macmode`
    - `mbo_enable`
    - `mfp`
    - `mode`
    - `password`
    - `radius_ipaddr`
    - `radius_key`
    - `radius_port`
    - `ssid`
    - `wpa_encryption`
    - `xbox_optimized`
  - description: Switch entity allows turning on / off WiFi network
</details>

## Tested devices

The integration supports virtually **any** AsusWRT-powered device with firmware `3.0.0.4.x`.

This list provides only the models tested by me or other users. If your device is not listed yet but works well, please open a [Device Support](https://github.com/Vaskivskyi/ha-asusrouter/issues/new/choose) ticket with the device model and it will be added to the list.

<table>

<tr><th>Group</th><th>Devices</th><th>Firmware</th><th>Limitation</th></tr>

<tr><td>Full support</td><td>

**802.11ax**:<br/>
`DSL-AX82U` (<a href="https://amzn.to/3rXo7md" target="_blank">link*</a>)<br/>
`GT-AX11000` (<a href="https://amzn.to/3VpWgJa" target="_blank">link</a>)<br/>
`RT-AX55` (<a href="https://amzn.to/3MwlBwP" target="_blank">link</a>)<br/>
`RT-AX58U` (<a href="https://amzn.to/3Mrpu6a" target="_blank">link</a>)<br/>
`RT-AX68U` (<a href="https://amzn.to/3rS2jZy" target="_blank">link</a>)<br/>
`RT-AX82U` (<a href="https://amzn.to/3MslCC0" target="_blank">link</a>)<br/>
`RT-AX86U` (<a href="https://amzn.to/3CxEGdk" target="_blank">link</a>)<br/>
`RT-AX86S` (reported as `RT-AX86U`) (<a href="https://amzn.to/3g2YPAK" target="_blank">link</a>)<br/>
`RT-AX88U` (<a href="https://amzn.to/3RVEoTh" target="_blank">link</a>)<br/>
`RT-AX89X` (<a href="https://amzn.to/3fRXXi3" target="_blank">link</a>)<br/>
`RT-AX92U` (<a href="https://amzn.to/3EFz57O" target="_blank">link</a>)<br/>
`TUF-AX5400` (<a href="https://amzn.to/3MtthzR" target="_blank">link</a>)<br/>
`ZenWiFi AX (XT8)` (<a href="https://amzn.to/3Cn8tW4" target="_blank">link</a>)<br/>
`ZenWiFi AX Mini (XD4)` (<a href="https://amzn.to/3CTveTf" target="_blank">link</a>)<br/><br/>
**802.11ac**:<br/>
`4G-AC55U`<br/>
`DSL-AC68U` (<a href="https://amzn.to/3CQ77oq" target="_blank">link</a>)<br/>
`RT-AC5300`<br/>
`RT-AC86U` (<a href="https://amzn.to/3VgJ60S" target="_blank">link</a>)<br/>
`RT-ACRH13`

</td><td><b>Stock</b>: Any<br/><b>Merlin</b>: Any</td><td></td></tr>

<tr><td>Limited support</td><td>

**802.11ac**:<br/>
`RT-AC51U` (<a href="https://amzn.to/3VooPGF" target="_blank">link</a>)<br/>
`RT-AC66U` (<a href="https://amzn.to/3yBeldp" target="_blank">link</a>)<br/>
`RT-ACRH17` (reported as `RT-AC82U`)<br/><br/>
**802.11n**:<br/>
`RT-N66U`

</td><td><b>Stock</b>: Latest available<b><br/>Merlin</b>: 380.70+</td><td>no LED control</td></tr>

<tr><td>Non-Asus devices</td><td>

**Netgear**:<br/>
`R6300V2`,<br/>
`R7000`

</td><td><b>Merlin</b>: 380.70+</td><td></td></tr>

<tr><td><b>Not supported</b></td><td>

`DSL-AC68VG` (non-compatible FW)

</td><td></td><td></td></tr>

</table>
* As an Amazon Associate I earn from qualifying purchases. Not like I ever got anything yet (:

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
<li>Blocking internet access (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/146">#146</a>)</li>
<li>Per-device traffic monitoring (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/220">#220</a>)</li>
<li>Possibility to use DHCP `hostname` value for device tracking (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/119">#119</a>)</li>
</ol></td><td>
<b>in progress [1]<br/>considered [2,3]</b>
</td></tr>

<tr><td>Firmware</td><td><ol>
<li>Available updates status (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/222">#222</a>)</li>
</ol></td><td>
<b>considered</b>
</td></tr>

<tr><td>Guest network</td><td><ol>
<li>Enable / disable (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/213">#213</a>)</li>
<li>Full control (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/213">#213</a>)</li>
</ol></td><td>
<b>in progress [1]<br/>considered [2]</b>
</td></tr>

<tr><td>Port forwarding</td><td><ol>
<li>Full support (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/136">#136</a>)</li>
</ol></td><td>
<b>considered</b>
</td></tr>

<tr><td>VPN</td><td><ol>
<li>OpenVPN server switches (<a href="https://github.com/Vaskivskyi/ha-asusrouter/issues/224">#224</a>)</li>
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

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 60px !important;"></a>

## Thanks to

The initial codebase for this integration is highly based on Home Assistant core integration [AsusWRT](https://www.home-assistant.io/integrations/asuswrt/) and [ollo69/ha_asuswrt_custom](https://github.com/ollo69/ha_asuswrt_custom).



