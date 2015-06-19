# coding: utf-8
import dbus

from json import loads

from msa.core.settings import DBUS_BUSNAME_PIR, DBUS_PIR_PATH


class DbusPIRController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.pir = self._get_pir()
        self._signal_detected = self.register_detected()
        self._callback_detected = None
        self._signal_not_detected = self.register_not_detected()
        self._callback_not_detected = None

    def _get_pir(self):
        return self.bus.get_object(DBUS_BUSNAME_PIR,
                                   DBUS_PIR_PATH)

    def get_pir_status(self):
        get_pir_status = self.pir.get_dbus_method("get_pir_status")
        status = loads(get_pir_status())
        return status

    def check_detected(self, function):
        self._callback_detected = function

    def register_detected(self):
        self._signal_detected = \
            self.pir.connect_to_signal("pir_detected", self.status_detected)
        return self._signal_detected

    def status_detected(self):
        if self._callback_detected is not None:
            self._callback_detected()

    def uncheck_detected(self):
        self._callback_detected = None

    def deregister_detected(self):
        if self._signal_detected is not None:
            self._signal_detected.remove()
            self._signal_detecte = None

    def check_not_detected(self, function):
        self._callback_not_detected = function

    def register_not_detected(self):
        self._signal_not_detected = \
            self.pir.connect_to_signal("pir_not_detected",
                                       self.status_not_detected)
        return self._signal_not_detected

    def status_not_detected(self):
        if self._callback_not_detected is not None:
            self._callback_not_detected()

    def uncheck_not_detected(self):
        self._callback_not_detected = None

    def deregister_not_detected(self):
        if self._signal_not_detected is not None:
            self._signal_not_detected.remove()
            self._signal_not_detected = None

    def get_pir_mode(self):
        get_pir_mode = self.pir.get_dbus_method("get_pir_mode")
        return get_pir_mode()

    def set_pir_mode(self, mode):
        set_pir_mode = self.pir.get_dbus_method("set_pir_mode")
        return set_pir_mode(mode)
