import _thread
from deque import deque
from ucollections import namedtuple

Notification = namedtuple('Notification', 'type data')


class NotificationQueue:

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

    def push_in_use_property(self, in_use):
        self._push(Notification('property', {'key': 'in_use', 'value': in_use}))

    def push_vbat_property(self, vbat):
        self._push(Notification('property', {'key': 'battery_voltage', 'value': vbat}))

    def push_in_use_action(self, in_use):
        self._push(Notification('action',
                                {'type': '_appliance_started'
                                    if in_use
                                    else '_appliance_stopped'}))

    def push_last_use_property(self, sec):
        self._push(Notification('property', {'key': 'last_use', 'value': sec}))

    def __len__(self):
        return len(self._deque)

    def __bool__(self):
        return bool(self._deque)

    def __iter__(self):
        yield from self._deque

    def __str__(self):
        return 'deque({})'.format(self._deque)
