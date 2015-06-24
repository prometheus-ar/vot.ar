# Puerto serie a utilizar cuando pyudev no encuentra un device
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_TIMEOUT = 0.2

AUTOFEED_1_MOVE = -128
AUTOFEED_2_MOVE = 8

FALLBACK_2K = False

DEBUG = False

try:
    from msa.core.armve.settings_local import *
except ImportError:
    pass
