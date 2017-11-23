from MPL3115A2 import MPL3115A2
from machine import Timer


class TemperatureSensor:
    def __init__(self, queue, temp_period):
        self._dev = MPL3115A2()
        self._queue = queue
        self._temp_period = temp_period
        Timer.Alarm(self.temp_timer_handler, temp_period, periodic=True)

    def temp_timer_handler(self, alarm):
        self._queue.push_temperature(self._dev.temperature())
