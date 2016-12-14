"""
Modulo para capacitación de electores.

Muestra un menú para elegir la Ubicacion (en caso de ser más de una) y permite
elegir entre capacitar sufragio, asistida e imprimir votos en blanco para
capacitar sobre la verificacion del voto en caso de que esté activado.
"""
import time

from gi.repository.GObject import idle_add

from msa.core.config_manager.constants import COMMON_SETTINGS
from msa.core.data import Ubicacion
from msa.core.documentos.boletas import Seleccion
from msa.modulos import get_sesion
from msa.modulos.asistida import Modulo as ModuloAsistida
from msa.modulos.asistida.controlador import Controlador as ControllerAsistida
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.capacitacion.controlador import Controlador as ControllerCapac
from msa.modulos.capacitacion.rampa import RampaCapacitacion
from msa.modulos.constants import (E_REGISTRANDO, MODULO_ASISTIDA,
                                   MODULO_CAPACITACION, MODULO_INICIO,
                                   MODULO_SUFRAGIO)
from msa.modulos.sufragio import Modulo as ModuloSufragio
from msa.modulos.sufragio.controlador import Controlador as ControllerVoto
from msa.modulos.sufragio.registrador import Registrador


class FakeRegistrador(Registrador):
    """Registrador fake que usamos para pisar en la capacitacion."""

    def __init__(self, *args):
        """Constructor."""
        super(FakeRegistrador, self).__init__(*args[:4])

    def _registrar_voto(self, solo_impimir=False):
        """Expulsa la boleta en vez de imprimir."""
        sesion = get_sesion()
        sesion.impresora.expulsar_boleta()
        time.sleep(5)
        self.modulo._fin_registro()

    def _prepara_impresion(self, seleccion):
        self.seleccion = seleccion


class Modulo(ModuloSufragio):

    """Modulo de capacitacion de electores."""

    def __init__(self, nombre):
        """Constructor."""
        self._mesa_anterior = None
        self.controlador = ControllerCapac(self)
        self.web_template = "capacitacion"

        ModuloBase.__init__(self, nombre)
        self.config_files = [COMMON_SETTINGS, MODULO_SUFRAGIO, MODULO_ASISTIDA,
                             nombre]
        self._load_config()
        self.estado = None

        self.volvera = None
        self._metiendo_papel = False
        self.constants_sent = False

        self.tiempo_verificacion = 5000

        self.rampa = RampaCapacitacion(self)
        self.sesion = get_sesion()

    def imprimir_boleta(self):
        selec = Seleccion(self.controlador.mesa)
        selec.rellenar_de_blanco()
        registrador = Registrador(self.controlador.fin_boleta_demo, self,
                                  self.controlador.fin_boleta_demo_error)
        registrador.seleccion = selec
        registrador._registrar_voto()
        self.rampa.datos_tag = None

    def _iniciar_capacitacion(self):
        """Inicia el modulo."""
        self._descargar_ui_web()
        self.web_template = "sufragio"
        self.controlador = ControllerVoto(self)
        self.tiempo_verificacion = 5000

        Clase_reg = Registrador if self.config("imprimir_capacitacion") \
            else FakeRegistrador
        self.registrador = Clase_reg(self._fin_registro, self, self._error)

        self._cargar_ui_web()
        self.ventana.show_all()

    def _iniciar_capacitacion_asistida(self):
        """Inicia el modulo."""
        self._descargar_ui_web()
        self.web_template = "sufragio"
        ModuloAsistida.inicializar_locutor(self)
        self.controlador = ControllerAsistida(self)
        # piso el tiempo de verificacion para que termine de hablar
        self.tiempo_verificacion = 25000

        Clase_reg = Registrador if self.config("imprimir_capacitacion") \
            else FakeRegistrador
        self.registrador = Clase_reg(self._fin_registro, self, self._error)

        self._cargar_ui_web()
        self.ventana.show_all()

    def _ready(self):
        """Envia las constantes y carga los botones cuando se cargó el HTML."""
        self.controlador.send_constants()
        self.controlador.cargar_botones()

    def _guardar_voto(self):
        """Guarda al voto."""
        self.set_estado(E_REGISTRANDO)
        self.registrador._registrar_voto(solo_impimir=True)
        self.rampa.datos_tag = None

    def _configurar_ubicacion_capacitacion(self, tag, data=None):
        """Establece la ubicacion para capacitar."""
        mesa_obj = Ubicacion.one(numero=tag)
        mesa_obj.set_aes_key(b"\xff" * 16)
        self._mesa_anterior = self.sesion.mesa
        self.sesion.mesa = mesa_obj

    def salir(self):
        """Sale del modulo o va al menu de capacitacion, segun el contexto."""
        if self.controlador.nombre == MODULO_CAPACITACION:
            if self._mesa_anterior:
                self.sesion.mesa = self._mesa_anterior
            self.rampa.expulsar_boleta()
            self._salir()
        else:
            self._descargar_ui_web()
            self.controlador = ControllerCapac(self)
            self.web_template = "capacitacion"

            def _recargar():
                self._cargar_ui_web()
                self.ventana.show_all()
                self.rampa = RampaCapacitacion(self)

            idle_add(_recargar)

    def _salir(self):
        """Sale del modulo, desloguea al usuario."""
        self.salir_a_modulo(MODULO_INICIO)
