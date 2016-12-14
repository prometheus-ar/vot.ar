"""Constantes del modulo sufragio."""
from msa.modulos.constants import (MODULO_APERTURA, MODULO_ASISTIDA,
                                   MODULO_CAPACITACION, MODULO_INICIO,
                                   MODULO_MANTENIMIENTO, MODULO_MENU,
                                   MODULO_RECUENTO, MODULO_SUFRAGIO,
                                   MODULO_TOTALIZADOR,
                                   SUBMODULO_DATOS_APERTURA,
                                   SUBMODULO_DATOS_ESCRUTINIO,
                                   SUBMODULO_MESA_Y_PIN_INICIO)

MODULOS_APLICACION = [MODULO_APERTURA, MODULO_ASISTIDA,
                      MODULO_CAPACITACION, MODULO_INICIO, MODULO_MANTENIMIENTO,
                      MODULO_MENU, MODULO_RECUENTO, MODULO_TOTALIZADOR,
                      MODULO_SUFRAGIO, SUBMODULO_MESA_Y_PIN_INICIO,
                      SUBMODULO_DATOS_APERTURA, SUBMODULO_DATOS_ESCRUTINIO]

BOTON_VOTAR_POR_CATEGORIAS = "BTN_CATEG"
BOTON_LISTA_COMPLETA = "BTN_COMPLETA"
BOTON_VOTAR_EN_BLANCO = "BTN_BLANCO"

PANTALLA_INSERCION_BOLETA = "insercion_boleta"
PANTALLA_SELECCION_INTERNA = "seleccion_interna"
PANTALLA_SELECCION_CANDIDATOS = "seleccion_candidatos"
PANTALLA_AGRADECIMIENTO = "agradecimiento"
PANTALLA_MENSAJE_FINAL = "mensaje_final"
PANTALLA_CONSULTA = "consulta"
PANTALLA_BOLETA_INSERTADA = "boleta_insertada"

IDIOMAS_DISPONIBLES = (
    ("Español", "es_AR"),
)


NUMEROS_TEMPLATES = {
    "vanilla": [2, 4, 6, 9, 12, 16, 20, 24, 30, 36],
    "empanada": [2, 3, 4, 6, 9, 12, 16, 21, 24, 30, 36],
    "soja": [8, ],
    "milanga": [2, 4, 6, 9, 12, 16],
    "medialuna": [2, 3, 4]
}

TEXTOS = (
    "conformar_voto", "si_confirmar_voto", "no_confirmar_voto",
    "votar_por_categorias", "votar_lista_completa", "su_seleccion",
    "votar_en_blanco", "confirmar_voto", "alto_contraste", "introduzca_boleta",
    "si_tiene_dudas", "su_voto_impreso", "muchas_gracias",
    "puede_retirar_boleta", "si_desea_verificarla", "imprimiendo_voto",
    "no_retirar_boleta", "agradecimiento", "este_es_su_voto",
    "volver_al_inicio", "aguarde_unos_minutos", "seleccionar_idioma",
    "aceptar", "cancelar", "confirmar_seleccion", "cargando_interfaz",
    "espere_por_favor", "no_olvide_verificar", "palabra_lista",
    "sus_candidatos", "candidato_no_seleccionado", "verificando_seleccion",
    "cambiar_modo_votacion", "salir_al_menu", "seleccione_accion",
    "error_grabar_boleta_alerta", "error_grabar_boleta_aclaracion", "si_desea_verificarla_alto_cotraste",
    "cinta_capacitacion", "cinta_demostracion", "modificar"
)
