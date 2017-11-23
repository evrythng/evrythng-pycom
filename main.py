import math
import time
import _thread
import pysense
from machine import Pin
from machine import WDT
from machine import Timer
from micropython import const
from config import cloud_config
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from temp_sensor import TemperatureSensor
from dispatcher import CloudDispatcher

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

wireless_selector = Pin('P20', mode=Pin.IN, pull=Pin.PULL_DOWN)
if wireless_selector():
    print('Sigfox notifier selected')
    from sigfox_notifier import SigfoxNotifier
    notifier = SigfoxNotifier()
else:
    print('HTTP notifier selected')
    from http_notifier import HttpNotifier
    notifier = HttpNotifier(cloud_config['thng_id'], cloud_config['api_key'])

wdt = WDT(timeout=25000)  # enable it with a timeout of 20 seconds

queue = NotificationQueue()
dispatcher = CloudDispatcher(queue, [notifier])

v = VibrationSensor(queue)
_thread.start_new_thread(v.loop_forever, tuple())

ht = TemperatureSensor(queue, 60)

uptimer = Timer.Chrono()
uptimer.start()

uptime_counter = uptime_period = const(90 * 10)
while True:
    wdt.feed()
    dispatcher.cycle()
    time.sleep(.1)

    uptime_counter -= 1
    if not uptime_counter:
        print('uptime: {}'.format(uptimer.read()))
        queue.push_uptime(math.floor(uptimer.read()))
        uptime_counter = uptime_period
