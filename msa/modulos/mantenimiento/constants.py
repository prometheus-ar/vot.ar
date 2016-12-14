"""Constatnes del modulo mantenimiento."""
INCREMENTO_FAN = 10
DECREMENTO_FAN = 10

INCREMENTO_BRILLO = 20
DECREMENTO_BRILLO = 20

POTENCIA_ALTA = "Full"
POTENCIA_BAJA = "Half"

INTERVALO_REFRESCO = 10000
INTERVALO_REFRESCO_BATERIA = 10000

TIEMPO_DESACTIVACION_CHEQUEO = 10000

BATTERY_THRESHOLD = 100

COMANDO_MD5 = 'cd %s ; LC_ALL=C md5sum -c md5sum.txt | grep -v "casper_\|isolinux\|.disk\|OK$"'

TEXTOS = (
    "titulo_menu", "totalizacion", "apertura_de_mesa",
    "sistema_boleta_electronica", "cierre_y_escrutinio", "reiniciar",
    "version_demo", "votacion_asistida", "expulsar_boleta", "salir", "mesa",
    "mantenimiento", "auto", "manual", "rfid", "titulo_mantenimiento",
    "volumen", "brillo", "gestion_energia", "version_firmware",
    "chequeo_rfid", "volver_al_inicio", "potencia_rfid", "temperatura",
    "iniciar_chequeo", "modo_ventilador", "no_hay_tag",
    "descripcion_chequeo_rfid", "cargando", "expulsar_cd", "estado_pir",
    "pir_prendido", "pir_apagado", "pir", "cancelar", "pir_activado",
    "pir_desactivado", "chequeo_cd", "prueba_impresora", "aceptar",
    "reset_devices", "modo_autofeed", "seleccione_boleta", "edicion_2013",
    "edicion_2015", "autodetectar", "calidad_impresion", "cargando_interfaz",
    "agente", "espere_por_favor", "tipo_de_boleta", "impresora",
    "titulo_reiniciar_dispositivos", "alta", "muy_alta",
    "titulo_calidad_impresion", "muy_baja", "baja", "media", "texto_md5",
)
