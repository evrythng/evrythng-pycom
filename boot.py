# boot.py -- run on boot-up
import os
import machine
from machine import UART
from network import WLAN

uart = UART(0, 115200)
os.dupterm(uart)

wlan = WLAN(mode=WLAN.STA)
nets = wlan.scan()

known_networks = {
    'rusel.by': 'alina&ksenia',
    'evrythng-embedded': 'evrythng-2016'
}

for net in nets:
    if net.ssid in known_networks:
        wlan.connect(net.ssid, auth=(net.sec, known_networks[net.ssid]), timeout=5000)
        while not wlan.isconnected():
            machine.idle()  # save power while waiting
        print('WLAN connection succeeded!')
        break
