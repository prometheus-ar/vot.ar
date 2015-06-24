# -*- coding:utf-8 -*-
import os

DEBUG = False
MODO_DEMO = True
QUEMA = True

PATH_CODIGO = '/cdrom/app/msa/'  # poner la barra al final
PATH_REPO_RECURSOS = '/opt/eleccion_recursos/'

PATH_FUENTES = ''
PATH_RECURSOS = ''
PATH_TTS = ''
PATH_CERTS = ''
PATH_CD = ''


def actualizar_paths():
    global PATH_FUENTES, PATH_DATOS_JSON, PATH_RECURSOS, PATH_TTS, \
        PATH_CERTS, PATH_CD

    PATH_RECURSOS = os.path.join(PATH_CODIGO, 'recursos')
    PATH_TTS = os.path.join(PATH_RECURSOS, 'tts')
    PATH_FUENTES = os.path.join(PATH_RECURSOS, 'fuentes')
    PATH_CERTS = os.path.join(PATH_RECURSOS, 'keys')
    PATH_CD = '/cdrom'

DEFAULT_LOCALE = "es_AR"

# Este parámetro indica si se corre en modo de categoría única, y en caso de
# ser así, indicar el codigo de la categoría sino, dejar en None.
COD_CATEGORIA_UNICA = None

FECHA = '01/26/2012'  # Fecha en formato MM/dd/AAAA

try:
    from msa.settings_logging import *
except ImportError:
    pass

try:
    from msa.settings_local import *
except ImportError:
    pass

actualizar_paths()
