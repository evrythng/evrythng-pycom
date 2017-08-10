import pycom
import pysense
import _thread

from cloud_notifier import CloudNotifier
from notification_queue import NotificationQueue
from vibration_sensor import VibrationSensor

pycom.heartbeat(False)

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

notification_queue = NotificationQueue()
cloud = CloudNotifier('UGF4satMBD8atpwawDXK2pXp',
                      'hxiiLp4uaOtmUvM2awOT2cg3wdZi5CAUesiTMppVXKGBjz5ODn9Y48BOdc1gOsn0zrFJe9YIw87FVeLQ',
                      notification_queue)
v = VibrationSensor(notification_queue)

_thread.start_new_thread(v.loop_forever, tuple())

cloud.loop_forever()
