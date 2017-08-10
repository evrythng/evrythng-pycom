import time
import pycom
import pysense

from machine import Timer
from LIS2HH12 import LIS2HH12
from micropython import const

import cloud

pycom.heartbeat(False)

ps = pysense.Pysense()
print('Pysense HW ver: {}, FW ver: {}'.format(
    ps.read_hw_version(), ps.read_fw_version()))

led_red = (lambda: pycom.rgbled(0x440000))
led_green = (lambda: pycom.rgbled(0x004400))

led_green()

T_v_release = const(2)
T_v_min = const(5)
T_v_last = 0

V_delta = .04
V_detected = False

accel_sensor = LIS2HH12()

chrono = Timer.Chrono()

cloud = cloud.CloudNotifier('UGF4satMBD8atpwawDXK2pXp',
                            'wmioueSdGLwYbRmcqLds2aFW4Rc8haciqtf6aVEaVidb9eP0mFH6hm9SSjIWFk6WxufEFADHPwkzt316')

in_use = False

V_last = (x, y, z) = accel_sensor.acceleration()

while True:
    V_current = (x, y, z) = accel_sensor.acceleration()
    diffs = [(i - j) > V_delta for i, j in zip(V_current, V_last)]

    # print('({0:.2f}, {1:.2f}, {2:.2f})'.format(abs(x), abs(y), abs(z)))

    if any(diffs):
        if not V_detected:
            led_red()
            V_detected = True
            chrono.start()
        T_v_last = chrono.read()

        if T_v_last > T_v_min and not in_use:
            cloud.schedule_inuse_start()
            cloud.notify()
            in_use = True

    elif V_detected:
        t = chrono.read()
        diff = t - T_v_last
        print('last vibration {} sec ago'.format(diff))

        if diff > T_v_release:
            chrono.stop()
            chrono.reset()
            led_green()
            V_detected = False
            in_use = False
            if t - diff > T_v_min:
                print('DETECTED VIBRATION FOR {} SEC (MIN {} SEC)'
                      .format(t - diff, T_v_min))
                cloud.schedule_inuse_stop()
                cloud.schedule_last_use(t - diff)
                cloud.notify()

    V_last = V_current
    time.sleep(.1)
