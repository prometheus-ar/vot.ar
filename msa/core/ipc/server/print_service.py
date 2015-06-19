#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import gobject

from base64 import b64encode
from os import system

from msa import get_logger
from msa.core.ipc.server.dbus_service import MSADbusService
from msa.core.serial.printer import obtener_impresora
from msa.core.settings import DBUS_IMPRESORA_PATH, DBUS_BUSNAME_PRINTER, \
    SCAN_DELAY, PATH_IPC_SERVER
from msa.helpers import levantar_locales


levantar_locales()
logger = get_logger("print_service")


class PrinterDBus(MSADbusService):

    def __init__(self):
        """Constructor"""
        self.object_path = DBUS_IMPRESORA_PATH
        self.bus_name = DBUS_BUSNAME_PRINTER
        self._conn = False
        MSADbusService.__init__(self, True)

    def _real_init(self):
        self.ultimo_estado_tarjeta = None
        self.printer = obtener_impresora()

        def _tarjeta_ingresada(callback):
            try:
                ingresada = self.printer.tarjeta_ingresada()
                if not self._conn:
                    self.connection(True)
                    self._conn = True
                if ingresada is None:
                    ingresada = False
                if ingresada != self.ultimo_estado_tarjeta:
                    self.ultimo_estado_tarjeta = ingresada
                    callback(self.full_paper_status())
            # si falla viendo si hay papel o no asumimos que la impresora esta
            # desconectada
            except Exception, e:
                if self._conn:
                    self._conn = False
                    self.connection(False)
            return True
        gobject.timeout_add(SCAN_DELAY, _tarjeta_ingresada,
                            self.insertando_papel)

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def quit(self):
        """ Cierra el servicio DBUS, útil para casos de reinicio"""
        if self._loop.is_running():
            self._loop.quit()

    def _info(self, func):
        logger.info("llamando a %s" % func)

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def imprimiendo(self):
        self._info("imprimiendo")
        return self.printer.imprimiendo()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def get_type(self):
        self._info("get_type")
        return self.printer.get_type()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def get_vendor(self):
        self._info("get_vendor")
        return self.printer.get_vendor()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def linefeed(self, n):
        self._info("linefeed")
        return self.printer.linefeed(n)

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def backfeed(self, n):
        self._info("backfeed")
        return self.printer.backfeed(n)

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def expulsar_boleta(self):
        self._info("expulsar_boleta")
        self.printer.expulsar_boleta()
        self.boleta_expulsada()

    @dbus.service.signal(DBUS_BUSNAME_PRINTER)
    def boleta_expulsada(self):
        self._info("boleta_expulsada")
        return None

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def tomar_tarjeta(self, loops):
        self._info("tomar_tarjeta")
        #dbus no permite pasar None, entonces paso False y convierto
        if not loops:
            loops = None
        return self.printer.tomar_tarjeta(loops)

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def posicionar_al_inicio(self):
        self._info("posicionar_al_inicio")
        return self.printer.posicionar_al_inicio()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def limpiar_cola(self):
        self._info("limpiar_cola")
        return self.printer.limpiar_cola()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def imprimir_image(self, filepath, mode, size, dpi, transpose, compress,
                       only_buffer):
        self._info("imprimir_image")
        size = ",".join([str(num) for num in size])
        dpi = ",".join([str(num) for num in dpi])
        command = "%s/print_or_cache.py" % PATH_IPC_SERVER
        args = "--filepath %s --mode %s --size %s --dpi %s " % (filepath, mode,
                                                                size, dpi)
        if transpose:
            args += "--transpose "

        if only_buffer:
            args += "--only_buffer "
        #args = list(args.split())
        logger.debug("Corriendo comando externo de impresion %s", command)
        system(command + " " + args)
        return True

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer,
                             extra_data):
        self._info("imprimir_serializado")
        command = "%s/print_or_cache.py" % PATH_IPC_SERVER
        args = "--serialized --tipo_tag %s --tag \"%s\" --extra_data \"%s\" " % (tipo_tag, tag,
            b64encode(extra_data))
        if transpose:
            args += "--transpose "

        if only_buffer:
            args += "--only_buffer "

        logger.debug("Corriendo comando externo de impresion %s", command)
        logger.info(command + "  " + args)
        system(command + " " + args)
        return True


    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def do_print(self):
        self._info("do_print")
        self.printer.do_print()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def simular_impresion(self):
        self._info("simular_impresion")
        return self.printer.simular_impresion()

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def tarjeta_ingresada(self):
        status = self.full_paper_status()
        self._info("tarjeta_ingresada")
        return status

    @dbus.service.signal(DBUS_BUSNAME_PRINTER)
    def insertando_papel(self, status):
        self._info("insertando_papel")
        return status

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def full_paper_status(self):
        self._info("full_paper_status")
        status = {}
        try:
            ingresada = self.printer.tarjeta_ingresada()
            status['paper_out_1'] = 1 if ingresada else 0
        except ValueError, e:
            status['paper_out_1'] = 0
            self._conn = False
            self.connection(False)
        return status

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def tarjeta_sin_retirar(self):
        self._info("tarjeta_sin_retirar")
        estado = self.printer.tarjeta_sin_retirar()
        self._info("estado %s" %  estado)
        status = self.full_paper_status()
        return status

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def ping(self):
        return 'pong'

    @dbus.service.method(DBUS_BUSNAME_PRINTER)
    def estado(self, out_signature="b"):
        return self._conn

    @dbus.service.signal(DBUS_BUSNAME_PRINTER)
    def con_tarjeta(self, tiene_tarjeta):
        self._info("tiene_tarjeta %s" % tiene_tarjeta)
        status = self.full_paper_status()
        return status

    @dbus.service.signal(DBUS_BUSNAME_PRINTER)
    def connection(self, state):
        self._info("connection: " + str(state))
        return state

if __name__ == '__main__':
    PrinterDBus()
