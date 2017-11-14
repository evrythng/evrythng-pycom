import math
from SI7006A20 import SI7006A20
from MPL3115A2 import MPL3115A2
from machine import Timer


class HumidityTemperatureSensor:
    def __init__(self, queue, temp_period, humidity_period):
        self._dev_hum = SI7006A20()
        self._dev_temp = MPL3115A2()
        self._queue = queue
        self._temp_period = temp_period
        self._humidity_period = humidity_period

        Timer.Alarm(self.temp_timer_handler, temp_period, periodic=True)
        Timer.Alarm(self.humidity_timer_handler, humidity_period, periodic=True)

    def temp_timer_handler(self, alarm):
        self._queue.push_temperature(self._dev_temp.temperature())

    def humidity_timer_handler(self, alarm):
        self._queue.push_humidity(math.floor(self._dev_hum.humidity()))
