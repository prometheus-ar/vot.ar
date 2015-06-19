#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de inicio del sistema.
"""

import os
import gc

from importlib import import_module
from optparse import OptionParser

from msa.core.audioplayer import WavPlayer
from msa.helpers import levantar_locales
#from msa.voto import modulos, modulos_impresora, recuento_web, \
#    apertura, demo, calibrador, voto_web, inicio_web, asistida
from msa.voto.constants import MODULO_REINICIO, MODULO_ADMIN,\
    MODULO_APERTURA, MODULO_VOTO, MODULO_ASISTIDA, MODULO_DEMO,\
    MODULO_EXPULSAR_BOLETA, MODULO_CALIBRADOR, SHUTDOWN, \
    MODULO_RECUENTO, MODULO_INICIO, RESTART, MODULO_TOTALIZADOR
from msa.voto.settings import VOLUMEN_GENERAL


def get_options():
    parser = OptionParser()
    parser.add_option('-c', '--calibrate', action='store_true', default=False,
                      help='Run the calibration software before')
    parser.add_option("-m", "--modulo", default=None)
    parser.add_option("-u", "--ubicacion", default=None)
    return parser.parse_args()[0]


if __name__ == '__main__':
    modulos_startup = [MODULO_INICIO]
    options = get_options()

    levantar_locales()

    # NO INVERTIR EL ORDEN en que se apilan los módulos, porque
    # la calibración está antes que nada (por ende va último en la lista)
    if options.calibrate:
        modulos_startup.append(MODULO_CALIBRADOR)

    # Asigno cada clase de un modulo a un diccionario, luego las instancio
    # desde ahi mismo.
    modulos_aplicacion = {
        MODULO_INICIO: ["inicio", "ModuloInicio"],
        MODULO_REINICIO: ["inicio", "ModuloReinicio"],
        MODULO_ADMIN: ["administrador", "ModuloAdministradorWeb"],
        MODULO_APERTURA: ["apertura", "ModuloApertura"],
        MODULO_RECUENTO: ["recuento", "ModuloRecuento"],
        MODULO_TOTALIZADOR: ["totalizador", "ModuloTotalizador"],
        MODULO_VOTO: ["voto", "ModuloVoto"],
        MODULO_ASISTIDA: ["asistida", "ModuloAsistida"],
        MODULO_DEMO: ["demo", "ModuloDemo"],
        MODULO_EXPULSAR_BOLETA: ["modulos_impresora", "ModuloExpulsarBoleta"],
        MODULO_CALIBRADOR: ["calibrador", "CalibradorPantalla"]
    }

    # Seteo el volumen del audio al maximo antes de iniciar
    audioplayer = WavPlayer(as_daemon=False)
    audioplayer.set_volume(VOLUMEN_GENERAL)
    audioplayer.close()

    if options.modulo is None:
        modulo = modulos_startup.pop()
    else:
        modulo = options.modulo

    if options.ubicacion is not None:
        from msa.core.data import Ubicacion
        from msa.voto.sesion import get_sesion

        sesion = get_sesion()
        sesion.mesa = Ubicacion.one(options.ubicacion)

    ejecutar = True
    res = ''
    while ejecutar:
        # Instancio una clase, y ejecuto su metodo main()
        # Este metodo debe devolver un string si quiere llamar a otro modulo
        paquete, nombre_mod = modulos_aplicacion[modulo]
        paquete = import_module(".%s" % paquete, "msa.voto.modulos")
        mod = getattr(paquete, nombre_mod)()
        res = mod.main()

        # Paso la escoba para evitar el leak de las imágenes de los candidatos
        # esto es quizá redundante, dados los pasos similares en ModuloVoto,
        # pero necesario.
        if hasattr(mod, 'pantalla'):
            if hasattr(mod.pantalla, 'botones'):
                del mod.pantalla.botones
            del mod.pantalla
        del mod
        gc.collect()

        if modulos_startup:
            modulo = modulos_startup.pop()
        # Si no vengo de un calibrador y el retorno es volver a inicio, restart
        # o apagar, salgo
        elif (not modulo.startswith(MODULO_CALIBRADOR)) and \
             (res in (MODULO_INICIO, RESTART, SHUTDOWN)):
            ejecutar = False
        elif res in modulos_aplicacion:
            modulo = res

    if res == SHUTDOWN:
        os.system('eject /dev/sr0 -i off; eject /dev/sr0')
        os.system('poweroff')
