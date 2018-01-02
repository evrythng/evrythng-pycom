from _thread import allocate_lock
from deque import deque
from ucollections import namedtuple

Notification = namedtuple('Notification', 'type data')


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

    def push_version(self, version):
        self._push(Notification(type=NotificationQueue.VERSION, data=version))

    def push_uptime(self, uptime_sec):
        # uptime_sec = uptime_ms // 1000
        uptime_hours = uptime_sec // (60 * 60)
        uptime_sec -= uptime_hours * (60 * 60)
        uptime_min = uptime_sec // 60
        uptime_sec -= uptime_min * 60
        self._push(Notification(type=NotificationQueue.UPTIME,
                                data='{}h {}m {}s'.format(uptime_hours, uptime_min, uptime_sec)))

    def push_ambient(self, temperature, humidity, pressure, voltage):
        self._push(Notification(type=NotificationQueue.AMBIENT,
                                data=(temperature, humidity, pressure, voltage)))

    def push_mangnitudes(self, mangitudes):
        self._push(Notification(type=NotificationQueue.MAGNITUDE,
                                data=mangitudes))

    def __len__(self):
        return len(self._deque)

    def __bool__(self):
        return bool(self._deque)

    def __iter__(self):
        yield from self._deque

    def __str__(self):
        return 'deque({})'.format(self._deque)
