# coding: utf-8
import dbus

from tempfile import NamedTemporaryFile

from msa.core.settings import DBUS_BUSNAME_ARMVE, DBUS_ARMVE_PATH
from msa.core.imaging import get_dpi_boletas


class DbusBatteryController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.conn = self._get_connection()

    def _get_connection(self):
        return self.bus.get_object(DBUS_BUSNAME_ARMVE,
                                   DBUS_ARMVE_PATH)

    def get_power_source(self):
        dbus_method = self.conn.get_dbus_method('get_power_source')
        return dbus_method()

    def battery_discharging(self, funcion):
        return self.conn.connect_to_signal("battery_discharging", funcion)

