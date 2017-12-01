import gc
import led
from time import sleep
from machine import Timer
from LIS2HH12 import LIS2HH12
from micropython import const


class VibrationSensor:

    def __init__(self, queue):
        self._queue = queue
        self._t_v_release = const(4)
        self._t_v_min = const(2)
        self._t_v_last = 0
        self._v_delta = .04
        self._v_detected = False
        self._in_use = False
        self._chrono = Timer.Chrono()
        # to avoid all zeros reading
        self._accel_sensor = LIS2HH12()
        self._accel_sensor.acceleration()
        sleep(.5)
        self._v_last = (x, y, z) = self._accel_sensor.acceleration()
        led.green()

    def cycle(self):
        v_current = (x, y, z) = self._accel_sensor.acceleration()
        # print('({0:.2f}, {1:.2f}, {2:.2f})'.format(abs(x), abs(y), abs(z)))
        diffs = [abs(i - j) > self._v_delta for i, j in zip(v_current, self._v_last)]
        self._v_last = v_current

        if any(diffs):
            if not self._v_detected:
                led.red()
                self._v_detected = True
                self._chrono.start()
            self._t_v_last = self._chrono.read()

            if self._t_v_last > self._t_v_min and not self._in_use:
                self._queue.push_vibration_started()
                self._in_use = True

        elif self._v_detected:
            t = self._chrono.read()
            diff = t - self._t_v_last
            # print('last vibration {} sec ago'.format(diff))

            if diff > self._t_v_release:
                self._chrono.stop()
                self._chrono.reset()
                self._v_detected = False
                self._in_use = False
                led.green()
                if t - diff > self._t_v_min:
                    print('DETECTED VIBRATION FOR {} SEC (MIN {} SEC)'
                          .format(t - diff, self._t_v_min))
                    self._queue.push_vibration_stopped(t - diff)

    def loop_forever(self):
        while True:
            self.cycle()
            sleep(.1)
            gc.collect()
