"""Settings para el calibrador."""
TEST = False
FAKE = False

DEBUG = False

NPOINTS = 4
MISCLICK_THRESHOLD = 30
DUALCLICK_THRESHOLD = 100

# Timeout in milliseconds
TIMEOUT = 0

FAST_START = True
AUTO_CLOSE = True

try:
    from msa.modulos.calibrador.settings_local import *
except ImportError:
    pass
