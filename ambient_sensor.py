import math
from MPL3115A2 import MPL3115A2
from SI7006A20 import SI7006A20
from machine import Timer


class AmbientSensor:
    def __init__(self, queue, period):
        self._dev_mpl = MPL3115A2()
        self._dev_si = SI7006A20()
        self._queue = queue
        self._period = period
        self._temp_calib = 5.5
        Timer.Alarm(self._timer_handler, period, periodic=True)

    def _timer_handler(self, alarm):
        # temp_sensor = self._dev_si.temperature()
        temp_sensor = self._dev_mpl.temperature()
        humidity_sensor = self._dev_si.humidity()
        pressure_sensor = self._dev_mpl.pressure()
        temp_calib = temp_sensor - self._temp_calib
        humidity_calib = humidity_sensor / (math.pow(.95, self._temp_calib))
        self._queue.push_ambient(temp_calib, humidity_calib, pressure_sensor)
