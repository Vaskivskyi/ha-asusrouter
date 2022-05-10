## Dashboards ideas for AsusRouter integration

### Simple status dashboard

Sensors provided by the integration can be used for a simple status dashboard.

In this case, the following custom cards are used:

<details>
<summary>List of custom cards</summary>

- [stack-in-card](https://github.com/custom-cards/stack-in-card)
- [text-divider-row](https://github.com/iantrich/text-divider-row)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card)
</details>

![Simple AsusRouter status dashboard](Fig-Dashboard-1.png)

Fig. 1. Simple AsusRouter status dashboard

<details>
<summary>YAML code</summary>

*Replace `rt_ac66u` with your device*

```yaml
type: custom:stack-in-card
cards:
  - type: entities
    entities:
      - text: Router
        type: custom:text-divider-row
  - type: custom:mini-graph-card
    name: CPU
    color_thresholds:
      - color: '#159F3B'
        value: 0
      - color: '#F2B528'
        value: 50
      - color: '#DD5129'
        value: 80
    decimals: 2
    entities:
      - entity: sensor.rt_ac66u_cpu
        name: CPU
        show_state: true
        state_adaptive_color: true
    font_size: 75
    hour24: true
    hours_to_show: 1
    line_width: 3
    points_per_hour: 120
    update_interval: 10
  - type: entities
    entities:
      - entity: sensor.rt_ac66u_ram
        name: RAM
      - entity: sensor.rt_ac66u_connected_devices
        name: Connected devices
      - entity: sensor.rt_ac66u_boot_time
        name: Boot time
      - entity: sensor.rt_ac66u_wan_speed
        name: WAN
      - entity: sensor.rt_ac66u_lan_speed
        name: LAN
  - type: custom:mini-graph-card
    name: WAN
    decimals: 2
    entities:
      - entity: sensor.rt_ac66u_wan_download_speed
        name: Download
        show_state: true
        state_adaptive_color: true
      - entity: sensor.rt_ac66u_wan_upload_speed
        name: Upload
        show_state: true
        state_adaptive_color: true
    font_size: 75
    hour24: true
    hours_to_show: 3
    line_width: 3
    points_per_hour: 30
    update_interval: 300
```
</details>


### For those who like to control everything

The followind custom cards are used:

<details>
<summary>List of custom cards</summary>

- [stack-in-card](https://github.com/custom-cards/stack-in-card)
- [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row)
</details>

![Detailed AsusRouter health dashboard](Fig-Dashboard-2.png)

Fig. 2. Detailed AsusRouter health dashboard. Please, note that RAM attributes are recalculated inside the custom card with 1/1000 factor. To have a correct value, one would need to divide by 1024.

<details>
<summary>YAML code</summary>

*Replace `rt_ac66u` with your device*

```yaml
type: custom:stack-in-card
cards:
  - type: entities
    entities:
      - type: custom:text-divider-row
        text: Health
      - type: custom:multiple-entity-row
        entity: sensor.rt_ac66u_ram
        name: RAM (MB)
        show_state: true
        state_header: Usage
        entities:
          - entity: sensor.rt_ac66u_ram
            attribute: Total
            name: Total
            format: kilo
          - entity: sensor.rt_ac66u_ram
            attribute: Used
            name: Used
            format: kilo
          - entity: sensor.rt_ac66u_ram
            attribute: Free
            name: Free
            format: kilo
      - type: custom:text-divider-row
        text: Ports status
      - type: custom:multiple-entity-row
        entity: sensor.rt_ac66u_lan_speed
        name: WAN speed (Mb/s)
        show_state: true
        state_header: WAN 0
        unit: false
      - type: custom:multiple-entity-row
        entity: sensor.rt_ac66u_lan_speed
        name: LAN speed (Mb/s)
        show_state: false
        entities:
          - entity: sensor.rt_ac66u_lan_speed
            attribute: LAN 1
            name: LAN 1
          - entity: sensor.rt_ac66u_lan_speed
            attribute: LAN 2
            name: LAN 2
          - entity: sensor.rt_ac66u_lan_speed
            attribute: LAN 3
            name: LAN 3
          - entity: sensor.rt_ac66u_lan_speed
            attribute: LAN 4
            name: LAN 4

```
</details>


