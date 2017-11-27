# boot.py -- run on boot-up
import os
import pycom
import config
import provision
# from upgrade import sd_upgrade
from machine import UART
from reset import ResetButton

ResetButton('P14')

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

# sd_upgrade()

provision.check_and_start_provisioning_mode()

try:
    config.read_configs()
except config.InvalidWifiConfigException:
    print('reading wifi config failed, starting provisioning mode')
    provision.start_provisioning_server()
except config.InvalidCloudConfigException:
    print('reading cloud config failed, starting provisioning mode')
    provision.start_provisioning_server()
