# -*- coding: utf-8 -*-
import gobject

from os import popen
from time import sleep

from msa.core.clases import Apertura
from msa.core.rfid.constants import NO_TAG
from msa.core.settings import USA_ARMVE
from msa.helpers import levantar_locales
from msa.voto.constants import MODULO_ADMIN, COMANDO_MD5, MODULO_CALIBRADOR
from msa.voto.controllers.administrador import ControllerAdmin
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaAdmin
from msa.voto.sesion import get_sesion
from msa.voto.settings import REALIZAR_APERTURA


sesion = get_sesion()


class ModuloAdministradorWeb(Modulo):

    """El modulo de administracion del sistema"""

    def __init__(self):
        self.controller = ControllerAdmin(self)
        self.es_modulo_web = True
        self.web_template = "admin"

        Modulo.__init__(self)
        levantar_locales()

        self._vaciar_impresora()
        self.ret_code = MODULO_ADMIN  # Esto hace que salga del gtk_main()
        self.mesa_abierta = sesion.apertura is not None or not \
            REALIZAR_APERTURA
        self.modo_mantenimiento = False
        self.boton_mantenimiento = False

        self.rampa = RampaAdmin(self)

    def _vaciar_impresora(self):
        impresora = sesion.impresora
        if impresora is not None and impresora.tarjeta_ingresada():
            impresora.expulsar_boleta()

    def _inicio(self):
        self.controller.send_constants()
        self.controller.cargar_botones(self.mesa_abierta)

    def _set_maintenance_mode(self):
        self.modo_mantenimiento = True

    def _show_maintenance_button(self):
        self.boton_mantenimiento = True
        self.controller.show_maintenance_button()

    def _btn_presionado(self, boton):
        """ Evento al presionar sobre un módulo """
        # Obtengo el label del botón, lo busco en el diccionario de botones
        # y lo establezco como código de retorno
        self.ret_code = boton
        if self.browser is not None:
            self.ventana.remove(self.browser)
        self.quit()

    def _calibrar_pantalla(self):
        self.ret_code = MODULO_CALIBRADOR
        self.ventana.remove(self.browser)
        self.quit()

    def quit(self, w=None):
        if hasattr(self.controller, "timeout_bateria"):
            gobject.source_remove(self.controller.timeout_bateria)
        if self.signal is not None:
            self.signal.remove()

        Modulo.quit(self, w)

    def _recheck_batteries(self):
        self.controller.refresh_batteries()

    def _recheck_pir_detected(self):
        self.controller.pir_detection_status(True)

    def _recheck_pir_not_detected(self):
        self.controller.pir_detection_status(False)

    def printer_begin_test(self):
        if not self.rampa.tiene_papel:
            if USA_ARMVE:
                self.signal_paper = \
                    sesion.impresora.registrar_autofeed_end(self._printer_test)
            else:
                sesion.impresora.registrar_insertando_papel(self._printer_test)
            self.controller.printer_begin_test()
        else:
            self._printer_test(estado=True)

    def printer_end_test(self):
        sesion.impresora.remover_autofeed_end()
        sesion.impresora.remover_insertando_papel()
        if not USA_ARMVE:
            sleep(10)
            self.rampa.expulsar_boleta()
        self.controller.printer_end_test()

    def _printer_test(self, estado):
        self.controller.print_test()
        self.printer_end_test()

    def md5_checkfiles(self, path):
        if USA_ARMVE:
            arq = "malata"
            machine_number = sesion.agent.get_machine_type()
            if machine_number is not None and machine_number == 2:
                arq = "armve"
        else:
            arq = "armve"
        hashobj = popen(COMANDO_MD5 % (path, arq))
        md5num = hashobj.read()
        hashobj.close()
        return md5num

    def _configurar_mesa(self, datos_tag):
        """
        Configura la mesa con los datos que contiene el tag.
        """
        apertura = Apertura.desde_tag(datos_tag)
        if apertura.mesa is not None:
            sesion.apertura = apertura
            sesion.mesa = apertura.mesa
            self.mesa_abierta = True
            self._inicio()

    def rfid_check(self, datos_tag):
        try:
            self.controller.rfid_check(datos_tag['tipo'])
        except:
            self.controller.rfid_check(NO_TAG)
