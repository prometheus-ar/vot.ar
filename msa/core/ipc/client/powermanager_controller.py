# coding: utf-8
import dbus

from msa.core.settings import DBUS_BUSNAME_POWERMANAGER, DBUS_POWERMANAGER_PATH


class DbusPowerManagerController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.powermanager = self._get_powermanager()
        self._signal_ac = self.register_switch_ac()
        self._callback_ac = None
        self._signal_batt_discharging = self.register_battery_discharging()
        self._callback_batt_discharging = None
        self._signal_batt_plugged = self.register_battery_plugged()
        self._callback_batt_plugged = None
        self._signal_batt_unplugged = self.register_battery_unplugged()
        self._callback_batt_unplugged = None

    def _get_powermanager(self):
        return self.bus.get_object(DBUS_BUSNAME_POWERMANAGER,
                                   DBUS_POWERMANAGER_PATH)

    def get_power_status(self):
        get_power_status = \
            self.powermanager.get_dbus_method("get_power_status")
        return get_power_status()

    def get_power_source(self):
        get_power_source = self.powermanager.get_dbus_method(
            "get_power_source")
        return get_power_source()

    def check_ac(self, function):
        self._callback_ac = function

    def register_switch_ac(self):
        self._signal_ac = \
            self.powermanager.connect_to_signal("switch_ac",
                                                self.switch_ac_status)
        return self._signal_ac

    def switch_ac_status(self):
        if self._callback_ac is not None:
            self._callback_ac()

    def uncheck_ac(self):
        self._callback_ac = None

    def deregister_switch_ac(self):
        if self._signal_ac is not None:
            self._signal_ac.remove()
            self._signal_ac = None

    def check_battery_discharging(self, function):
        self._callback_batt_discharging = function

    def register_battery_discharging(self):
        self._signal_batt_discharging = \
            self.powermanager.connect_to_signal("battery_discharging",
                                                self.battery_discharging_status)
        return self._signal_batt_discharging

    def battery_discharging_status(self):
        if self._callback_batt_discharging is not None:
            self._callback_batt_discharging()

    def uncheck_battery_discharging(self):
        self._callback_batt_discharging = None

    def deregister_battery_discharging(self):
        if self._signal_batt_discharging is not None:
            self._signal_batt_discharging.remove()
            self._signal_batt_discharging = None

    def check_battery_plugged(self, function):
        self._callback_batt_plugged = function

    def register_battery_plugged(self):
        self._signal_batt_plugged = \
            self.powermanager.connect_to_signal("battery_plugged",
                                                self.battery_plugged_status)
        return self._signal_batt_plugged

    def battery_plugged_status(self):
        if self._callback_batt_plugged is not None:
            self._callback_batt_plugged()

    def uncheck_battery_plugged(self):
        self._callback_batt_plugged = None

    def deregister_battery_plugged(self):
        if self._signal_batt_plugged is not None:
            self._signal_batt_plugged.remove()
            self._signal_batt_plugged = None

    def check_battery_unplugged(self, function):
        self._callback_batt_unplugged = function

    def register_battery_unplugged(self):
        self._signal_batt_unplugged = \
            self.powermanager.connect_to_signal("battery_unplugged",
                                                self.battery_unplugged_status)
        return self._signal_batt_unplugged

    def battery_unplugged_status(self):
        if self._callback_batt_unplugged is not None:
            self._callback_batt_unplugged()

    def uncheck_battery_unplugged(self):
        self._callback_batt_unplugged = None

    def deregister_battery_unplugged(self):
        if self._signal_batt_unplugged is not None:
            self._signal_batt_unplugged.remove()
            self._signal_batt_unplugged = None
