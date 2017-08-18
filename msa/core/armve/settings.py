from __future__ import absolute_import
# Puerto serie a utilizar cuando pyudev no encuentra un device
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_TIMEOUT = 0.2

AUTOFEED_1_MOVE = -128
AUTOFEED_2_MOVE = 8

# Rellena todos los bytes que no se escriben en el chip con "\x00" y pisa
# cualquier cosa que hubiera en su lugar
ESCRIBIR_TODOS_BLOQUES = True
# si el firmare es >= 2.1.0 usa la nueva funcion de carga de buffer de
# impresion solo si esta setting está en True. Sino usa la anterior aunque el
# firmware lo soporte
USAR_IMPRESION_V2 = False

DEBUG = False

try:
    from msa.core.armve.settings_local import *
except ImportError:
    pass
