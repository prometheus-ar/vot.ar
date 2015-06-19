# -*- coding: utf-8 -*-
import os

from msa.core.data.settings import JUEGO_DE_DATOS
from msa.settings import PATH_RECURSOS, PATH_FUENTES, PATH_CODIGO
from msa.voto.constants import BOTON_LISTA_COMPLETA, BOTON_VOTAR_POR_CATEGORIAS

# settings de paths de toda la aplicacion
PATH_RECURSOS_VOTO = None
PATH_IMAGENES_VOTO = None
PATH_SONIDOS_VOTO = None
PATH_LOCALE_VOTO = None
PATH_IMAGENES_BOTONES = None
PATH_FOTOS_ORIGINALES = None
PATH_TEMPLATES_VOTO = None
PATH_TONOS = None

def actualizar_paths():
    global PATH_RECURSOS_VOTO, PATH_IMAGENES_VOTO, PATH_SONIDOS_VOTO, \
    PATH_IMAGENES_BOTONES, PATH_LOCALE_VOTO, PATH_FOTOS_ORIGINALES, \
    PATH_TEMPLATES_VOTO, PATH_TONOS

    PATH_RECURSOS_VOTO = os.path.join(PATH_RECURSOS, 'voto')
    PATH_IMAGENES_VOTO = os.path.join(PATH_RECURSOS_VOTO, 'imagenes')
    PATH_SONIDOS_VOTO = os.path.join(PATH_RECURSOS_VOTO, 'sonidos')
    PATH_LOCALE_VOTO = os.path.join(PATH_RECURSOS_VOTO, 'locale')
    PATH_IMAGENES_BOTONES = os.path.join(PATH_IMAGENES_VOTO, 'botones',
                                         JUEGO_DE_DATOS)
    PATH_FOTOS_ORIGINALES = os.path.join(PATH_FUENTES, "imagenes_candidaturas")
    PATH_TEMPLATES_VOTO = os.path.join(PATH_CODIGO, "voto", "gui", "templates")
    PATH_TONOS = os.path.join(PATH_SONIDOS_VOTO, 'tonos')

USAR_CEF = False
DEBUG_ZAGUAN = False

# pantalla y temas
SCREEN_SIZE = 1366, 768
FONT = 'Ubuntu 11'
FULLSCREEN = True
MOSTRAR_CURSOR = False

# Para elecciones pequeñas no es necesario realizar Apertura de mesa
REALIZAR_APERTURA = True
USA_TILDES = False

# Poner en None para saltear la pantalla
BOTONES_SELECCION_MODO = (BOTON_VOTAR_POR_CATEGORIAS, BOTON_LISTA_COMPLETA)
BARRA_SELECCION = True
FLAVOR = "vanilla"

# extension de las imagenes de los candidatos
EXT_IMG_VOTO = "jpg"

# setting de aparicion de candidatos
MEZCLAR_CANDIDATOS = True
MEZCLAR_LISTAS = True
MEZCLAR_INTERNAS = True
MEZCLAR_CONSULTA = True
AGRUPAR_POR_PARTIDO = False
AGRUPAR_POR_ALIANZA = False

# VOLUMEN_GENERAL = -1 no hace cambios en el volumen
VOLUMEN_GENERAL = 100
USAR_ASISTIDA = True
USAR_TOTALIZADOR = False

# Efectos de transicion
EFECTOS_INICIO = False
EFECTOS_ADMIN = False
EFECTOS_VOTO = False
EFECTOS_RECUENTO = False

# Multilenguaje
SELECCIONAR_IDIOMA = False
IDIOMAS_DISPONIBLES = (
   ("Español", "es_AR"),
   ("English", "en_US"),
   ("Deutsch", "de_DE"),
   ("Português", "po_BR"),
)

# Minimo de boletas que debe tener cada recuento, para mostrar alerta en caso
# contrario
MINIMO_BOLETAS_RECUENTO = 10

# settings de reintentos de lectura y escritura
MARGEN_LECTURAS_ERRONEAS = 3
MARGEN_LECTURAS_CON_COLISION = 2
REINTENTOS_TAG_PERDIDO = 2
SEGUNDOS_ESPERA_ULTIMO_VOTO = 2
REINTENTOS_REGISTRADOR = 3
REINTENTOS_REGISTRADOR_MALATA = 5

DUMP_FILE_REINICIO = '/tmp/last_state.tmp'

# Timeouts Varios
# cada cuanto leo el lector para verificar si hay un tag.
SCAN_DELAY = 400
# El tiempo a esperar entre que empieza la impresion y se vuelve a mostrar la
# pantalla inicial.
TIMEOUT_FINAL = 5000
# El tiempo a esperar entre que empieza la impresion  y se vuelve a mostrar la
# pantalla inicial en demo.
TIMEOUT_FINAL_DEMO = 7000

TIMEOUT_WATCHDOG = 2000

# en segundos. 0 para que no se duerma nunca
TIEMPO_REPOSO_MONITOR = 0

try:
    from msa.voto.settings_local import *
except ImportError, e:
    pass

actualizar_paths()
