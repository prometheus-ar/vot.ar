# -*- coding: utf-8 -*-
"""
Modulo apertura.

Imprime el acta de apertura.
"""
from gi.repository.GObject import timeout_add

from msa.modulos.constants import MODULO_MENU
from msa.modulos.apertura.controlador import Controlador
from msa.modulos.apertura.rampa import Apertura
from msa.modulos.apertura.registrador import RegistradorApertura
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_INICIAL, MODULO_INICIO,
                                   SUBMODULO_DATOS_APERTURA)
from msa.modulos.decorators import requiere_mesa_abierta


class Modulo(ModuloBase):

    """ Modulo de Apertura de votos.

        Este módulo permite generar el acta de apertura de una mesa.
        El usuario debe ingresar el acta en la maquina, agregar y confirmar sus
        datos e imprimirla.
    """

    @requiere_mesa_abierta
    def __init__(self, nombre):
        """Constructor del modulo Apertura.
        Argumentos:
            nombre -- el nombre del modulo que se está cargando.
        """
        self.web_template = "apertura"
        self.rampa = Apertura(self)
        self.controlador = Controlador(self)
        self._mensaje = None

        ModuloBase.__init__(self, nombre)
        self._start_audio()

        self.ret_code = MODULO_INICIO
        self.estado = E_INICIAL
        self.registrador = RegistradorApertura(self, self.callback_salir,
                                               self.callback_proxima_acta)

    def callback_salir(self):
        self.salir_a_modulo(MODULO_MENU)

    def callback_proxima_acta(self):
        self.controlador.proxima_acta()

    def reimprimir(self, *args):
        timeout_add(100, self.controlador.reimprimir)

    def confirmar_apertura(self):
        """Configura la apertura."""
        self.registrador.registrar()

    def salir(self):
        """ Sale del módulo de apertura, vuelve al comienzo con la maquina
            desconfigurada.
        """
        self.salir_a_modulo(MODULO_INICIO)

    def mensaje_inicial(self):
        """
        No hace nada, por que estamos en el modulo y no en el submodulo.
        """
        pass

    def volver_atras(self):
        """ Sale del módulo de apertura, vuelve al comienzo con la maquina
            desconfigurada.
        """
        self.salir_a_modulo(SUBMODULO_DATOS_APERTURA)
