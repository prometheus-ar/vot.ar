# coding: utf-8
from os.path import join

from msa.settings import PATH_CODIGO

# OJO: No juntar los imports
from msa.core.data.constants import NOMBRE_JSON_MESAS_1 as MESAS

# settings relativas a los datos y como se muestran
NOMBRE_JSON_MESAS = MESAS

# settings de juego de dato
JUEGO_DE_DATOS = 'demo_caba_generales_2015'
# lista de los juegos de datos presentes en el branch
# (se usa en el generador CSV)

PREFIJO_PROVINCIA = 'CABA'

JUEGOS_DE_DATOS_ACTIVOS = {
    'caba_generales_2015':
    {'jerarquia_ubicaciones': ['Distrito',
                               'Comuna',
                               'Circuito',
                               'Establecimiento',
                               'Mesa'],
     'jerarquia_candidaturas': ['Partido',
                                'Lista',
                                'Candidato'],
     'generar_dhont': False,
     'generar_adhesiones': False,
     'generar_adhesiones_cargos': False,
     'generar_nocargoubicacion': False},
    'demo_caba_generales_2015':
    {'jerarquia_ubicaciones': ['Distrito',
                               'Comuna',
                               'Circuito',
                               'Establecimiento',
                               'Mesa'],
     'jerarquia_candidaturas': ['Partido',
                                'Lista',
                                'Candidato'],
     'generar_dhont': False,
     'generar_adhesiones': False,
     'generar_adhesiones_cargos': False,
     'generar_nocargoubicacion': False}
}

# Nombre de la DB intermedia para los CSVs
DATALOADER_DB = 'origen_csv'

# Niveles compresión:
# 0 - Sin compresión: 001.001
# 1 - Sin padding: 1.1
# 2 - Sin padding y nros en hexa: b.b
COMPRESION_ID_JERARQUICO = 1

# Indica si el último tramo del id_jerarquico de ubicaciones
# representa el id único de la mesa
ID_UNICO_MESA = True

# Indica si los candidatos suplentes van al JSON (si no se van a mostrar
# en pantalla ésto ahorra espacio)
GENERAR_JSON_SUPLENTES = True

DEFAULT_PIN_DEMO = "ABC123"

PATH_DATOS_JSON = ''


def actualizar_paths():
    global PATH_DATOS_JSON
    PATH_DATOS_JSON = join(PATH_CODIGO, 'datos_json', JUEGO_DE_DATOS)

try:
    from msa.core.data.settings_local import *
except ImportError:
    pass

actualizar_paths()
