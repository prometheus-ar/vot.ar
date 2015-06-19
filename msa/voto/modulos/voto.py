# -*- coding: utf-8 -*-
"""Los modulos que componen al sistema.

Cada modulo es independiente, pero todos pueden heredar de Modulo para
facilitar la implementacion y mantenimiento.

Cada modulo debe tener un método main(), que puede o no devolver un
string. Si este string existe como indice del diccionario del script
de inicio, ejecuta el modulo relacionado a ese indice.

Por ejemplo, sin en el script de inicio tenemos el diccionario:

modulos = {'voto': ModuloVoto, 'escrutinio': ModuloEscrutinio}

si al salir de un modulo devuelvo 'escrutinio', el script de inicio
deberia llamar instanciar un ModuloEscrutinio, y ejecutar su metodo
main():

mod = modulos['escrutinio']
res = mod.main()
"""

import gobject

from datetime import datetime

from msa.core.clases import Seleccion
from msa.voto.constants import MODULO_VOTO, PANTALLA_INSERCION_BOLETA, \
    PANTALLA_MENSAJE_FINAL, PANTALLA_SELECCION_CANDIDATOS, E_VOTANDO, \
    E_EXPULSANDO_BOLETA, E_ESPERANDO, E_CONSULTANDO, E_REGISTRANDO
from msa.core.settings import USA_ARMVE
from msa.settings import LOG_CAPTURE_STDOUT
from msa.voto.controllers.voto import ControllerVoto
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaVoto
from msa.voto.registrador import Registrador
from msa.voto.sesion import get_sesion
from msa.voto.settings import SELECCIONAR_IDIOMA


sesion = get_sesion()


class ModuloVoto(Modulo):

    """
        Modulo de voto.

        Hereda de: ModuloLector

        Espera a que se aproxime un tag, si esta vacio permite votar, sino
        muestra el contenido del tag.

        Si durante cualquier momento del voto, se retira el tag, cancela
        la operacion y vuelve a la pantalla de inicio.
    """

    def __init__(self):
        """Constructor"""
        if LOG_CAPTURE_STDOUT:
            import sys
            from logging import INFO, ERROR
            from msa import StreamToLogger
            sys.stdout = StreamToLogger(sesion.logger, INFO)
            sys.stderr = StreamToLogger(sesion.logger, ERROR)
        self.constants_sent = False
        self.send_function = None
        self.set_controller()
        self.es_modulo_web = True
        self.web_template = "voto"
        Modulo.__init__(self)
        self.estado = None

        self.ret_code = MODULO_VOTO
        self.volvera = None
        self._metiendo_papel = False
        self.momento_ultimo_voto = None

        self.registrador = Registrador(self._fin_registro,
                                       self.seleccion, self)
        self.sesion = sesion
        self.tiempo_verificacion = 5000

        self.rampa = RampaVoto(self)

    def set_estado(self, estado):
        """
            Setea el estado y realiza el seteo del tiempo para poder *medir* la
            espera
        """
        self.estado = estado

    def set_controller(self):
        self.controller = ControllerVoto(self)

    def _comenzar(self):
        # Inicializo la seleccion
        if self.estado != E_VOTANDO:
            self.set_estado(E_VOTANDO)
            self.seleccion = Seleccion(sesion.mesa, sesion.interna)
            self.controller.set_screen(PANTALLA_SELECCION_CANDIDATOS)

    def set_pantalla(self, pantalla, image_data=None):
        self.controller.set_screen(pantalla, image_data=image_data)

    def get_pantalla_inicial_voto(self):
        if SELECCIONAR_IDIOMA:
            self.controller.set_pantalla_idiomas()
        else:
            self.controller.get_pantalla_modos()

    def expulsar_boleta(self):
        self.rampa.tiene_papel = False
        self.set_estado(E_EXPULSANDO_BOLETA)
        self.expulsar_boleta()

    def salir(self):
        # Llamo al destroy para que elimine los pixbufs y evitar leaks
        if self.pantalla is not None:
            self.pantalla.destroy()

        if self.browser is not None:
            self.ventana.remove(self.browser)
        self.admin()

    def _fin_registro(self):
        self.set_pantalla(PANTALLA_MENSAJE_FINAL)

        def _retornar():
            if self.estado not in (E_CONSULTANDO, E_VOTANDO):
                self.pantalla_insercion()

        gobject.timeout_add(5000, _retornar)

    def _guardar_voto(self):
        self.set_estado(E_REGISTRANDO)
        if USA_ARMVE:
            self.registrador._registrar_voto()
            self.rampa.datos_tag = None
        else:
            self.registrador._proceso()
        self.momento_ultimo_voto = datetime.now()

    def pantalla_insercion(self):
        self.seleccion = None
        self.set_estado(E_ESPERANDO)
        self.set_pantalla(PANTALLA_INSERCION_BOLETA)

    def hay_tag_vacio(self):
        self._comenzar()

    def _consultar(self, datos_tag, force=False):
        if self.estado != E_CONSULTANDO or force:
            self.set_estado(E_CONSULTANDO)

            if datos_tag is not None and len(datos_tag) > 0:
                def _fin():
                    if self.estado == E_CONSULTANDO:
                        sigue = False
                        if self.rampa.tiene_papel:
                            self.rampa.expulsar_boleta()
                        else:
                            tag = sesion.lector.get_tag()
                            if tag is not None:
                                sigue = True
                                self._consultar(tag['datos'], True)
                        if not sigue:
                            # reseteo el estado del tag por si no me llega el evento.
                            self.rampa.datos_tag = None
                            self.pantalla_insercion()

                seleccion_tag = None
                try:
                    seleccion_tag = Seleccion.desde_tag(datos_tag, sesion.mesa)
                except Exception as e:
                    sesion.logger.error("La boleta no contiene datos validos")
                    sesion.logger.exception(e)
                    _fin()
                if seleccion_tag is not None:
                    self.controller.consulta(seleccion_tag)
                    gobject.timeout_add(self.tiempo_verificacion, _fin)
            else:
                self.rampa.expulsar_boleta()

    def document_ready(self):
        self.controller.send_constants()
        self.rampa.maestro()

    def show_dialogo(self, mensaje=None, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=None,
                     btn_aceptar=None):
        self.controller.show_dialogo(mensaje, callback_cancelar,
                                     callback_aceptar, btn_cancelar,
                                     btn_aceptar)

    def hide_dialogo(self):
        self.controller.hide_dialogo()
