import machine
from machine import Timer
from machine import Pin


class ResetButton:

    def __init__(self, pin):
        self._pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_DOWN)
        self._pin.callback(Pin.IRQ_RISING, self._pin_handler)
        self._alarm = None
        self._alarm_step = .2
        self._alarm_thres = 3
        self._pressed = 0

    def _press_handler(self, alarm):
        # if button is still pressed
        if self._pin():
            self._pressed += self._alarm_step
            print('pressed for {} seconds already'.format(self._pressed))
            if self._pressed >= self._alarm_thres:
                self._pressed = 0
                alarm.cancel()
                print('PROVISIONING MODE ACTIVATED')
        else:
            self._pressed = 0
            alarm.cancel()
            machine.reset()

    def _pin_handler(self, pin):
        # print('got an interrupt on pin {}, value {}'.format(pin.id(), pin.value()))
        if pin.value():
            self._pressed = 0
            if self._alarm:
                self._alarm.cancel()
            self._alarm = Timer.Alarm(self._press_handler, self._alarm_step, periodic=True)
