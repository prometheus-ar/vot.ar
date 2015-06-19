# -*- coding: utf-8 -*-
import os

from msa.core.constants import LECTOR_TEXAS
from msa.settings import PATH_RECURSOS, PATH_CODIGO
from msa.core.armve.helpers import is_armve_capable

# Settings para numpacker
CANTIDAD_BITS_PACKER = 9  # Cantidad de bits por numero en numpacker
FAST_PACKING = False  # Indica si se usan las funciones rápidas para
                      # pack|unpack
SMART_PACKING = True  # Indica si se usan las funciones de smart packing

# settings para rfid
TOKEN = '1C'
COMPROBAR_TOKEN = True
# desplazamiento de boleta en la impresora para sacarla o volverla al lector
DESPLAZAMIENTO_BOLETA = 10
DEBUG_RFID = False
SCAN_DELAY = 400
# Lector y Tags con los que trabaja el sistema
CLASE_LECTOR = LECTOR_TEXAS
USA_ARMVE = is_armve_capable()

DBUS_ARMVE_PATH = '/ar/com/msa/VotAr/ARMVE'
DBUS_BUSNAME_ARMVE = 'ar.com.msa.VotAr.ARMVE'

# settings para DBUS
if not USA_ARMVE:
    DBUS_BUSNAME_RFID = 'ar.com.msa.VotAr.rfid'
    DBUS_BUSNAME_PRINTER = 'ar.com.msa.VotAr.printer'
    DBUS_BUSNAME_BACKLIGHT = 'ar.com.msa.VotAr.backlight'
    DBUS_BUSNAME_POWERMANAGER = 'ar.com.msa.VotAr.powermanager'
    DBUS_BUSNAME_AGENT = 'ar.com.msa.VotAr.agent'
    DBUS_BUSNAME_FANCOOLERS = 'ar.com.msa.VotAr.fancoolers'
    DBUS_BUSNAME_PIR = 'ar.com.msa.VotAr.pir'

    # paths
    DBUS_LECTOR_PATH = '/ar/com/msa/VotAr/Lectores/lector0'
    DBUS_IMPRESORA_PATH = '/ar/com/msa/VotAr/Impresoras/printer0'
    DBUS_BACKLIGHT_PATH = '/ar/com/msa/VotAr/Backlight'
    DBUS_POWERMANAGER_PATH = '/ar/com/msa/VotAr/PowerManager'
    DBUS_AGENT_PATH = '/ar/com/msa/VotAr/Agent'
    DBUS_FANCOOLERS_PATH = '/ar/com/msa/VotAr/FanCoolers'
    DBUS_PIR_PATH = '/ar/com/msa/VotAr/PIR'
else:
    DBUS_BUSNAME_RFID = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_PRINTER = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_BACKLIGHT = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_POWERMANAGER = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_AGENT = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_FANCOOLERS = DBUS_BUSNAME_ARMVE
    DBUS_BUSNAME_PIR = DBUS_BUSNAME_ARMVE

    # paths
    DBUS_LECTOR_PATH = DBUS_ARMVE_PATH
    DBUS_IMPRESORA_PATH = DBUS_ARMVE_PATH
    DBUS_BACKLIGHT_PATH = DBUS_ARMVE_PATH
    DBUS_POWERMANAGER_PATH = DBUS_ARMVE_PATH
    DBUS_AGENT_PATH = DBUS_ARMVE_PATH
    DBUS_FANCOOLERS_PATH = DBUS_ARMVE_PATH
    DBUS_PIR_PATH = DBUS_ARMVE_PATH


# settings para QR codes
USAR_QR = True
QR_PIXEL_SIZE = 10
QR_ERROR_LEVEL = 'Q'
# nivel | % de error recuperable
# L     | 7%
# M     | 15%
# Q     | 25%
# H     | 30%

PATH_RECURSOS_CORE = ''
PATH_IMAGENES_CORE = ''
PATH_IPC = ''
PATH_IPC_SERVER = ''
PATH_TEMPLATES_BOLETAS = ''


def actualizar_paths():
    global PATH_RECURSOS_CORE, PATH_IMAGENES_CORE, PATH_IPC, PATH_IPC_SERVER, \
        PATH_TEMPLATES_BOLETAS

    PATH_RECURSOS_CORE = os.path.join(PATH_RECURSOS, 'core')
    PATH_IMAGENES_CORE = os.path.join(PATH_RECURSOS_CORE, 'imagenes')
    PATH_IPC = os.path.join(PATH_CODIGO, 'core', 'ipc')
    PATH_TEMPLATES_BOLETAS = os.path.join(PATH_CODIGO, 'core', 'imaging',
                                          'templates')
    PATH_IPC_SERVER = os.path.join(PATH_IPC, 'server')

# cosas de impresion
ACTA_DESGLOSADA = False

IMPRESION_HD_APERTURA = True
IMPRESION_HD_CIERRE = True
IMPRESION_HD_BOLETAS = USA_ARMVE

USAR_CYTHON = False
IMPRESION_USBLP = False
COMPRESION_IMPRESION = False
USAR_BUFFER_IMPRESION = False

USB_PRINTER_VENDOR_ID = 0x0dd4
USB_PRINTER_PRODUCT_ID = 0x014c

# Pausa entre frases, en segundos
SPEECH_PAUSE = 3

USAR_PIR = True
USAR_FAN = True
ITERACIONES_APAGADO = 12

# Brillo en armve
DEFAULT_BRIGHTNESS = 80

# Potencia de la antena (armve). Full (255)/Half (0)
RFID_POWER = 0

try:
    from msa.core.settings_server import *
except ImportError:
    pass

try:
    from msa.core.settings_local import *
except ImportError:
    pass

actualizar_paths()
