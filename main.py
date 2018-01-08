import gc
import math
import machine
import config
import provision
import ota_upgrade
import pycom
import time
from _thread import start_new_thread
from pysense import Pysense

from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from ambient_sensor import AmbientSensor
from dispatcher import CloudDispatcher
from http_notifier import HttpNotifier
from reset import ResetButton
from version import version

ResetButton('P14')

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

ota_upgrade.start_upgrade_if_needed()

queue = NotificationQueue()
ambient = AmbientSensor(queue, 90)
notifier = HttpNotifier(config.cloud_config['thng_id'], config.cloud_config['api_key'])
dispatcher = CloudDispatcher(queue, [notifier])

'''
wdt = machine.WDT(timeout=25000)  # enable it with a timeout of 25 seconds
# uptimer = Timer.Chrono()

# start_new_thread(VibrationSensor(queue).loop_forever, tuple())

# uptimer.start()

uptime_counter = uptime_period = 180 * 10
firmware_counter = firmware_period = 420 * 10

uptime_counter -= 1
if not uptime_counter:
    queue.push_uptime(floor(uptimer.read()))
    uptime_counter = uptime_period

firmware_counter -= 1
if not firmware_counter:
    ota_upgrade.check_and_upgrade_if_needed(
        config.cloud_config['thng_id'],
        config.cloud_config['api_key'])
    firmware_counter = firmware_period

wdt.feed()
'''

# WAKE_REASON_ACCELEROMETER = 1
# WAKE_REASON_PUSH_BUTTON = 2
# WAKE_REASON_TIMER = 4
# WAKE_REASON_INT_PIN = 8

# pycom.heartbeat(False)
pysense = Pysense()

# enable wakeup source from INT pin
pysense.setup_int_pin_wake_up(False)

# enable activity and also inactivity interrupts, using the default callback handler
pysense.setup_int_wake_up(True, False)

wake_up_reason = pysense.get_wake_reason()
print("Wakeup reason: " + wake_up_reason)
if wake_up_reason == Pysense.WAKE_REASON_TIMER:
    queue.push_version(version)
    ambient.push_sensor_values()

'''
pysense.setup_sleep(30)
pysense.go_to_sleep()
'''

dispatcher.cycle()

print('sleeping now')
while True:
    machine.idle()
