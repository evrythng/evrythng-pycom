from network import Sigfox
from notification_queue import NotificationQueue
import socket
import ubinascii as binascii


class SigfoxNotifier():
    V_START = 1
    V_STOP = 2
    VER = 4
    TEMP = 5
    HUM = 6
    PRES = 7
    VOLT = 8

    def __init__(self):
        self._sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
        self._socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        self._socket.setblocking(True)
        self._socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
        print('sigfox mac: {}, pac: {}, id: {}'.format(
            binascii.hexlify(self._sigfox.mac()),
            binascii.hexlify(self._sigfox.pac()),
            binascii.hexlify(self._sigfox.id())))

    def handle_notifications(self, notifications):
        # self._socket.send(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
        msg = bytearray()
        for n in notifications:
            if n.type == NotificationQueue.VIBRATION_STARTED:
                msg.append(self.V_START)
                print(msg)
                self._socket.send(msg)

            elif n.type == NotificationQueue.VIBRATION_STOPPED:
                msg.append(self.V_STOP)
                msg.extend(n.data.to_bytes(8, 'little'))
                print(msg)
                self._socket.send(msg)

            elif n.type == NotificationQueue.AMBIENT:
                print(n.data)
                msg.append(self.TEMP)
                msg.extend(int(n.data[0]).to_bytes(8, 'little'))
                print(msg)
                self._socket.send(msg)
                '''
                t = zip((self.TEMP, self.HUM, self.PRES, self.VOLT), n.data)
                for a, b in t:
                    msg.append(a)
                    msg.extend(int(b).to_bytes(8, 'little'))
                    print(msg)
                    self._socket.send(msg)
                    msg = bytearray()
                '''
            else:
                print('unsupported event {}'.format(n.type))

            msg = bytearray()
