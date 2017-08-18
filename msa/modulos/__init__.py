from ojota import current_data_code

from msa.core.audio.speech import Locutor
from msa.core.logging import get_logger
from msa.core.ipc.client import IPCClient
from msa.settings import MODO_DEMO


_sesion_actual = None


class Sesion(object):

    """Informacion de sesion de voto."""

    def __init__(self, iniciar_hw=True):
        self.logger = get_logger("modulos")

        self._mesa = None
        self.apertura = None
        self.recuento = None
        self.credencial = None
        self._tmp_apertura = None
        self.locutor = None
        self.modo_demo = MODO_DEMO

        # interaccion con hardware
        if iniciar_hw:
            self._init_hardware()
        else:
            self._servicio = None

    def _init_hardware(self):
        self._servicio = IPCClient(self)

    def getmesa(self):
        return self._mesa

    def setmesa(self, value):
        """Establece la mesa en la sesion."""
        self._mesa = value

        if self._mesa is not None:
            self._mesa.usar_cod_datos()
        else:
            current_data_code(None)

    mesa = property(getmesa, setmesa)

    def inicializar_locutor(self):
        self.locutor = Locutor()


def get_sesion(iniciar_hw=True, force=False):
    '''Obtiene la sesion actual.'''
    global _sesion_actual
    if not _sesion_actual or force:
        _sesion_actual = Sesion(iniciar_hw=iniciar_hw)
    return _sesion_actual
