import pycom
import time
import machine
from machine import Timer
from micropython import const

led_red = (lambda: pycom.rgbled(0x440000))
led_green = (lambda: pycom.rgbled(0x004400))


class VibrationSensor:

    def __init__(self, queue):
        self._queue = queue
        self._t_v_release = const(5)
        self._t_v_min = const(2)
        self._t_v_last = 0
        self._v_delta = .03
        self._v_detected = False
        self._in_use = False
        self._chrono = Timer.Chrono()
        self._adc = machine.ADC()
        self._adc.init(bits=12)
        self._adc_channel = self._adc.channel(pin='P20', attn=machine.ADC.ATTN_11DB)
        led_green()

    def cycle(self):
        v_current = self._adc_channel.value()
        self._v_last = v_current

        if v_current > 0:
            print('adc value = {0:.2f}, V = {1:.2f}'.format(v_current, (v_current * 3.3) / 4096))

        if self._v_last > 10000:
            if not self._v_detected:
                led_red()
                self._v_detected = True
                self._chrono.start()
            self._t_v_last = self._chrono.read()

            if self._t_v_last > self._t_v_min and not self._in_use:
                self._queue.push_in_use_property(True)
                self._queue.push_in_use_action(True)
                self._in_use = True

        elif self._v_detected:
            t = self._chrono.read()
            diff = t - self._t_v_last
            print('last vibration {} sec ago'.format(diff))

            if diff > self._t_v_release:
                self._chrono.stop()
                self._chrono.reset()
                self._v_detected = False
                self._in_use = False
                led_green()
                if t - diff > self._t_v_min:
                    print('DETECTED VIBRATION FOR {} SEC (MIN {} SEC)'
                          .format(t - diff, self._t_v_min))
                    self._queue.push_in_use_property(False)
                    self._queue.push_last_use_property(t - diff)
                    self._queue.push_in_use_action(False)

    def loop_forever(self):
        while True:
            self.cycle()
            time.sleep(.01)
