import pycom
import pysense
import _thread

from cloud import CloudNotifier
from notification_queue import NotificationQueue
from vibration_sensor import VibrationSensor

pycom.heartbeat(False)

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

notification_queue = NotificationQueue()
cloud = CloudNotifier('UGF4satMBD8atpwawDXK2pXp',
                      'wmioueSdGLwYbRmcqLds2aFW4Rc8haciqtf6aVEaVidb9eP0mFH6hm9SSjIWFk6WxufEFADHPwkzt316',
                      notification_queue)
v = VibrationSensor(notification_queue)

_thread.start_new_thread(v.loop_forever, tuple())

cloud.loop_forever()
