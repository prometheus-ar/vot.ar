"""Modulo Menu."""
from gi.repository.GObject import idle_add
from msa.core.documentos.actas import Apertura
from msa.core.i18n import levantar_locales
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (MODULO_CALIBRADOR, MODULO_INICIO,
                                   MODULO_MENU, SHUTDOWN)
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.menu.controlador import Controlador
from msa.modulos.menu.rampa import Rampa


class Modulo(ModuloBase):

    """El modulo de menu del sistema"""

    @requiere_mesa_abierta
    def __init__(self, nombre):
        self.controlador = Controlador(self)
        self.web_template = MODULO_MENU

        ModuloBase.__init__(self, nombre)
        self._start_audio()
        levantar_locales()

        self.ret_code = MODULO_INICIO
        self.mesa_abierta = self.sesion.apertura is not None or not \
            self.config("realizar_apertura")
        self.boton_mantenimiento = False

        self.rampa = Rampa(self)
        self.rampa.expulsar_boleta()

        self.sesion._tmp_apertura = None

    def _inicio(self):
        """Inicio del modulo."""
        self.controlador.send_constants()
        self.controlador.cargar_botones(self.mesa_abierta)

    def mostrar_boton_mantenimiento(self):
        """Muestra el boton de mantenimiento."""
        self.boton_mantenimiento = True
        self.controlador.show_maintenance_button()

    def _btn_presionado(self, boton):
        """ Evento al presionar sobre un módulo """
        # Obtengo el label del botón, lo busco en el diccionario de botones
        # y lo establezco como código de retorno
        self.play_sonido_tecla()
        self.salir_a_modulo(boton)

    def _calibrar_pantalla(self):
        """Llama al calibrador de la pantalla."""
        self.ret_code = MODULO_CALIBRADOR
        self.ventana.remove(self.browser)
        self.quit()

    def _btn_apagar_clicked(self, w=None):
        """Llamo al callback para apagar la maquina en su totalidad."""
        self.controlador.reiniciar_timer()
        self.play_sonido_tecla()
        self.controlador.cargar_dialogo("msg_confirmacion_apagar",
                                        aceptar=self.apagar,
                                        cancelar=self.hide_dialogo)

    def hide_dialogo(self):
        """Esconde el dialogo."""
        self.controlador.hide_dialogo()

    def apagar(self):
        """Sale del módulo de inicio y envia la orden de apagado """
        self.ret_code = SHUTDOWN
        idle_add(self.quit)

    def quit(self, w=None):
        """Sale del modulo."""
        if self.signal is not None:
            self.signal.remove()
        self.controlador.quitar_timer()

        ModuloBase.quit(self, w)

    def _configurar_mesa(self, datos_tag):
        """Configura la mesa con los datos que contiene el tag."""
        apertura = Apertura.desde_tag(datos_tag)
        if apertura.mesa is not None:
            self.sesion.apertura = apertura
            self.sesion.mesa = apertura.mesa
            self.mesa_abierta = True
            self._inicio()
