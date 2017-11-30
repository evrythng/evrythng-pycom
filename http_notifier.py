import urequests as requests
from gc import collect as gc_collect
from time import sleep
from network import WLAN
from config import wifi_config
from notification_queue import NotificationQueue
from machine import Timer, reset, idle


class HttpNotifier():
    def connection_timer_handler(self, alarm):
        if not self._wlan.isconnected():
            print('failed to connect to {}, restarting...'.format(wifi_config['ssid']))
            reset()

    def __init__(self, thng_id, api_key):
        self._thng_id = thng_id
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': api_key}

        self._wlan = WLAN(mode=WLAN.STA)
        nets = self._wlan.scan()

        print('WLAN: scanned networks: {}'.format([net.ssid for net in nets]))

        for net in nets:
            if net.ssid == wifi_config['ssid']:
                print('WLAN: connecting to {}...'.format(net.ssid))
                self._wlan.connect(wifi_config['ssid'], auth=(
                    net.sec, wifi_config['passphrase']), timeout=30000)
                Timer.Alarm(self.connection_timer_handler, 35, periodic=False)
                while not self._wlan.isconnected():
                    idle()  # save power while waiting
                print('WLAN: connection to {} succeeded!'.format(wifi_config['ssid']))
                print('ifconfig: {}'.format(self._wlan.ifconfig()))
                self._send_props([{'key': 'in_use', 'value': False}])
                break

        # seems like we are still not connected,
        # setup wifi network does not exist ???
        if not self._wlan.isconnected():
            print('failed to connect or specified network does not exist')
            sleep(20)
            reset()
            # provision.enter_provisioning_mode()

    def _send(self, method, url, json):
        print('REQUEST: {}: {}'.format(method, json))
        try:
            resp = requests.request(method=method,
                                    url=url,
                                    json=json,
                                    headers=self._http_headers)
        except OSError as e:
            print('RESPONSE: failed to perform request: {}'.format(e))
            if not self._wlan.isconnected():
                print('wifi connection lost, restarting...')
                sleep(3)
                reset()
        else:
            print('RESPONSE: {}...'.format(str(resp.json())[:100]))
            gc_collect()

    def _send_props(self, data):
        self._send(method='PUT',
                   url='https://api.evrythng.com/thngs/{}/properties'.format(self._thng_id),
                   json=data)

    def _send_actions(self, data):
        for action in data:
            self._send(method='POST',
                       url='https://api.evrythng.com/thngs/{}/actions/{}'.format(
                           self._thng_id, action['type']),
                       json=action)

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

        elif notification.type == NotificationQueue.UPTIME:
            self._send_props([{'key': 'uptime', 'value': notification.data}])

        elif notification.type == NotificationQueue.AMBIENT:
            self._send_props([
                {'key': 'temperature', 'value': notification.data[0]},
                {'key': 'humidity', 'value': notification.data[1]},
                {'key': 'pressure', 'value': notification.data[2]}
            ])

        elif notification.type == NotificationQueue.VERSION:
            self._send_props([{'key': 'installed_version', 'value': notification.data}])

        else:
            print('unsupported event {}'.format(notification.type))
