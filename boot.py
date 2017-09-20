# boot.py -- run on boot-up
import os
import pycom
import config
import provision
# from upgrade import sd_upgrade
from machine import UART
from reset import ResetButton

ResetButton('P19')

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

# sd_upgrade()

provision.check_and_start_provisioning_mode()

try:
    config.read_config()
except config.InvalidConfigException:
    print('reading config failed, starting provisioning mode')
    provision.start_provisioning_server()
