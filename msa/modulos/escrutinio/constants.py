"""Constants del modulo escrutinio."""
from msa.core.documentos.constants import (CIERRE_ESCRUTINIO, CIERRE_RECUENTO,
                                           CIERRE_TRANSMISION)


SECUENCIA_CERTIFICADOS = [CIERRE_RECUENTO,  CIERRE_TRANSMISION,
                          CIERRE_ESCRUTINIO]


# Minimo de boletas que debe tener cada recuento, para mostrar alerta en caso
# contrario
MINIMO_BOLETAS_RECUENTO = 10

ACT_INICIAL = 0
ACT_BOLETA_NUEVA = 1
ACT_BOLETA_REPETIDA = 2
ACT_ERROR = 3
ACT_ESPECIALES = 4
ACT_CLONADA = 5

TEXTOS = (
    "cargando_interfaz", "espere_por_favor", "boletas_procesadas",
    "bienvenida_recuento", "boleta_repetida", "error_lectura",
    "finalizar_recuento", "aceptar", "cancelar", "seguro_salir_escrutinio",
    "seguro_salir_escrutinio_aclaracion", "pocas_boletas_alerta",
    "pocas_boletas_pregunta", "pocas_boletas_aclaracion", "total_general",
    "fin_escrutinio_pregunta", "fin_escrutinio_aclaracion", "volver",
    "introduzca_acta_cierre", "introduzca_acta_transmision",
    "palabra_siguiente", "recuento_no_almacenado_alerta",
    "palabra_anterior", "palabra_finalizar", "imprimir_actas",
    "recuento_no_almacenado_aclaracion", "mensaje_imprimiendo",
    "transmision_no_almacenada_alerta", "imprimiendo_acta",
    "transmision_no_almacenada_aclaracion", "continuar_recuento",
    "certificado_no_impreso_alerta", "certificado_no_impreso_aclaracion",
    "introduzca_acta_escrutinio", "introduzca_acta_recuento",
    "asegurese_firmar_acta", "el_suplente_acercara", "usted_puede_imprimir",
    "fiscales_qr", "introduzca_certificado_boletas", "palabra_lista",
    "introduzca_sobre_actas", "introduzca_certificados_para_fiscales",
    "lista_actas_sobre", "lista_otras_actas", "padrones_electorales",
    "otros_votos", "poderes_fiscales", "certificado_de_escrutinio",
    "boletas_votos_nulos", "introducir_urna", "cerrar_faja_seguridad",
    "palabra_siguiente", "mensaje_copias", "seguro_salir_totalizador",
    "finalizar_totalizacion", "bienvenida_totalizador", "acta_repetida",
    "continuar_totalizacion", "apagar", "titulo_confirmacion_apagado",
    "recuerde_remover_disco", "boleta_clonada", "contacte_autoridades"
)
