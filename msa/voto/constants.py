# coding: utf-8
FONT_NAME = 'Nimbus Sans L'
try:
    import pango
    DEFAULT_FONT = pango.FontDescription(FONT_NAME)
except ImportError:
    DEFAULT_FONT = None

from msa.core.constants import CIERRE_RECUENTO, CIERRE_TRANSMISION, \
    CIERRE_ESCRUTINIO

BOTON_VOTAR_POR_CATEGORIAS = "BTN_CATEG"
BOTON_LISTA_COMPLETA = "BTN_COMPLETA"
BOTON_VOTAR_EN_BLANCO = "BTN_BLANCO"

EXT_IMAGENES_BOTONES = '.png'

MSG_BOLETA_OK = 'BOLETA_OK'
MSG_CANCELAR = 'CANCELAR'
MSG_COMENZAR = 'COMENZAR'
MSG_CONFIGURAR = 'CONFIGURAR'
MSG_CONFIRMAR = 'CONFIRMAR'
MSG_FIN_REGISTRO = 'FIN REGISTRO'
MSG_INSERTAR_BOLETA = 'INSERTAR_BOLETA'
MSG_REGISTRAR = 'REGISTRAR'
MSG_REINICIO_VOTO = 'REINICIO VOTO'
MSG_REVISAR = 'REVISAR'
MSG_SELECCIONAR_INTERNA = 'SELECCIONAR INTERNA'
MSG_SELF = 'SELF'
MSG_SETVOLVER = 'SETVOLVER'

MODULO_ADMIN = "admin"
MODULO_APERTURA = "apertura"
MODULO_ASISTIDA = "asistida"
MODULO_CALIBRADOR = "calibrador_pantalla"
MODULO_DEMO = "demo"
MODULO_EXPULSAR_BOLETA = "expulsar_boleta"
MODULO_INICIO = "inicio"
MODULO_RECUENTO = "recuento"
MODULO_REINICIO = "reinicio"
MODULO_TOTALIZADOR = "totalizador"
MODULO_VOTO = "voto"

RESTART = "restart"
SHUTDOWN = "shutdown"

TIPO_BTN_CANDIDATO = 1
TIPO_BTN_PRESEL = 2

NOMBRE_PO_VOTO = "voto"

CONFIG_BOLETA_APERTURA = {
    'tipo': 'apertura',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#f9c33d',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#fef0cc',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#f9c33d',
    },
    'vot_ar': {
        'fill': '#ffffff'
    },
    'legend': {
        'fill': '#ffffff'
    },
}

CONFIG_BOLETA_CIERRE = {
    'tipo': 'cierre',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#61b9e7',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#d9edf9',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#ffffff',
    },
    'vot_ar': {
        'fill': '#ffffff'
    },
    'legend': {
        'fill': '#ffffff'
    },
}

CONFIG_BOLETA_ESCRUTINIO = {
    'tipo': 'escrutinio',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#ffffff',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#ecf6fc',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#61b9e7',
    },
    'vot_ar': {
        'fill': '#61b9e7'
    },
    'legend': {
        'fill': '#61b9e7'
    },
}

CONFIG_BOLETA_TRANSMISION = {
    'tipo': 'transmision',
    'width': 600,
    'height': 1030,
    'style': 'stroke:#cccccc;stroke-width:1;',
    'top_rect': {
        'x': 30,
        'y': 40,
        'width': 529,
        'height': 540,
        'fill': '#ffffff',
    },
    'bottom_rect': {
        'x': 30,
        'y': 575,
        'width': 529,
        'height': 455,
        'fill': '#ecf6fc',
    },
    'flecha': {
        'fill': '#f9c33d',
    },
    'vot_ar': {
        'fill': '#f9c33d'
    },
    'legend': {
        'fill': '#f9c33d'
    },
}

PANTALLA_INSERCION_BOLETA = "insercion_boleta"
PANTALLA_SELECCION_INTERNA = "seleccion_interna"
PANTALLA_SELECCION_CANDIDATOS = "seleccion_candidatos"
PANTALLA_AGRADECIMIENTO = "agradecimiento"
PANTALLA_MENSAJE_FINAL = "mensaje_final"
PANTALLA_CONSULTA = "consulta"
PANTALLA_BOLETA_INSERTADA = "boleta_insertada"

RECUENTO_OK = 0
RECUENTO_ERROR = 1
RECUENTO_ERROR_REPETIDO = 2
RECUENTO_NO_TAG = 3
RECUENTO_VER_RESULTADOS = 4
RECUENTO_RECUENTO_OK = 5
RECUENTO_RECUENTO_ERROR = 6
RECUENTO_IMPRIMIENDO = 7
RECUENTO_GENERANDO = 8

# Cantidad de suplentes ademas del presidente en las autoridades de mesa
CANTIDAD_SUPLENTES = 1

TIPO_DOC = ["DNI", "LC", "LE"]

NUMEROS_TEMPLATES = {"vanilla": [2, 4, 6, 9, 12, 16, 20, 24, 30, 36],
                     "empanada": [2, 3, 4, 6, 8, 10, 12, 15, 18, 21,
                                  24, 28, 32, 36],
                     "soja": [8, ],
                     "caipirinha": [2, 4, 6, 9, 12, 16, 20, 24, 30, 36]}

INCREMENTO_VOLUMEN = 10
DECREMENTO_VOLUMEN = 10

INCREMENTO_BRILLO = 20
DECREMENTO_BRILLO = 20

POTENCIA_ALTA = "Full"
POTENCIA_BAJA = "Half"

INTERVALO_REFRESCO = 10000
INTERVALO_REFRESCO_BATERIA = 10000

TIEMPO_DESACTIVACION_CHEQUEO = 10000

BATTERY_THRESHOLD = 100

SECUENCIA_CERTIFICADOS = [CIERRE_RECUENTO,  CIERRE_TRANSMISION,
                          CIERRE_ESCRUTINIO]
SECUENCIA_CERTIFICADOS_TOTALIZACION = [CIERRE_TRANSMISION,
                                       CIERRE_ESCRUTINIO]

COMANDO_MD5 = 'cd %s ; LC_ALL=C md5sum -c md5sum.txt | grep -v "casper_%s\|isolinux\|.disk\|OK$"'

WINDOW_BORDER_WIDTH = 12
APP_TITLE = "PyVoto"

# ESTADOS DE LA RAMPA

# COMUNES
E_ESPERANDO = "ESPERANDO"
E_ESPERANDO_TAG = "ESPERANDO_TAG"
E_EXPULSANDO_BOLETA = "EXPULSANDO_BOLETA"
E_INICIAL = "INICIAL"

# VOTO
E_VOTANDO = "VOTANDO"
E_CONSULTANDO = "CONSULTANDO"
E_CONSULTANDO_CON_PAPEL = "CONSULTANDO_CON_PAPEL"
E_REGISTRANDO = "REGISTRANDO"

# APERTURA
E_CARGA = "CARGA"
E_CONFIRMACION = "CONFIRMACION"

# INICIO
E_EN_CONFIGURACION = "EN_CONFIGURACION"
E_CONFIGURADA = "CONFIGURADA"

# RECUENTO
E_SETUP = "SETUP"
E_RECUENTO = "RECUENTO"
E_RESULTADO = "RESULTADO"
E_VERIFICACION = "VERIFICACION"

# INGRESO_DATOS
E_INGRESO_ACTA = "ESPERANDO_INGRESO_ACTA"
E_MESAYPIN = "INGRESO_MESA_Y_PIN"
E_INGRESO_DATOS = "INGRESO_DATOS_AUTORIDADES"
