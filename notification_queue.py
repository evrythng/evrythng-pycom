import _thread
from deque import deque
from ucollections import namedtuple

Notification = namedtuple('Notification', 'type data')


class NotificationQueue:
    VIBRATION_STARTED = 1
    VIBRATION_STOPPED = 2
    BATTERY_VOLTAGE = 3
    UPTIME = 4
    TEMPERATURE = 5
    HUMIDITY = 6

    def __init__(self):
        self._deque = deque()
        self._lock = _thread.allocate_lock()

    def _push(self, notification):
        with self._lock:
            self._deque.appendleft(notification)

    def pop(self):
        r = []
        with self._lock:
            while self._deque:
                r.append(self._deque.popright())
        return r

    def push_vibration_started(self):
        self._push(Notification(type=NotificationQueue.VIBRATION_STARTED, data=None))

    def push_vibration_stopped(self, duration):
        self._push(Notification(type=NotificationQueue.VIBRATION_STOPPED, data=int(duration)))

    def push_battery_voltage(self, voltage):
        self._push(Notification(type=NotificationQueue.BATTERY_VOLTAGE, data=voltage))

    def push_uptime(self, uptime_sec):
        # uptime_sec = uptime_ms // 1000
        uptime_hours = uptime_sec // (60 * 60)
        uptime_sec -= uptime_hours * (60 * 60)
        uptime_min = uptime_sec // 60
        uptime_sec -= uptime_min * 60
        self._push(Notification(type=NotificationQueue.UPTIME,
                                data='{}h {}m {}s'.format(uptime_hours, uptime_min, uptime_sec)))

    def push_temperature(self, temperature):
        self._push(Notification(type=NotificationQueue.TEMPERATURE, data=temperature))

    def push_humidity(self, humidity):
        self._push(Notification(type=NotificationQueue.HUMIDITY, data=humidity))

    def __len__(self):
        return len(self._deque)

    def __bool__(self):
        return bool(self._deque)

    def __iter__(self):
        yield from self._deque

    def __str__(self):
        return 'deque({})'.format(self._deque)
