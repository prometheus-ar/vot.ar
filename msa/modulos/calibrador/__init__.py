#!/usr/bin/env python
"""Modulo que permite la calibración de la maquina."""
from os import getenv, system
from gi.repository import Gdk

from msa.modulos.base.modulo import ModuloBase
from msa.modulos.calibrador.controlador import Controlador
from msa.modulos.calibrador.settings import (AUTO_CLOSE, DUALCLICK_THRESHOLD,
                                             FAKE, FAST_START,
                                             MISCLICK_THRESHOLD, NPOINTS,
                                             TIMEOUT)
from msa.modulos.constants import MODULO_INICIO, MODULO_MENU


class Modulo(ModuloBase):

    """Modulo de Calibracion de pantalla."""

    def __init__(self, nombre):
        """Constructor."""
        self.controlador = Controlador(
            self, FAKE, None, MISCLICK_THRESHOLD, DUALCLICK_THRESHOLD,
            TIMEOUT, FAST_START, NPOINTS, AUTO_CLOSE)
        self.web_template = "calibrador"

        # Esto hace que no se apague la pantalla
        system("DISPLAY=%s xset s off; xset -dpms" % getenv("DISPLAY", ":0"))

        ModuloBase.__init__(self, nombre)

    def quit(self, w=None):
        """Sale del modulo."""
        if self.sesion._mesa is not None:
            self.ret_code = MODULO_MENU
        else:
            self.ret_code = MODULO_INICIO
        self._descargar_ui_web()
        ModuloBase.quit(self)

    def _webkit2_touch(self, widget, event):
        """ Webkitgtk 2 no lanza el evento del DOM touchend y touchmove por un
        bug https://bugs.webkit.org/show_bug.cgi?id=158531 Por lo tanto muchos
        clicks no son capturados correctamente.
        """
        if event.touch.type == Gdk.EventType.TOUCH_END:
            data = {
                "x": event.x,
                "y": event.y
            }
            self.controlador.send_command("fake_touch_end", data)
