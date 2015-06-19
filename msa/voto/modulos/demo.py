# -*- coding: utf-8 -*-
"""Modulo de demostracion, generalmente utilizado para capacitación."""

import pygtk

pygtk.require('2.0')
import time

from msa.core.data import Ubicacion
from msa.voto.constants import MODULO_INICIO
from msa.voto.controllers.demo import ControllerDemo
from msa.voto.controllers.voto import ControllerVoto
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaDemo
from msa.voto.modulos.voto import ModuloVoto
from msa.voto.registrador import Registrador
from msa.voto.sesion import get_sesion


sesion = get_sesion()


class FakeRegistrador(Registrador):

    def __init__(self, *args):
        #self.parent = args[2]
        super(FakeRegistrador, self).__init__(*args[:3])

    def _guarda_tag(self, datos):
        self._datos = datos
        return True

    def _lee_tag(self):
        return self._datos

    def _registrar_voto(self):
        self._imprime()

    def _proceso(self):
        self._imprime()

    def _imprime(self):
        sesion.impresora.posicionar_al_inicio()
        time.sleep(0.5)
        sesion.impresora.expulsar_boleta()
        time.sleep(5)
        self.parent._fin_registro()

    def _prepara_impresion(self, seleccion):
        self.seleccion = seleccion


class ModuloDemo(ModuloVoto):

    def __init__(self):
        self._mesa_anterior = None
        self.controller = ControllerDemo(self)
        self.es_modulo_web = True
        self.web_template = "demo"

        Modulo.__init__(self)
        self.estado = None

        #self._limpiar_configuracion()
        self.volvera = None
        self._metiendo_papel = False
        self.momento_ultimo_voto = None
        self.constants_sent = False

        self.tiempo_verificacion = 5000

        self.rampa = RampaDemo(self)

    def _iniciar_demo(self):
        self._descargar_ui_web()
        self.web_template = "voto"
        self.controller = ControllerVoto(self)
        self.registrador = FakeRegistrador(self._fin_registro, self.seleccion,
                                           self)
        self._cargar_ui_web()
        self.ventana.show_all()

    def _ready(self):
        self.controller.send_constants()
        self.controller.cargar_botones()

    def _configurar_ubicacion_demo(self, tag, data=None):
        # Guardo una referencia a la configuracion anterior, para cuando salga
        # volver a configurarla
        #if self.pantalla:
        #    self.pantalla.callback = self.controlador
        #    self.pantalla.quit()
        mesa_obj = Ubicacion.one(numero=tag)
        self._mesa_anterior = sesion.mesa
        #self._configurar_mesa(mesa_obj)
        sesion.mesa = mesa_obj

    def salir(self):
        if self._mesa_anterior:
            #self._configurar_mesa(self._mesa_anterior)
            sesion.mesa = self._mesa_anterior
        sesion.impresora.expulsar_boleta()
        self.ret_code = MODULO_INICIO
        self.quit()
