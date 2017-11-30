import gc
import os
import pycom
import config
import provision
from machine import UART
from reset import ResetButton
from ota_upgrade import start_upgrade_if_needed


ResetButton('P19')

pycom.heartbeat(False)
uart = UART(0, 115200)
os.dupterm(uart)

provision.check_and_start_provisioning_mode()

try:
    config.read_configs()
except config.InvalidWifiConfigException:
    print('reading wifi config failed, starting provisioning mode')
    provision.start_provisioning_server()
except config.InvalidCloudConfigException:
    print('reading cloud config failed, starting provisioning mode')
    provision.start_provisioning_server()
finally:
    gc.collect()

start_upgrade_if_needed()
gc.collect()
