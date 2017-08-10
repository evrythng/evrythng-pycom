import _thread
import time
import urequests as requests
import ujson as json
from deque import deque


class CloudNotifier:

    def __init__(self, thng_id, api_key):
        self._deque = deque()
        self._thng_id = thng_id
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': api_key}
        self._lock = _thread.allocate_lock()
        #self._thread_id = _thread.start_new_thread(self.thread_func, tuple())

    def schedule_inuse_start(self):
        with self._lock:
            self._deque.appendleft({'key': 'in_use', 'value': True})

    def schedule_inuse_stop(self):
        with self._lock:
            self._deque.appendleft({'key': 'in_use', 'value': False})

    def schedule_last_use(self, sec):
        with self._lock:
            self._deque.appendleft({'key': 'last_use_sec', 'value': sec})

    def thread_func(self):
        while True:
            time.sleep(5)
            data = []

            with self._lock:
                while self._deque:
                    data.append(self._deque.popright())

            if not data:
                continue

            print(json.dumps(data))

            resp = requests.put('https://api.evrythng.com/thngs/{}/properties'.format(self._thng_id),
                                headers=self._http_headers, json=data)
            print('{}'.format(resp.json()))
