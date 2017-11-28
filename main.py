import math
import time
import _thread
from machine import Pin
from machine import WDT
from machine import Timer
from micropython import const
from config import cloud_config
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from ambient_sensor import AmbientSensor
from dispatcher import CloudDispatcher
from ota_upgrade import OTAUpgrader

wireless_selector = Pin('P20', mode=Pin.IN, pull=Pin.PULL_DOWN)
if wireless_selector():
    print('Sigfox notifier selected')
    from sigfox_notifier import SigfoxNotifier
    notifier = SigfoxNotifier()
else:
    print('HTTP notifier selected')
    from http_notifier import HttpNotifier
    notifier = HttpNotifier(cloud_config['thng_id'], cloud_config['api_key'])

wdt = WDT(timeout=25000)  # enable it with a timeout of 25 seconds

queue = NotificationQueue()
dispatcher = CloudDispatcher(queue, [notifier])

v = VibrationSensor(queue)
_thread.start_new_thread(v.loop_forever, tuple())

ht = AmbientSensor(queue, 90)

uptimer = Timer.Chrono()
uptimer.start()

ota_upgrader = OTAUpgrader()

uptime_counter = uptime_period = const(90 * 10)
while True:
    wdt.feed()
    dispatcher.cycle()
    time.sleep(.1)

    uptime_counter -= 1
    if not uptime_counter:
        queue.push_uptime(math.floor(uptimer.read()))
        ota_upgrader.check_and_upgrade()
        uptime_counter = uptime_period
