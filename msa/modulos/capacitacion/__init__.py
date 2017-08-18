"""
Modulo para capacitación de electores.

Muestra un menú para elegir la Ubicacion (en caso de ser más de una) y permite
elegir entre capacitar sufragio, asistida e imprimir votos en blanco para
capacitar sobre la verificacion del voto en caso de que esté activado.
"""
from gi.repository.GObject import idle_add, timeout_add
from time import sleep

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
                                   MODULO_SUFRAGIO, E_ESPERANDO)
from msa.modulos.sufragio import Modulo as ModuloSufragio
from msa.modulos.sufragio.controlador import Controlador as ControllerVoto
from msa.modulos.sufragio.registrador import Registrador


class FakeRegistrador(Registrador):
    """Registrador fake que usamos para pisar en la capacitacion."""

    def __init__(self, *args):
        """Constructor."""
        super(FakeRegistrador, self).__init__(*args[:4])

    def registrar_voto(self, solo_impimir=False):
        """Expulsa la boleta en vez de imprimir."""
        timeout_add(4000, self.modulo.rampa.expulsar_boleta)
        timeout_add(8000, self.modulo._fin_registro)

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

        self.constants_sent = False

        self.rampa = RampaCapacitacion(self)
        self.sesion = get_sesion()
        self._timeout_consulta = None
        self._consultando_tag = None

    def imprimir_boleta(self):
        selec = Seleccion(self.controlador.mesa)
        selec.rellenar_de_blanco()
        registrador = Registrador(self.controlador.fin_boleta_demo, self,
                                  self.controlador.fin_boleta_demo_error)
        registrador.seleccion = selec
        registrador.registrar_voto()
        self.rampa.datos_tag = None

    def cancelar_impresion(self):
        self.set_estado(E_ESPERANDO)

    def _iniciar_capacitacion(self):
        """Inicia el modulo."""
        self._descargar_ui_web()
        self.web_template = "sufragio"
        self.controlador = ControllerVoto(self)

        Clase_reg = Registrador if self.config("imprimir_capacitacion") \
            else FakeRegistrador
        self.registrador = Clase_reg(self._fin_registro, self, self._error)

        sleep(1)
        self._cargar_ui_web()
        sleep(1)
        self.ventana.show_all()

    def _iniciar_capacitacion_asistida(self):
        """Inicia el modulo."""
        self._descargar_ui_web()
        self.web_template = "sufragio"
        ModuloAsistida.inicializar_locutor(self)
        self.controlador = ControllerAsistida(self)

        Clase_reg = Registrador if self.config("imprimir_capacitacion") \
            else FakeRegistrador
        self.registrador = Clase_reg(self._fin_registro, self, self._error)

        sleep(1)
        self._cargar_ui_web()
        sleep(1)
        self.ventana.show_all()

    def _ready(self):
        """Envia las constantes y carga los botones cuando se cargó el HTML."""
        self.controlador.send_constants()
        self.controlador.cargar_botones()

    def _guardar_voto(self):
        """Guarda al voto."""
        self.set_estado(E_REGISTRANDO)
        self.registrador.registrar_voto(solo_impimir=True)
        self.rampa.datos_tag = None

    def _configurar_ubicacion_capacitacion(self, ubicacion):
        """Establece la ubicacion para capacitar."""
        mesa_obj = Ubicacion.one(numero=ubicacion)
        self._mesa_anterior = self.sesion.mesa
        mesa_obj.set_aes_key(b"\xff"*16)
        self.sesion.mesa = mesa_obj
        self._load_config()

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

    def _consultar(self, tag_leido):
        if self.controlador.nombre == MODULO_SUFRAGIO:
            ModuloSufragio._consultar(self, tag_leido)
        else:
            if self.rampa.tiene_papel:
                self._mostrar_consulta(tag_leido)
