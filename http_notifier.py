import machine
import time
import gc
import urequests as requests
from network import WLAN
from config import wifi_config
from notification_queue import NotificationQueue
from machine import Timer


class HttpNotifier():
    def connection_timer_handler(self, alarm):
        if not self._wlan.isconnected():
            print('failed to connect to {}, restarting...'.format(wifi_config['ssid']))
            machine.reset()

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
                    machine.idle()  # save power while waiting
                print('WLAN: connection to {} succeeded!'.format(wifi_config['ssid']))
                print('ifconfig: {}'.format(self._wlan.ifconfig()))
                self._send_props([{'key': 'in_use', 'value': False}])
                break

        # seems like we are still not connected,
        # setup wifi network does not exist ???
        if not self._wlan.isconnected():
            print('failed to connect or specified network does not exist')
            time.sleep(3)
            machine.reset()
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
                time.sleep(3)
                machine.reset()
        else:
            print('RESPONSE: {}...'.format(str(resp.json())[:100]))
            gc.collect()

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

        elif notification.type == NotificationQueue.BATTERY_VOLTAGE:
            self._send_props([{'key': 'battery_voltage', 'value': notification.data}])

        elif notification.type == NotificationQueue.UPTIME:
            self._send_props([{'key': 'uptime', 'value': notification.data}])

        elif notification.type == NotificationQueue.TEMPERATURE:
            self._send_props([{'key': 'temperature', 'value': notification.data}])
        else:
            print('unsupported event {}'.format(notification.type))
