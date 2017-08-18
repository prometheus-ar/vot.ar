"""Modulo de votacion asistida.
Permite la votacion de personas con impedimentos visuales.

Hereda la mayoría de los comportamientos del modulo Sufragio.
"""
from gi.repository.GObject import idle_add

from msa.core.config_manager.constants import COMMON_SETTINGS
from msa.core.data import Speech
from msa.modulos.asistida.controlador import Controlador
from msa.modulos.constants import E_VOTANDO, MODULO_SUFRAGIO
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.sufragio import Modulo as ModuloSufragio


class Modulo(ModuloSufragio):

    """Modulo para votacion asistida.
    Hereda del ModuloSufragio y agrega cosas especificas de la votacion para
    personas con impedimentos visuales."""

    @requiere_mesa_abierta
    def __init__(self, *args, **kwargs):
        """Constructor. inicializa lo mismo que Sufragio más el locutor."""
        ModuloSufragio.__init__(self, *args, **kwargs)
        self.config_files = [COMMON_SETTINGS, MODULO_SUFRAGIO, self.nombre]
        self._load_config()
        self._start_audio()
        self.inicializar_locutor()

    def inicializar_locutor(self):
        """Inicializa el locutor que es el proceso que habla en asistida."""
        if self.sesion.locutor is None:
            self.sesion.inicializar_locutor()
        if not self.sesion.locutor.is_alive():
            self.sesion.locutor.start()

    def set_controller(self):
        """Pisa el metodo set_controlador para que levante el de asistida."""
        self.controlador = Controlador(self)

    def _inicio(self, *args, **kwargs):
        """Pisa el metodo inicio para mostrar el teclado."""
        ModuloSufragio._inicio(self, *args, **kwargs)
        if self.estado == E_VOTANDO:
            self.controlador.send_command("mostrar_teclado")

    def _error(self, cambiar_estado=True):
        """Lanza el error tanto en la interfaz visual como en la auditiva."""
        ModuloSufragio._error(self, cambiar_estado)

        def _locutar_error():
            """Ejecuta el sonido del error."""
            self.controlador.sesion.locutor.shutup()
            frases = [Speech.one("error_almacenado").texto,
                      Speech.one("error_almacenado_2").texto]
            self.sesion.locutor.decir(frases)
        idle_add(_locutar_error)


    def _consultar(self, tag):
        """Permite al elector consultar una boleta.

        Parametros:
            tag -- un objeto de clase SoporteDigital.
        """
        # En votacion asistida no permitimos verificar la boleta apoyandola.
        if self.rampa.tiene_papel:
            self._mostrar_consulta(tag)
