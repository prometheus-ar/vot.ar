"""
El modulo inicial de la aplicación.

Nos permite loguearnos con una mesa.
"""
from os import system
from subprocess import Popen

from gi.repository.GObject import idle_add
from msa.modulos import get_sesion
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_INICIAL, MODULO_CAPACITACION, SHUTDOWN,
                                   SUBMODULO_MESA_Y_PIN_INICIO)
from msa.modulos.gui.basegui import MsgDialog
from msa.modulos.inicio.controlador import Controlador
from msa.modulos.inicio.rampa import Rampa
from msa.settings import DEBUG

try:
    from keybinder.keybinder_gtk import KeybinderGtk
except ImportError:
    print('Keybinder no encontrado')


class Modulo(ModuloBase):

    """ Modulo de Inicio.

        Este módulo muestra la pantalla de bienvenida y realiza el proceso de
        configuracion de una mesa.
        El usuario debe pasar el tag de presidente o de MSA para habilitar el
        comienzo de la configuración.
        Luego se le pedirá un PIN y el modulo configurará la mesa para la
        ubicación solicitada.
    """

    def __init__(self, nombre):
        """Constructor."""
        # Importante antes de inicializar el modulo, limpiar la configuracion
        self.sesion = get_sesion()
        self._limpiar_configuracion()
        self.mute_armve_ver_1()
        self.controlador = Controlador(self)
        self.web_template = "inicio"

        ModuloBase.__init__(self, nombre)

        self.loop_lector = True
        self._vaciar_impresora()
        self.estado = E_INICIAL
        self.dialogo = None
        self._bind_term()
        self.manejar_desconexion()

        self.rampa = Rampa(self)

    def mute_armve_ver_1(self):
        """Funcion para mutear ARMVE version 1 (serie P2)."""
        if hasattr(self.sesion, "agent"):
            machine_number = self.sesion.agent.get_machine_type()
            if machine_number == 1:
                system('/usr/bin/amixer -c 0 sset "Auto-Mute Mode" Disabled')

    def _bind_term(self):
        """Bindea la terminal si tenemos el modulo necesario para hacerlo."""
        try:
            keybinder = KeybinderGtk()
            keybinder.register('<Ctrl>x', self.abrir_terminal)
            keybinder.start()
        except (KeyError, NameError):
            pass

    def set_pantalla(self, pantalla):
        """Setea la pantalla indicada."""
        self.controlador.set_screen(pantalla)

    def hide_dialogo(self):
        """Esconde el dialogo."""
        self.controlador.hide_dialogo()

    def _inicio(self):
        """Funcion llamada desde el controlador."""
        self.controlador.send_constants()

    def manejar_desconexion(self):
        """Maneja la desconexion del hardware.

        En Malata tenia mas sentido que ahora, pero de todos modos si perdemos
        conexion lo mostramos.
        """
        def mostrar_dialogo(estado):
            """Muestra el dialogo en caso de desconexion."""

            if not estado and self.dialogo is None:
                self.dialogo = MsgDialog(_("arm_no_responde"))
                self.dialogo.show()
            elif estado and self.dialogo is not None:
                self.dialogo.hide()
                self.dialogo = None

        if self.sesion.impresora is None or not self.sesion.impresora.estado():
            mostrar_dialogo(False)

        if self.sesion.impresora is not None:
            self.sesion.impresora.connection(mostrar_dialogo)

    def _vaciar_impresora(self):
        """Expulsa la boleta cuando arranca el modulo"""
        impresora = self.sesion.impresora
        if impresora is not None and impresora.estado():
            impresora.expulsar_boleta()

    def _pantalla_principal(self):
        """Levanta la pantalla inicial."""
        self.controlador.set_screen("pantalla_inicio")

    def a_capacitacion(self):
        """Sale al modo de capacitacion."""
        self.salir_a_modulo(MODULO_CAPACITACION)

    def configurar(self):
        """Inicio la configuración de la mesa."""
        self.salir_a_modulo(SUBMODULO_MESA_Y_PIN_INICIO)

    def _limpiar_configuracion(self):
        """Reinicio todos los valores."""
        sesion = get_sesion()
        sesion.mesa = None
        sesion.apertura = None
        sesion.recuento = None

    def apagar(self):
        """ Sale del módulo de inicio y envia la orden de apagado """
        self.ret_code = SHUTDOWN
        idle_add(self.quit)

    def abrir_terminal(self):
        """Abre la terminal en caso de que las condiciones esten dadas."""
        if DEBUG:
            self.sesion.logger.debug('abrir terminal')
            Popen('xterm')
