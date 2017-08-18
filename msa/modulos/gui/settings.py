DEBUG_ZAGUAN = False
WEBKIT_VERSION = 2

# pantalla y temas
SCREEN_SIZE = 1366, 768
FULLSCREEN = True
MOSTRAR_CURSOR = False
USAR_SONIDOS_UI = True

try:
    from msa.modulos.gui.settings_local import *
except ImportError as e:
    pass
