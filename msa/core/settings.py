# -*- coding: utf-8 -*-

# settings para rfid
TOKEN = '74'
TOKEN_TECNICO = '73'
COMPROBAR_TOKEN = True
USAR_SALT = True

# desplazamiento de boleta en la impresora para sacarla o volverla al lector
DESPLAZAMIENTO_BOLETA = 10  #TODO: esta variable podria ser eliminada a partir
# de la muerte de Malata

# cosas de impresion
COMPRESION_IMPRESION = False
USAR_BUFFER_IMPRESION = False

try:
    from msa.core.settings_local import *
except ImportError as e:
    pass
