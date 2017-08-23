import time
import pycom
import pysense
import _thread
import machine

from config import config
from network import WLAN
from micropython import const
from cloud_notifier import CloudNotifier
from notification_queue import NotificationQueue
from accelerometer_sensor import VibrationSensor
# from adc_sensor import VibrationSensor

pycom.heartbeat(False)

wlan = WLAN(mode=WLAN.STA)
nets = wlan.scan()
wifi_networks = config['known_wifi_networks']

for net in nets:
    if net.ssid in wifi_networks:
        print('WLAN: connecting to {}...'.format(net.ssid))
        wlan.connect(net.ssid, auth=(net.sec, wifi_networks[net.ssid]), timeout=5000)
        while not wlan.isconnected():
            machine.idle()  # save power while waiting
        print('WLAN: connection to {} succeeded!'.format(net.ssid))
        break


ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

cloud_settings = config['cloud_settings']
notification_queue = NotificationQueue()
cloud = CloudNotifier(cloud_settings['thng_id'],
                      cloud_settings['api_key'],
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
