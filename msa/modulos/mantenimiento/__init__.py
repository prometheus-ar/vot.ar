"""Modulo para permitir hacer algunos ligeros cambios de configuración.

Permite verificar el estado del hardware la maquina.
"""
from os import popen

from gi.repository import GObject

from msa.core.i18n import levantar_locales
from msa.core.rfid.constants import NO_TAG
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import MODULO_MANTENIMIENTO, MODULO_MENU
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.mantenimiento.constants import COMANDO_MD5
from msa.modulos.mantenimiento.controlador import Controlador
from msa.modulos.mantenimiento.rampa import Rampa


class Modulo(ModuloBase):

    """El modulo de mantenimiento del sistema."""

    @requiere_mesa_abierta
    def __init__(self, nombre):
        self.controlador = Controlador(self)
        self.web_template = MODULO_MANTENIMIENTO

        ModuloBase.__init__(self, nombre)
        levantar_locales()

        self.ret_code = MODULO_MENU

        self.rampa = Rampa(self)
        self.rampa.expulsar_boleta()
        self.controlador.rampa = self.rampa
        self._start_audio()

    def _btn_presionado(self, boton):
        """ Evento al presionar sobre un módulo """
        # Obtengo el label del botón, lo busco en el diccionario de botones
        # y lo establezco como código de retorno
        self.salir_a_modulo(boton)

    def _inicio(self):
        """Inicio del modulo mantenimiento."""
        self.controlador.send_constants()
        GObject.timeout_add(200, self.controlador.inicio_mantenimiento)

    def quit(self, w=None):
        """Sale del modulo."""
        if hasattr(self.controlador, "timeout_bateria"):
            GObject.source_remove(self.controlador.timeout_bateria)
        if self.signal is not None:
            self.signal.remove()

        ModuloBase.quit(self, w)

    def _recheck_batteries(self, data):
        """Rechequea las baterias."""
        self.controlador.refresh_batteries()

    def _recheck_pir_detected(self, data):
        """Rechequea el estado presente del PIR."""
        self.controlador.pir_detection_status(True)

    def _recheck_pir_not_detected(self, data):
        """Rechequea la ausencia de deteccion del PIR."""
        self.controlador.pir_detection_status(False)

    def printer_begin_test(self):
        """Inicia el test de impresion."""
        if not self.rampa.tiene_papel:
            self.signal_paper = self.rampa.registrar_nuevo_papel(
                self._printer_test)
            self.controlador.printer_begin_test()
        else:
            self._printer_test(estado=True)

    def printer_end_test(self):
        """Finaliza el test de impresion."""
        self.rampa.remover_nuevo_papel()
        self.rampa.remover_insertando_papel()
        self.controlador.printer_end_test()
        self.rampa.tiene_papel = False

    def _printer_test(self, estado):
        """Inicia el test de impresion."""
        self.controlador.print_test()
        self.printer_end_test()

    def md5_checkfiles(self, path):
        """Chequea el md5 del DVD."""
        hashobj = popen(COMANDO_MD5 % path)
        md5num = hashobj.read()
        hashobj.close()
        return md5num

    def rfid_check(self, datos_tag):
        """chequea el estado del RFID."""
        try:
            self.controlador.rfid_check(datos_tag.tipo)
        except:
            self.controlador.rfid_check(NO_TAG)
