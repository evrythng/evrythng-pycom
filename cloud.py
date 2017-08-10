import _thread
import time
import urequests as requests
import ujson as json


class CloudNotifier:

    def __init__(self, thng_id, api_key, queue):
        self._queue = queue
        self._thng_id = thng_id
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': api_key}
        self._lock = _thread.allocate_lock()

    def _send_props(self, data):
        print(json.dumps(data))
        resp = requests.put('https://api.evrythng.com/thngs/{}/properties'.format(self._thng_id),
                            headers=self._http_headers, json=data)
        print('{}'.format(resp.json()))

    def _send_actions(self, data):
        print(json.dumps(data))
        for action in data:
            resp = requests.put('https://api.evrythng.com/thngs/{}/actions/{}'.format(self._thng_id, action['type']),
                                headers=self._http_headers, json=data)
            print('{}'.format(resp.json()))

    def cycle(self):
        props = []
        actions = []
        notifications = self._queue.pop()

        for n in notifications:
            if n.type == 'property':
                props.append(n.data)
            elif n.type == 'action':
                actions.append(n.data)

        if props:
            self._send_props(props)

        if actions:
            self._send_actions(props)

    def loop_forever(self):
        while True:
            time.sleep(5)
            self.cycle()
