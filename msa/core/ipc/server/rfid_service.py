#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dbus
import gobject

from base64 import b64decode
from json import dumps

from msa import get_logger
from msa.core.settings import DBUS_BUSNAME_RFID
from msa.core.settings import DBUS_LECTOR_PATH, SCAN_DELAY
from msa.core.ipc.server.dbus_service import MSADbusService
from msa.core.ipc.server.rfid_controller import RFIDController
from serial.serialutil import SerialException


logger = get_logger("core")


class LectorRFID(MSADbusService):

    def __init__(self):
        """Constructor"""
        self.object_path = DBUS_LECTOR_PATH
        self.bus_name = DBUS_BUSNAME_RFID
        self._connection = False
        MSADbusService.__init__(self, True)

    def _real_init(self):
        try:
            self.controller = RFIDController(self.tag_leido)
        except SerialException:
            self.controller = None

        def consula_lector(callback):
            if self.controller is not None:
                self.controller.consulta_lector(callback)
            else:
                try:
                    self.controller = RFIDController(self.tag_leido)
                    self.connection(True)
                except SerialException:
                    self.controller = None
            return True

        gobject.timeout_add(SCAN_DELAY, consula_lector, self.tag_leido)

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def quit(self, w=None):
        """ Cierra el servicio DBUS, útil para casos de reinicio"""
        self.loop_lector = False
        if self._loop.is_running():
            self._loop.quit()

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def read(self):
        tag = self.controller.get_tag()
        return tag

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def get_map(self):
        return self.controller.get_map()

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def write(self, serial, tipo, data, marcar_ro=False):
        data = b64decode(data)
        return self.controller.write(serial, tipo, data, marcar_ro)

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def is_read_only(self, serial):
        return self.controller.is_read_only(serial)

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def set_tipo(self, serial, tipo):
        return self.controller.set_tipo(serial, tipo)

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def ping(self):
        return 'pong'

    @dbus.service.signal(DBUS_BUSNAME_RFID)
    def tag_leido(self, tipo, tag=None):
        logger.debug(tag)
        return tipo, tag

    @dbus.service.signal(DBUS_BUSNAME_RFID)
    def connection(self, state):
        logger.debug("connection: " + str(state))
        return state

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def list_events(self):
        return dumps([])

    @dbus.service.method(DBUS_BUSNAME_RFID)
    def read_metadata(self, out_signature="s"):
        return dumps(self.controller.get_tag_metadata())


if __name__ == '__main__':
    LectorRFID()

