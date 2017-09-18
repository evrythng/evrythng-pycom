# boot.py -- run on boot-up
import os
import pycom
# from upgrade import sd_upgrade
from machine import UART
from reset import ResetButton

ResetButton('P19')

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

# sd_upgrade()
