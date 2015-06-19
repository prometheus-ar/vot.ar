#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import getenv, system

from msa.core.settings_calibrador import FAKE, MISCLICK_THRESHOLD, \
    DUALCLICK_THRESHOLD, FINGER_DELTA, TIMEOUT, FAST_START, NPOINTS, AUTO_CLOSE
from msa.voto.constants import MODULO_ADMIN, MODULO_INICIO
from msa.voto.controllers.calibrador import CalibratorController
from msa.voto.modulos import Modulo
from msa.voto.sesion import get_sesion

sesion = get_sesion()


class CalibradorPantalla(Modulo):

    """ Modulo de Calibracion de pantalla

    """

    def __init__(self):
        """ Constructor """
        self.controller = CalibratorController(self, FAKE, None,
                                               MISCLICK_THRESHOLD,
                                               DUALCLICK_THRESHOLD,
                                               FINGER_DELTA, TIMEOUT,
                                               FAST_START, NPOINTS, AUTO_CLOSE)
        self.es_modulo_web = True
        self.web_template = "calibrador"

        # Esto hace que no se apague la pantalla
        system("DISPLAY=%s xset s off; xset -dpms" % getenv("DISPLAY",
                                                            ":0"))

        Modulo.__init__(self)

    def quit(self, w=None):
        if sesion._mesa is not None:
            self.ret_code = MODULO_ADMIN
        else:
            self.ret_code = MODULO_INICIO
        self._descargar_ui_web()
        Modulo.quit(self)
