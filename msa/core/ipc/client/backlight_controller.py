# coding: utf-8
import dbus

from msa.core.settings import DBUS_BUSNAME_BACKLIGHT, DBUS_BACKLIGHT_PATH


class DbusBacklightController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.backlight = self._get_backlight()

    def _get_backlight(self):
        return self.bus.get_object(DBUS_BUSNAME_BACKLIGHT,
                                   DBUS_BACKLIGHT_PATH)

    def get_brightness(self):
        get_brightness = self.backlight.get_dbus_method("get_brightness")
        return get_brightness()

    def set_brightness(self, value):
        set_brightness = self.backlight.get_dbus_method("set_brightness")
        return set_brightness(value)
