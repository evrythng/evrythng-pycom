from network import Sigfox
from notification_queue import NotificationQueue
import socket
import ubinascii as binascii


class SigfoxNotifier():
    def __init__(self):
        self._sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
        self._socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        self._socket.setblocking(True)
        self._socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
        self._temp = 0
        self._last_use = 0
        self._in_use = False
        print('sigfox mac: {}, pac: {}, id: {}'.format(
            binascii.hexlify(self._sigfox.mac()),
            binascii.hexlify(self._sigfox.pac()),
            binascii.hexlify(self._sigfox.id())))

    def handle_notifications(self, notifications):
        for n in notifications:
            msg = bytearray()
            self._last_use = 0
            if n.type == NotificationQueue.VIBRATION_STARTED:
                self._in_use = True

            elif n.type == NotificationQueue.VIBRATION_STOPPED:
                self._in_use = False
                self._last_use = n.data

            elif n.type == NotificationQueue.AMBIENT:
                self._temp = int(n.data[0])

            else:
                print('unsupported event {}'.format(n.type))
                continue

            msg.append(self._in_use)
            msg.extend(self._last_use.to_bytes(4, 'little'))
            msg.extend(self._temp.to_bytes(4, 'little'))
            print(list(msg))
            self._socket.send(msg)
