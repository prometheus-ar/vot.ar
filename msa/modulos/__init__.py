from time import sleep

from ojota import current_data_code

from msa.core.audio.speech import Locutor
from msa.core.ipc.client.agent_controller import DbusAgentController
from msa.core.ipc.client.backlight_controller import DbusBacklightController
from msa.core.ipc.client.fancoolers_controller import DbusFanCoolersController
from msa.core.ipc.client.pir_controller import DbusPIRController
from msa.core.ipc.client.powermanager_controller import(
    DbusPowerManagerController)
from msa.core.ipc.client.print_controller import DbusPrintController
from msa.core.ipc.client.rfid_controller import DbusLectorController
from msa.core.logging import get_logger
from msa.modulos.constants import MODULO_SUFRAGIO


_sesion_actual = None


class Sesion(object):

    """Informacion de sesion de voto."""

    def __init__(self, iniciar_hw=True):
        self._mesa = None
        self.apertura = None
        self._tmp_apertura = None
        self.recuento = None
        self.interna = None
        self.impresora = None
        self.lector = None
        # para poder iluminar de rojo en el recuento
        self.logger = get_logger(MODULO_SUFRAGIO)
        self.salt = ""

        if iniciar_hw:
            from dbus.exceptions import DBusException
            from dbus.mainloop.glib import DBusGMainLoop
            DBusGMainLoop(set_as_default=True)
            retries = 3
            while retries:
                try:
                    self.impresora = DbusPrintController()
                    retries = 0
                except DBusException as error:
                    msg = "Hubo un problema para inicializar la impresora"
                    self.logger.error(msg)
                    self.logger.error(error)
                    retries -= 1
                    sleep(5)

            self.lector = DbusLectorController()
            self.powermanager = DbusPowerManagerController()
            self.backlight = DbusBacklightController()
            self.agent = DbusAgentController()
            self.fancoolers = DbusFanCoolersController()
            self.pir = DbusPIRController()

        self.locutor = None

    def getmesa(self):
        return self._mesa

    def setmesa(self, value):
        self._mesa = value
        if self._mesa:
            self._mesa.usar_cod_datos()
        else:
            current_data_code(None)

    mesa = property(getmesa, setmesa)

    def restart(self):
        """ Reinicia los Servicios de DBus y resetea el ARM si existe """
        self.lector.quit()

    def inicializar_locutor(self):
        self.locutor = Locutor()


def get_sesion(iniciar_hw=True, force=False):
    '''Obtiene la sesion actual.'''
    global _sesion_actual
    if not _sesion_actual or force:
        _sesion_actual = Sesion(iniciar_hw=iniciar_hw)
    return _sesion_actual
