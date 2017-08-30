import machine
import urequests as requests
import ujson as json
from network import WLAN
from config import config
from notification_queue import NotificationQueue
from base_notifier import BaseNotifier


class HttpNotifier(BaseNotifier):
    def __init__(self, thng_id, api_key):
        self._thng_id = thng_id
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': api_key}

        self._wlan = WLAN(mode=WLAN.STA)
        nets = self._wlan.scan()
        wifi_networks = config['known_wifi_networks']

        print('WLAN: scanned networks: {}'.format([net.ssid for net in nets]))

        wifi_networks = config['known_wifi_networks']

        for net in nets:
            if net.ssid in wifi_networks:
                print('WLAN: connecting to {}...'.format(net.ssid))
                self._wlan.connect(net.ssid, auth=(net.sec, wifi_networks[net.ssid]), timeout=5000)
                while not self._wlan.isconnected():
                    machine.idle()  # save power while waiting
                print('WLAN: connection to {} succeeded!'.format(net.ssid))
                print('ifconfig: {}'.format(self._wlan.ifconfig()))
                break

    def _send_props(self, data):
        print(json.dumps(data))
        resp = requests.put('https://api.evrythng.com/thngs/{}/properties'.format(self._thng_id),
                            headers=self._http_headers, json=data)
        try:
            print('{}'.format(resp.json()))
        except ValueError as e:
            print(e)
            pass

    def _send_actions(self, data):
        print(json.dumps(data))
        for action in data:
            resp = requests.post('https://api.evrythng.com/thngs/{}/actions/{}'.format(self._thng_id, action['type']),
                                 headers=self._http_headers, json=action)
            try:
                print('{}'.format(resp.json()))
            except ValueError as e:
                print(e)
                pass

    def handle_notification(self, notification):
        if notification.type == NotificationQueue.VIBRATION_STARTED:
            self._send_props([{'key': 'in_use', 'value': True}])
            self._send_actions([{'type': '_appliance_started'}])
            # pass
        elif notification.type == NotificationQueue.VIBRATION_STOPPED:
            self._send_props([{'key': 'in_use', 'value': False},
                              {'key': 'last_use', 'value': notification.data}])
            #  self._send_props([{'key': 'in_use', 'value': notification.data}])
            self._send_actions([{'type': '_appliance_stopped'}])

        elif notification.type == NotificationQueue.BATTERY_VOLTAGE:
            self._send_props([{'key': 'battery_voltage', 'value': notification.data}])
        else:
            print('unsupported event {}'.format(notification.type))
