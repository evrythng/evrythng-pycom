from pysense import Pysense
from MPL3115A2 import MPL3115A2
from SI7006A20 import SI7006A20


class AmbientSensor:
    def __init__(self, queue, pys):
        # self._ps = Pysense()
        self._ps = pys
        self._dev_mpl = MPL3115A2(pysense=self._ps)
        self._dev_si = SI7006A20(pysense=self._ps)
        self._queue = queue
        self._temp_calib = 5
        # Timer.Alarm(self._timer_handler, period, periodic=True)

    def push_sensor_values(self):
        # temp_sensor = self._dev_si.temperature()
        temp_sensor = self._dev_mpl.temperature()
        pressure_sensor = self._dev_mpl.pressure()
        temp_calib = temp_sensor - self._temp_calib
        humidity_calib = self._dev_si.humid_ambient(temp_calib)
        self._queue.push_ambient(temp_calib,
                                 humidity_calib,
                                 pressure_sensor,
                                 self._ps.read_battery_voltage())
