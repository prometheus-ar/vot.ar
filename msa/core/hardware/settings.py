# -*- coding: utf-8 -*-
from __future__ import absolute_import

USAR_PIR = False
USAR_FAN = True
ITERACIONES_APAGADO = 12

# Brillo en armve
DEFAULT_BRIGHTNESS = 80

# Potencia de la antena (armve). Full (255)/Half (0)
RFID_POWER = 0

try:
    from msa.core.hardware.settings_local import *
except ImportError:
    pass
