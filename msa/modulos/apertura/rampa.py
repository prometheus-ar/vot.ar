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

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        if tag_dict is not None:
            if tipo_tag == TAG_ADMIN:
                timeout_add(500, self.salir)
            elif tipo_tag == TAG_COLISION:
                self.expulsar_boleta()
                self.tag_colision()

        if tag_dict != self.datos_tag:
            self.datos_tag = tag_dict
            self.maestro()

    def procesar_tag(self, datos_tag):
        """ Callback del evento de tag modificado.

        Argumentos:
            datos_tag -- los datos del tag
        """
        pass
