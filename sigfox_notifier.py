from network import Sigfox
from notification_queue import NotificationQueue
import socket
import ubinascii as binascii


class SigfoxNotifier():

    def __init__(self):
        self._sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ2)
        self._socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        self._socket.setblocking(True)
        self._socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
        print('sigfox mac: {}, pac: {}, id: {}'.format(
            binascii.hexlify(self._sigfox.mac()),
            binascii.hexlify(self._sigfox.pac()),
            binascii.hexlify(self._sigfox.id())))

    def handle_notification(self, notification):
        # self._socket.send(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
        if notification.type == NotificationQueue.VIBRATION_STARTED:
            pass
        elif notification.type == NotificationQueue.VIBRATION_STOPPED:
            print('sigfox vibration duration: {}'.format(notification.data))
            self._socket.send(notification.data.to_bytes(8))
        elif NotificationQueue.BATTERY_VOLTAGE:
            pass
        else:
            print('unsupported event {}'.format(notification.type))
