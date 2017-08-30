import time
import pycom
import pysense
import _thread

from micropython import const
from config import config
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
from sigfox_notifier import SigfoxNotifier
from http_notifier import HttpNotifier
from dispatcher import CloudDispatcher

pycom.heartbeat(False)

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

cloud_settings = config['cloud_settings']

http = HttpNotifier(cloud_settings['thng_id'], cloud_settings['api_key'])
# sigfox = SigfoxNotifier()
queue = NotificationQueue()
dispatcher = CloudDispatcher(queue, [http])

v = VibrationSensor(queue)
_thread.start_new_thread(v.loop_forever, tuple())

vbat_counter = vbat_period = const(60 * 10)
# dispatcher.loop_forever()
while True:
    dispatcher.cycle()
    time.sleep(.1)

    vbat_counter -= 1
    if not vbat_counter:
        queue.push_battery_voltage(ps.read_battery_voltage())
        vbat_counter = vbat_period
