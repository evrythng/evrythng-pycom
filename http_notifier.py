
import time
import urequests as requests
from gc import collect as gc_collect
from network import WLAN
from config import wifi_config
from notification_queue import NotificationQueue
from machine import Timer, reset, idle, RTC


class HttpNotifier():
    def connection_timer_handler(self, alarm):
        if not self._wlan.isconnected():
            print('failed to connect to {}, restarting...'.format(wifi_config['ssid']))
            reset()

    def sync_timer_handler(self, alarm):
        if not self._rtc.synced():
            print('failed to sync time with ntp, restarting...')
            reset()

    def __init__(self, thng_id, api_key):
        self._thng_id = thng_id
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': api_key}
        self._rtc = RTC()

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

                Timer.Alarm(self.sync_timer_handler, 30, periodic=False)
                while not self._rtc.synced():
                    self._rtc.ntp_sync('pool.ntp.org', update_period=3600)
                    time.sleep(1)
                print("time synced: {}".format(self._rtc.now()))

        # seems like we are still not connected,
        # setup wifi network does not exist ???
        if not self._wlan.isconnected():
            print('failed to connect or specified network does not exist')
            time.sleep(20)
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
                time.sleep(3)
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
                       url='https://api.evrythng.com/thngs/{}/actions/all'.format(self._thng_id),
                       json=action)

    def handle_notifications(self, notifications):
        properties = []
        actions = []
        for n in notifications:
            if n.type == NotificationQueue.VIBRATION_STARTED:
                properties.append({'key': 'in_use', 'value': True, 'timestamp': n.timestamp})
                actions.append({'type': '_appliance_started', 'timestamp': n.timestamp})

            elif n.type == NotificationQueue.VIBRATION_STOPPED:
                properties.extend([{'key': 'in_use', 'value': False, 'timestamp': n.timestamp},
                                   {'key': 'last_use', 'value': n.data, 'timestamp': n.timestamp}])
                actions.append({'type': '_appliance_stopped', 'timestamp': n.timestamp})

            elif n.type == NotificationQueue.UPTIME:
                properties.append({'key': 'uptime', 'value': n.data, 'timestamp': n.timestamp})

            elif n.type == NotificationQueue.AMBIENT:
                properties.extend([
                    {'key': 'temperature', 'value': n.data[0], 'timestamp': n.timestamp},
                    {'key': 'humidity', 'value': n.data[1], 'timestamp': n.timestamp},
                    {'key': 'pressure', 'value': n.data[2], 'timestamp': n.timestamp},
                    {'key': 'battery_voltage', 'value': n.data[3], 'timestamp': n.timestamp}
                ])

            elif n.type == NotificationQueue.VERSION:
                properties.append({'key': 'version', 'value': n.data, 'timestamp': n.timestamp})

            elif n.type == NotificationQueue.MAGNITUDE:
                if not len(n.data):
                    return
                properties.append({'key': 'magnitude', 'value': n.data, 'timestamp': n.timestamp})

            else:
                print('unsupported event {}'.format(n.type))

        if actions:
            self._send_actions(actions)
        if properties:
            self._send_props(properties)
