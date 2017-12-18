import gc
import config
import provision
import ota_upgrade
from reset import ResetButton

ResetButton('P19')

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
gc.collect()


from time import sleep
from _thread import start_new_thread
from math import floor
from machine import WDT, Timer
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from ambient_sensor import AmbientSensor
from dispatcher import CloudDispatcher
from http_notifier import HttpNotifier
from version import version


wdt = WDT(timeout=25000)  # enable it with a timeout of 25 seconds
queue = NotificationQueue()
notifier = HttpNotifier(config.cloud_config['thng_id'], config.cloud_config['api_key'])
dispatcher = CloudDispatcher(queue, [notifier])
ambient = AmbientSensor(queue, 90)
uptimer = Timer.Chrono()

start_new_thread(VibrationSensor(queue).loop_forever, tuple())

uptimer.start()
queue.push_version(version)

uptime_counter = uptime_period = 120 * 10
firmware_counter = firmware_period = 120 * 10

print('free memory: {}'.format(gc.mem_free()))
while True:
    wdt.feed()
    dispatcher.cycle()
    sleep(.1)

    uptime_counter -= 1
    if not uptime_counter:
        print('free memory: {}'.format(gc.mem_free()))
        queue.push_uptime(floor(uptimer.read()))
        uptime_counter = uptime_period

    firmware_counter -= 1
    if not firmware_counter:
        ota_upgrade.check_and_upgrade_if_needed(
            config.cloud_config['thng_id'],
            config.cloud_config['api_key'])
        firmware_counter = firmware_period
