# -*- coding: utf-8 -*-
from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException
from time import sleep

from ojota import current_data_code

from msa import get_logger
from msa.core.ipc.client.rfid_controller import DbusLectorController
from msa.core.ipc.client.print_controller import DbusPrintController
from msa.core.ipc.client.powermanager_controller import \
    DbusPowerManagerController
from msa.core.ipc.client.backlight_controller import DbusBacklightController
from msa.core.ipc.client.agent_controller import DbusAgentController
from msa.core.ipc.client.fancoolers_controller import DbusFanCoolersController
from msa.core.ipc.client.pir_controller import DbusPIRController
from msa.core.settings import USA_ARMVE
from msa.core.speech import Locutor
from msa.voto.constants import MODULO_VOTO


_sesion_actual = None


class Sesion(object):

    """Informacion de sesion de voto."""

    def __init__(self, iniciar_hw=True):
        self._mesa = None
        self.apertura = None
        self.recuento = None
        self.interna = None
        self.impresora = None
        self.lector = None
        # para poder iluminar de rojo en el recuento
        self.ultima_seleccion = None
        self.logger = get_logger(MODULO_VOTO)

        if iniciar_hw:
            DBusGMainLoop(set_as_default=True)
            retries = 3
            while retries:
                try:
                    self.impresora = DbusPrintController()
                    retries = 0
                except DBusException, error:
                    msg = "Hubo un problema para inicializar la impresora"
                    self.logger.error(msg)
                    self.logger.error(error)
                    retries -= 1
                    sleep(5)

            self.lector = DbusLectorController()
            if USA_ARMVE:
                self.powermanager = DbusPowerManagerController()
                self.backlight = DbusBacklightController()
                #self.backlight.set_brightness(DEFAULT_BRIGHTNESS)
                self.agent = DbusAgentController()
                self.fancoolers = DbusFanCoolersController()
                self.pir = DbusPIRController()

        self.locutor = None

    def getmesa(self):
        return self._mesa

    def setmesa(self, value):
        self._mesa = value
        if self._mesa:
            current_data_code(self._mesa.cod_datos)
        else:
            current_data_code(None)

    mesa = property(getmesa, setmesa)

    def restart(self):
        """ Reinicia los Servicios de DBus y resetea el ARM si existe """
        # Bajo uno, en caso de ARMVE baja todo
        self.lector.quit()
        # Entonces tengo 2 servicios Dbus, bajo el segundo
        if not USA_ARMVE:
            self.impresora.quit()

    def inicializar_locutor(self):
        self.locutor = Locutor()


def get_sesion(iniciar_hw=True):
    '''Obtiene la sesion actual.'''
    global _sesion_actual
    if not _sesion_actual:
        _sesion_actual = Sesion(iniciar_hw=iniciar_hw)
    return _sesion_actual
