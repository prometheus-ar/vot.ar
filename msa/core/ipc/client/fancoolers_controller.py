# coding: utf-8
import dbus

from msa.core.settings import DBUS_BUSNAME_FANCOOLERS, DBUS_FANCOOLERS_PATH


class DbusFanCoolersController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.fancoolers = self._get_fancoolers()

    def _get_fancoolers(self):
        return self.bus.get_object(DBUS_BUSNAME_FANCOOLERS,
                                   DBUS_FANCOOLERS_PATH)

    def get_fan_speed(self):
        get_fan_speed = self.fancoolers.get_dbus_method("get_fan_speed")
        return get_fan_speed()

    def set_fan_speed(self, value):
        set_fan_speed = self.fancoolers.get_dbus_method("set_fan_speed")
        return set_fan_speed(value)

    def get_fan_mode(self):
        get_fan_mode = self.fancoolers.get_dbus_method("get_fan_mode")
        return get_fan_mode()

    def set_fan_auto_mode(self, value):
        set_fan_auto_mode = self.fancoolers.get_dbus_method(
            "set_fan_auto_mode")
        return set_fan_auto_mode(value)
