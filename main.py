import gc
import machine
import config
import provision
import ota_upgrade
import time
import led
import pycoproc
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
wdt.feed()

uptimer = Timer.Chrono()
uptimer.start()
uptime_counter = uptime_period = 180 * 10
uptime_counter -= 1
if not uptime_counter:
    queue.push_uptime(floor(uptimer.read()))
    uptime_counter = uptime_period

firmware_counter = firmware_period = 420 * 10
firmware_counter -= 1
if not firmware_counter:
    firmware_counter = firmware_period
'''

pysense = Pysense()
queue = NotificationQueue()
reset_button = ResetButton('P14')

wake_up_reason = pysense.get_wake_reason()

notifier = HttpNotifier(config.cloud_config['thng_id'], config.cloud_config['api_key'])
dispatcher = CloudDispatcher(queue, [notifier])

vibration_sensor = VibrationSensor(queue, pysense)
vibration_sensor.launch_in_thread()

if wake_up_reason == pycoproc.WAKE_REASON_TIMER:
    led.blink_green(period=.3)
    queue.push_version(version)
    ambient = AmbientSensor(queue, pysense)
    ambient.push_sensor_values()

elif wake_up_reason == pycoproc.WAKE_REASON_PUSH_BUTTON:
    led.blink_blue(period=0.3)
    reset_button.check()

elif wake_up_reason == pycoproc.WAKE_REASON_ACCELEROMETER:
    led.blink_red(period=.3)

elif wake_up_reason == pycoproc.WAKE_REASON_INT_PIN:
    led.blink_red(period=.3)

else:
    led.blue()
    print('normal start/reset/wdt ({})'.format(machine.wake_reason()))

print('1')
while vibration_sensor.is_running():
    dispatcher.cycle()
    time.sleep(.1)
print('3')
dispatcher.cycle()
print('4')

vibration_sensor.enable_activity_wakeup()
print('5')

'''
pysense.setup_sleep(10)
pysense.go_to_sleep()
'''
