# boot.py -- run on boot-up
import os
from upgrade import sd_upgrade
from machine import UART

uart = UART(0, 115200)
os.dupterm(uart)

sd_upgrade()
