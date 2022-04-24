## AsusRouter - a custom Home Assistant integration

AsusRouter is a custom integration for Home Assistant to monitor and control your Asus router using [AsusRouter](https://github.com/Vaskivskyi/asusrouter) python library.

Please note, that this integration is in the early development stage and may contain some errors. You could always help with its development by providing your feedback.


## Installation

#### Manual

Copy content of `custom_components/asusrouter/` to `custom_components/asusrouter/` in your Home Assistant folder.

#### HACS

You can add this repository to a list of custom repositories in your HACS.


## Usage

After AsusRouter is installed, you can add your device from Home Assistant UI. 

#### Sensors

Integration provides several types of sensors:
- WAN traffic and speed sensors (x4, enabled by default)
- Secondary (USB) WAN traffic and speed sensors (x4, disabled)
- CPU usage sensor (disabled)
- RAM usage sensor (disabled)
- Connected devices sensor (enabled)
- Boot time sensor (disabled)

#### Device trackers

Device trackers (disabled by default for unknown to HA devices) contain the following attributes:
- IP address
- MAC
- Hostname
- Last time reachable
- Connection time (WiFi devices only)

## Support the integration

### Issues and Pull requests

If you have found an issue working with the integration or just want to ask for a new feature, please fill in a new [issue](https://github.com/Vaskivskyi/ha-asusrouter/issues).

You are also welcome to submit [pull requests](https://github.com/Vaskivskyi/ha-asusrouter/pulls) to the repository!

### Check it with your device

Testing the integration with different devices would help a lot in the development process. Unfortunately, currently, I have only one device available, so your help would be much appreciated.

### Other support

This integration is a free-time project. If you like it, you can support me by buying a coffee.

<a href="https://www.buymeacoffee.com/vaskivskyi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;"></a>

