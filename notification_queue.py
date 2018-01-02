import ujson
import utime
from _thread import allocate_lock
from deque import deque
from ucollections import namedtuple
from machine import RTC

Notification = namedtuple('Notification', 'type data timestamp')


class NotificationQueue:
    VIBRATION_STARTED = 1
    VIBRATION_STOPPED = 2
    UPTIME = 3
    AMBIENT = 4
    VERSION = 5
    MAGNITUDE = 6

    def __init__(self):
        self._deque = deque()
        self._lock = allocate_lock()
        self._rtc = RTC()

    def _push(self, notification):
        with self._lock:
            self._deque.appendleft(notification)

    def pop(self):
        r = []
        with self._lock:
            while self._deque:
                r.append(self._deque.popright())
        return r

    def timestamp(self):
        sec = utime.time()
        usec = self._rtc.now()[6]
        # print('{} {} {}'.format(sec, usec, sec * 1000 + int(usec / 1000)))
        return sec * 1000 + int(usec / 1000)

    def push_vibration_started(self):
        self._push(Notification(type=NotificationQueue.VIBRATION_STARTED,
                                data=None,
                                timestamp=self.timestamp()))

    def push_vibration_stopped(self, duration):
        self._push(Notification(type=NotificationQueue.VIBRATION_STOPPED,
                                data=int(duration),
                                timestamp=self.timestamp()))

    def push_version(self, version):
        self._push(Notification(type=NotificationQueue.VERSION,
                                data=version,
                                timestamp=self.timestamp()))

    def push_uptime(self, uptime_sec):
        # uptime_sec = uptime_ms // 1000
        uptime_hours = uptime_sec // (60 * 60)
        uptime_sec -= uptime_hours * (60 * 60)
        uptime_min = uptime_sec // 60
        uptime_sec -= uptime_min * 60
        self._push(Notification(type=NotificationQueue.UPTIME,
                                data='{}h {}m {}s'.format(uptime_hours, uptime_min, uptime_sec),
                                timestamp=self.timestamp()))

    def push_ambient(self, temperature, humidity, pressure, voltage):
        self._push(Notification(type=NotificationQueue.AMBIENT,
                                data=(temperature, humidity, pressure, voltage),
                                timestamp=self.timestamp()))

    def push_mangnitudes(self, magnitudes):
        if not magnitudes:
            return
        self._push(Notification(type=NotificationQueue.MAGNITUDE,
                                data=ujson.dumps(magnitudes),
                                timestamp=self.timestamp()))

    def __len__(self):
        return len(self._deque)

    def __bool__(self):
        return bool(self._deque)

    def __iter__(self):
        yield from self._deque

    def __str__(self):
        return 'deque({})'.format(self._deque)
