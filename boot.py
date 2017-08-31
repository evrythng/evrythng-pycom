# boot.py -- run on boot-up
import os
import pycom
from upgrade import sd_upgrade
from machine import UART

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

sd_upgrade()
