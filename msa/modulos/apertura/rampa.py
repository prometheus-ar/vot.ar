# -*- coding: utf-8 -*-
"""
Rampa para el modulo Apertura.

Maneja la interaccion entre la impresora, el lector y el
usuario.
"""
from gi.repository.GObject import timeout_add

from msa.core.rfid.constants import (TAG_COLISION, TAG_ADMIN)
from msa.modulos.base.rampa import RampaActas


class Apertura(RampaActas):

    """
    Rampa que maneja las particularidades de deteccion de chip en el modulo
    de apertura.
    """

    def cambio_tag(self, tipo_lectura, tag):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_lectura -- el tipo de lectura del tag
            tag -- representacion del tag
        """
        if tag is not None:
            if tipo_lectura == TAG_ADMIN:
                timeout_add(500, self.salir)
            elif tipo_lectura == TAG_COLISION:
                self.expulsar_boleta()
                self.tag_colision()

        if tag != self.tag_leido:
            self.tag_leido = tag
            self.maestro()

    def procesar_tag(self, tag):
        """ Callback del evento de tag modificado.

        Argumentos:
            tag -- los datos del tag
        """
        pass
