import gc
import machine
import config
import provision
import ota_upgrade
import pycom
import time
import led
import pycoproc
from _thread import start_new_thread
from pysense import Pysense

from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from ambient_sensor import AmbientSensor
from dispatcher import CloudDispatcher
from http_notifier import HttpNotifier
from reset import ResetButton
from version import version

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
    firmware_counter = firmware_period

wdt.feed()
'''

queue = NotificationQueue()

pysense = Pysense()

reset_button = ResetButton('P14')

# enable wakeup source from INT pin
# pysense.setup_int_pin_wake_up(False)

# enable activity and also inactivity interrupts, using the default callback handler
# pysense.setup_int_wake_up(True, False)

notifier = None
dispatcher = None
wake_up_reason = pysense.get_wake_reason()

if wake_up_reason == pycoproc.WAKE_REASON_TIMER:
    led.red()
    print('planned wakeup')
    notifier = HttpNotifier(config.cloud_config['thng_id'], config.cloud_config['api_key'])
    dispatcher = CloudDispatcher(queue, [notifier])
    queue.push_version(version)
    ambient = AmbientSensor(queue, pysense)
    ambient.push_sensor_values()

elif wake_up_reason == pycoproc.WAKE_REASON_PUSH_BUTTON:
    led.green()
    print('button pressed wakeup')
    reset_button.check()
    while reset_button.pressed():
        machine.idle()

elif wake_up_reason == pycoproc.WAKE_REASON_ACCELEROMETER:
    print('accelerator activity wakeup')

elif wake_up_reason == pycoproc.WAKE_REASON_INT_PIN:
    print('int pin wakeup')

else:
    led.blue()
    print('normal start/reset/wdt ({})'.format(machine.wake_reason()))


if dispatcher:
    dispatcher.cycle()

time.sleep(20)
pysense.setup_sleep(10)
pysense.go_to_sleep()
