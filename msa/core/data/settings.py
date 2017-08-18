from os.path import join

from msa.constants import PATH_VARS

# settings de juego de datos

# Juego de datos activo
JUEGO_DE_DATOS = 'salta_paso_2017'
JUEGO_DE_DATOS = 'salta_paso_2017'

EXT_IMG_VOTO = "jpg"

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
