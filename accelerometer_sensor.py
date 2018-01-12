import gc
import led
import _thread
from time import sleep
from machine import Timer
from LIS2HH12 import LIS2HH12
from micropython import const


class VibrationSensor:

    def __init__(self, queue, pys):
        self._pysense = pys
        self._queue = queue
        self._t_v_release = const(3)
        self._t_v_min = const(.1)
        self._t_v_last = 0
        self._v_delta = .04
        self._v_detected = False
        self._in_use = False
        self._vibration_chrono = Timer.Chrono()
        self._inactivity_chrono = Timer.Chrono()
        # to avoid all zeros reading
        self._accel_sensor = LIS2HH12(pysense=self._pysense)
        self._accel_sensor.acceleration()
        sleep(.2)
        self._v_last = (x, y, z) = self._accel_sensor.acceleration()
        self._magnitudes = []
        self._minutes = 1
        self._running = False

    def enable_activity_wakeup(self):
        # self._pysense.setup_int_pin_wake_up(False)
        self._pysense.setup_int_wake_up(True, False)
        self._accel_sensor.enable_activity_interrupt(50, 20)  # mG, ms

    def cycle(self):
        v_current = (x, y, z) = self._accel_sensor.acceleration()
        # print('({0:.2f}, {1:.2f}, {2:.2f})'.format(abs(x), abs(y), abs(z)))
        pairs = zip(v_current, self._v_last)
        diffs = [abs(i - j) for i, j in pairs]
        flags = [i > self._v_delta for i in diffs]

        if any(flags):
            if not self._v_detected:
                led.red()
                self._minutes = 1
                self._v_detected = True
                self._vibration_chrono.start()
                self._magnitudes[:] = []
                self._magnitudes.append((0, self._v_last[0],
                                         self._v_last[1],
                                         self._v_last[2]))
            self._t_v_last = self._vibration_chrono.read()

            t = (self._vibration_chrono.read(), x, y, z)
            # print('t:{}, x:{}, y:{}, z:{}'.format(t[0], t[1], t[2], t[3]))
            self._magnitudes.append(t)
            if (t[0] > 60 * self._minutes):  # send magnitudes each 60 seconds to avoid overflow
                self._queue.push_mangnitudes(self._magnitudes)
                self._magnitudes[:] = []
                self._minutes += 1

            if self._t_v_last > self._t_v_min and not self._in_use:
                self._queue.push_vibration_started()
                self._in_use = True

            self._inactivity_chrono.reset()

        elif self._v_detected:
            t = self._vibration_chrono.read()
            diff = t - self._t_v_last
            # print('last vibration {} sec ago'.format(diff))

            if diff > self._t_v_release:
                self._vibration_chrono.stop()
                self._vibration_chrono.reset()
                self._v_detected = False
                self._in_use = False
                led.off()
                if t - diff > self._t_v_min:
                    print('DETECTED VIBRATION FOR {} SEC (MIN {} SEC)'
                          .format(t - diff, self._t_v_min))
                    self._queue.push_vibration_stopped(t - diff)
                    self._queue.push_mangnitudes(self._magnitudes)

        self._v_last = v_current

    def loop_while_inuse(self):
        self._running = True
        self._inactivity_chrono.start()
        while True:
            self.cycle()
            sleep(.1)
            gc.collect()
            print('inactivity: {}'.format(self._inactivity_chrono.read()))
            if self._inactivity_chrono.read() > 5 and not self._in_use and not self._v_detected:
                print('exiting')
                break
        self._running = False

    def launch_in_thread(self):
        self._running = True
        _thread.start_new_thread(self.loop_while_inuse, tuple())

    def is_running(self):
        return self._running
