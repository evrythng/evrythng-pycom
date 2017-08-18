import time
import pycom
import pysense
import _thread

from micropython import const
from cloud_notifier import CloudNotifier
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
# from adc_sensor import VibrationSensor

pycom.heartbeat(False)

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

notification_queue = NotificationQueue()
cloud = CloudNotifier('U3GdtMQSegsatpRwwXQCTFmc',
                      '0YKrPmLEP0kJpMGZNmqeOJ58Ufk4TqvrDiWdRPp7xROs06EEltR2okm3augfPgx35hkAU7nO6TcjhSqo',
                      notification_queue)
v = VibrationSensor(notification_queue)

_thread.start_new_thread(v.loop_forever, tuple())

vbat_counter = vbat_period = const(60 * 10)
# cloud.loop_forever()
while True:
    cloud.cycle()
    time.sleep(.1)

    vbat_counter -= 1
    if not vbat_counter:
        notification_queue.push_vbat_property(ps.read_battery_voltage())
        vbat_counter = vbat_period
