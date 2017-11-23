import time
import gc


class CloudDispatcher:

    def __init__(self, queue, notifiers):
        self._queue = queue
        self._notifiers = notifiers

    def cycle(self):
        notifications = self._queue.pop()

        for n in self._notifiers:
            for e in notifications:
                n.handle_notification(e)
                gc.collect()

    def loop_forever(self):
        while True:
            time.sleep(3)
            self.cycle()
