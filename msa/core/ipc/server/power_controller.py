# coding: utf-8
import dbus

from msa.core.settings import DBUS_BUSNAME_ARMVE, \
    DBUS_ARMVE_PATH


class DbusPowerController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.connection = self._get_conn_handler()

    def _get_connection(self):
        return self.bus.get_object(DBUS_BUSNAME_ARMVE,
                                   DBUS_ARMVE_PATH)

    def imprimiendo(self):
        dbus_method = self.connection.get_dbus_method('get_power_source')
        return dbus_method()

    def battery_discharging(self, funcion):
        return self.connection.connect_to_signal("battery_discharging",
                                                 funcion)
