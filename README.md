# aevrythng-pycom-appliance-sensor

## Overview

This is a project showing how to use EVRYTHNG and a FiPy Pycom IoT device as an appliance sensor detecting useful metrics about devices it is attached to (e.g., washing cycles, number of coffees, etc.). The device senses vibrations using an accelerometer. Data analysis and decision making is done in the cloud. 

The hardware used for the prototype:
* Main module: [FiPy](https://pycom.io/product/fipy/)
* Extension (sensor) board: [Pysense](https://pycom.io/hardware/pysense-specs/)

## Preparing the Pycom device

More information on Pycom devices can be found [here](https://docs.pycom.io/). You can find instructions how to work with and assemble the FiPy and Pysense hardware [here](https://docs.pycom.io/chapter/gettingstarted/connection/fipy.html).

Newly acquired devices might not contain the latest firmware from the manufacturer. As the use of the latest firmware is highly recommended, please follow the official guides to [update FiPy](https://docs.pycom.io/chapter/gettingstarted/installation/firmwaretool.html) and [update Pysense](https://docs.pycom.io/chapter/pytrackpysense/installation/firmware.html).


## Uploading sources to a fresh device

There are two ways to upload python sources on a "fresh" device: using the Atom + Pymakr plugin or using FTP.


### Atom + Pymakr plugin

* Follow [these instructions](https://docs.pycom.io/chapter/pymakr/installation/atom.html) to install Atom + the Pymakr plugin, and setup device communication.
* Clone/download the project from GitHub and open it in Atom.
* Once communication with the device is established, press the "Upload" button on the Pymakr plugin panel.
* Press FiPy button to restart the device.


### FTP

* Follow [these instructions](https://docs.pycom.io/chapter/gettingstarted/programming/FTP.html) to connect FileZilla to the FiPy's internal FTP server.
* Copy all `.py` and `.html` files from the project folder to the `/flash` directory on the device, while making sure to  maintain the same directory structure.
* Press the FiPy reset button to restart the device.


## Provisioning

Once the device is loaded with the latest source code and restarted, it is ready to be provisioned - i.e. receive cloud credentials and connect to a comminication network (WiFi/Sigfox/LoRa etc). As the internal web page is still in development the best way to do this is via the command line and `curl` utility:

* To set the EVRYTHNG cloud credentials: 
```
curl -X POST 192.168.4.1/evt -d '{"thng_id": "<thing id>", "api_key": "<device api key>"}'
```

* To connect to WiFi:
```
curl -X POST 192.168.4.1/provision -d ‘{“ssid”: “<ssid>”, “type”: “wifi”, “passphrase”: “<passphrase>”}’
```
> After this command the device will reboot, so make sure this is the last command.

* To connect to Sigfox:
```
curl -X POST 192.168.4.1/provision -d '{"type":"sigfox"}'
```
> After this command the device will reboot and connect to sigfox network.


### Other useful commands:

* Get the EVRYTHNG cloud credentials:
```
curl -X GET 192.168.4.1/evt
```

* Get the current network configuration (WiFi, Sigfox, etc.)
```
curl -X GET 192.168.4.1/provision
```

* Scan for WiFi networks:
```
curl -X GET 192.168.4.1/scan
```

* Get a list of available connectivity methods:
```
curl -X GET 192.168.4.1/connectivity
```

To put the device into provisioning mode press the button on the Pysense board for 3 seconds. The device will restart in provisioning mode, and the LED will start blinking blue.


## Working with the sensor and interpreting results

While in normal operation, the LED will be solid green and the device will continuously read accelerometer sensor values. The device will enter vibration mode if the following conditions are true:
* The difference between the last reading and current reading of acceleration values on any axis is greater than a threshold of 0.04 (G).
* The time between exceedances of the threshold is less then four seconds and more then two seconds.

Simply put, if the device detects vibration for more then two seconds then it enters the vibration mode. The LED will turn solid red. If four seconds pass since the last exceedance of the threshold the device exits vibration mode, send magnitude data to the cloud, and set the LED to solid green. This simple algorithm allows the device to ignore spurious vibrations. 

While in vibration mode the device sends vibration magnitudes of all three accerometer axes every minute and all other values on vibration mode exit or if the vibration lasts less then 1 minute. Magnitude data is stored in the `magnitude` property on the device's Thng in the following format:

```
[[0, -0.02294922, 0.002197266, 0.9916992], [0.0001508, 0.02099609, -0.01904297, 0.9971924], [0.4369363, 0.2623291, -0.1422119, 1.043335], ...]
```

It is a JSON array of arrays. Each array has a format of `[timestamp, x, y, z]`. The first array with timestamp `0` shows accelerometer readings before the first threshold exceedance was detected. The followings arrays have timestamps in fractions of a second since the vibration mode started. Only readings that exceed the threshold are recorded.


## Upgrade using the EVRYTHNG cloud

There is an internal mechanism for upgrading the firmware based on the [EVRYTHNG Files API](https://developers.evrythng.com/v3.0/reference#files). The device continuously checks for a new version by reading the last `_upgrade` action from the cloud, compares it the local firmware version and performs an update if there is a newer version available. 

The `post-upgrade.py` script can be used to create an upgrade bundle and to post an `_upgrade` action in the cloud in automatic mode. Do not forget to bump the version in `version.py` before launching the script. Run the `post-upgrade.py` script with the `-h` flag for more details.

While the device is upgrading itself the LED will blink red.
