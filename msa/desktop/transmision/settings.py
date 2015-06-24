from os.path import join

from msa.settings import PATH_CODIGO


DEBUG = False
FULLSCREEN = False

PING_EVERY = 60  # seconds

PATH_TEMPLATE_TRANSMISION = ""


def actualizar_paths():
    global PATH_TEMPLATE_TRANSMISION
    PATH_TEMPLATE_TRANSMISION = join(PATH_CODIGO, "desktop", "transmision",
                                     "templates", "index.html")

PATH_NETWORK_CONF_APP = '/usr/bin/nm-connection-editor'

PATH_KEYS = './keys'
PATH_CERTS = './certs'
PATH_CA = './CA'

PATTERN_PKEY = '*.pkey'
PATTERN_CERT = '*.cert'

PATTERN_TAR_GZ = "*.tar.gz"
PATTERN_TGZ = "*.tgz"
PATTERN_GZ = "*.gz"

PROTOCOLO = "https"
CONFIG_FILE = './transmision.cfg'
UBIC_MODULO = "desktop/transmision/"

PROTOCOLO_CERTS = "https"
URL_LOGIN_CERTS = "/elecciones/ajax/login"


actualizar_paths()

try:
    from settings_local import *
except ImportError:
    pass
