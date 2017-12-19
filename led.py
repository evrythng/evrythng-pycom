import pycom
import time
from machine import Timer

RGB_BLUE = 0x0000FF
RGB_GREEN = 0x00FF00
RGB_RED = 0xFF0000

rgbled_color = 0x000000
rgbled_value = 0x000000

heartbeat_disabled = False
alarm = None


def disable_heartbeat():
    global heartbeat_disabled
    if not heartbeat_disabled:
        pycom.heartbeat(False)
        time.sleep(.1)
        heartbeat_disabled = True


def _led_timer(alarm):
    global rgbled_value
    rgbled_value ^= rgbled_color
    pycom.rgbled(rgbled_value)


def blink(period, color):
    global rgbled_color
    global alarm

    disable_heartbeat()
    rgbled_color = color
    if alarm:
        alarm.cancel()
    alarm = Timer.Alarm(_led_timer, period, periodic=True)


def solid(color):
    disable_heartbeat()
    if alarm:
        alarm.cancel()
    pycom.rgbled(color)


def blink_blue(period=0.5):
    blink(period, RGB_BLUE)


def blink_red(period=0.5):
    blink(period, RGB_RED)


def green():
    solid(RGB_GREEN)


def red():
    solid(RGB_RED)
