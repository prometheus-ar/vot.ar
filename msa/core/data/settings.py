# coding: utf-8
from os.path import join

from msa.constants import PATH_VARS

# OJO: No juntar los imports
from msa.core.data.constants import NOMBRE_JSON_MESAS_DEFINITIVO as MESAS

# settings relativas a los datos y como se muestran
NOMBRE_JSON_MESAS = MESAS

# settings de juego de datos

# Juego de datos activo
JUEGO_DE_DATOS = 'santarosa_municipales_2016'

EXT_IMG_VOTO = "jpg"
DEFAULT_PIN_CAPACITACION = "AB@12CD="

PATH_DATOS_JSON = ''
PATH_CARPETA_DATOS = ''

def actualizar_paths():
    global PATH_DATOS_JSON
    global PATH_CARPETA_DATOS
    PATH_CARPETA_DATOS = join(PATH_VARS, 'datos')
    PATH_DATOS_JSON = join(PATH_CARPETA_DATOS, JUEGO_DE_DATOS)

try:
    from msa.core.data.settings_local import *
except ImportError:
    pass

actualizar_paths()
