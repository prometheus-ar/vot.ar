# -*- coding: utf-8 -*-

# settings para rfid
TOKEN = '6A'
TOKEN_TECNICO = '3C'
COMPROBAR_TOKEN = True

# cosas de impresion
COMPRESION_IMPRESION = False
USAR_BUFFER_IMPRESION = False

try:
    from msa.core.settings_local import *
except ImportError as e:
    pass
