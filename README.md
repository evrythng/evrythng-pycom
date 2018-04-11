# appliance-sensor

## Overview

This is the source code for appliance sensing prototype used in replenishment project. Device is sensing vibrations using an accelerometer. Data analysis and decision making is done in the cloud. 

The hardware used for the prototype:
* main module: [Fipy](https://pycom.io/product/fipy/)
* extension (sensor) board: [Pysense](https://pycom.io/hardware/pysense-specs/)

## Pycom device preparations

Extensive source of informration on pycom devices can be found [here](https://docs.pycom.io/). You can find instructions how to work with and assemble the Fipy and Pysense hardware [here](https://docs.pycom.io/chapter/gettingstarted/connection/fipy.html)

A newly acquired devices might not contain the latest firmware from the manufacturer. As the usage of the latest firmware is highly recommended, please follow the official guides to update [Fipy](https://docs.pycom.io/chapter/gettingstarted/installation/firmwaretool.html) and [Pysense](https://docs.pycom.io/chapter/pytrackpysense/installation/firmware.html).

## Uploading sources to a fresh device

There are two ways to upload python sources on a "fresh" device: using the Atom + Pymakr plugin and using FTP.

### Atom + Pymakr plugin

* Follow [this](https://docs.pycom.io/chapter/pymakr/installation/atom.html) instruction to install Atom + Pymakr plugin and setup device communication
* Pull the project from github and open it in Atom
* Once the communication with the device established press "Upload" button on a Pymakr plugin panel.
* Press Fipy button to restart

### FTP

* Follow [this](https://docs.pycom.io/chapter/gettingstarted/programming/FTP.html) instructions to connect FileZilla to Fipy's internal ftp server
* Copy *.py* and *.html* files from project folder to */flash* directory on the device maintaining the directory structure
* Press Fipy reset button to restart

## Provisioning

Once the device is loaded with the latest source code and restarted, it is ready to be provisioned, i.e. receive cloud credentials and connect to a comminication network (wifi/sigfox/lora/...). As the internal web page is still in development the best way to do that is via the command line and curl utility:
* To set Evrythng cloud credentials: 
```
curl -X POST 192.168.4.1/evt -d '{"thng_id": "<thing id>", "api_key": "<device api key>"}'
```
* to connect to wifi:
```
curl -X POST 192.168.4.1/provision -d ‘{“ssid”: “<ssid>”, “type”: “wifi”, “passphrase”: “<passphrase>”}’
```
after this command the device will reboot, so make sure this is the last command
* to connect to Sigfox:
```
curl -X POST 192.168.4.1/provision -d '{"type":"sigfox"}'
```
after this command the device will reboot and connect to sigfox network

Other usefull commands:
* get Evrythng cloud credentials:
```
curl -X GET 192.168.4.1/evt
```
* get current network configuration (wifi, sigfox,...)
```
curl -X GET 192.168.4.1/provision
```
* scan for wifi networks:
```
curl -X GET 192.168.4.1/scan
```
* get list of available connectivity methods:
```
curl -X GET 192.168.4.1/connectivity
```

To put the device in provision mode press button on a Pysense board for 3 seconds. The device will restart in provisioning mode. The LED starts blinking blue.

## Working with the sensor and interpreting results

While normal operation LED is solid green and device reads accelerometer sensor values. The device enters "vibration" mode is the following is true:
* difference between last reading and current reading of acceleration values on any axis is greater then a threshold of 0.04 (G)
* time between exceedances of the threshold is less then 4 seconds and more then 2 seconds

Simply speaking if the device detects vibration for more then 2 seconds then it enters vibration mode. The LED turns solid red. If 4 seconds pass since last exceedance of the threshold device exits vibration mode, sends magnitudes and LED turns solid green. This simple algo allows skipping spurious vibrations. 

While in vibration mode device device sends vibration magnitudes of all 3 axis every 1 minute and all other values on vibration mode exit or if the vibration last less then 1 minute. Magnitudes are sent to "magnitude" property in the following format:
```
[[0, -0.02294922, 0.002197266, 0.9916992], [0.0001508, 0.02099609, -0.01904297, 0.9971924], [0.4369363, 0.2623291, -0.1422119, 1.043335], ...]
```
It is a json array of arrays. Each array has a format of [timestamp, x, y, z]. The first array with timestamp 0 shows accelerometer readings before the first threshold exceedance detected. The followings arrays has timestamps in fractions of a second since the vibration mode start. Only readings that exceed the threshold are recorded.

## Upgrade using the Evrythng cloud

There is an internal mechanism for upgrading the firmware (i.e. updating python sources) which is based on [Evrythng Files API](https://developers.evrythng.com/v3.0/reference#files). Device continuously checks for new version by reading the last *_upgrade* action from the cloud, compares the available version with its own and performs update if there is a newer version available. *post-upgrade.py* script can be used to create an upgrade bundle and post *_upgrade* action in the cloud in automatic mode. Do not forget to bump up version in *version.py* before launching the script. Run *post-upgrade.py* script with *-h* flag for more details.

While the device is upgrading itself the LED blinks red.

## Demo Documentation
https://docs.google.com/document/d/1yxOJHeC2tDd06ut66XmhzxQ-GzqhM1e_P--p_pBHA24/edit#
