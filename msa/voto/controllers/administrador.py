# -*- coding: utf-8 -*-
"""
Modulo Administrador.
Es el menú principal de la aplicación.
"""

import gobject
import json
import os

from time import sleep

from zaguan import WebContainerController
from zaguan.actions import BaseActionController
from zaguan.functions import asynchronous_gtk_message

from msa.core import get_config
from msa.core.settings import USA_ARMVE
from msa.core.armve.constants import AUTOFEED_1, AUTOFEED_2, \
    AUTOFEED_SELECT, DEV_AGENT, DEV_PRINTER, DEV_RFID, PRINT_SLOW, \
    PRINT_LOW, PRINT_MID, PRINT_HIGH, PRINT_SHIGH, PRINT_STEP
from msa.core.audioplayer import WavPlayer
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.core.temperature import get_temp
from msa.voto.constants import INCREMENTO_BRILLO, DECREMENTO_BRILLO, \
    INCREMENTO_VOLUMEN, DECREMENTO_VOLUMEN, POTENCIA_ALTA, \
    POTENCIA_BAJA, INTERVALO_REFRESCO, INTERVALO_REFRESCO_BATERIA, \
    TIEMPO_DESACTIVACION_CHEQUEO, BATTERY_THRESHOLD
from msa.settings import PATH_CD
from msa.voto.sesion import get_sesion
from msa.voto.settings import MOSTRAR_CURSOR, EFECTOS_ADMIN, \
    PATH_SONIDOS_VOTO, VOLUMEN_GENERAL, USAR_ASISTIDA, USAR_TOTALIZADOR, \
    PATH_TEMPLATES_VOTO


_audio_player = None


class Actions(BaseActionController):

    """Actions para el controller del administrador."""

    def document_ready(self, data):
        self.controller.parent._inicio()

    def load_maintenance(self, data):
        self.controller.parent._set_maintenance_mode()
        self.controller.inicio_mantenimiento()

    def click_boton(self, data):
        asynchronous_gtk_message(self.controller.parent._btn_presionado)(data)

    def volume(self, data):
        self.controller.set_volume(data)

    def brightness(self, data):
        self.controller.set_brightness(data)

    def check_rfid(self, data):
        self.controller.rfid_check(data)

    def check_fan(self, data):
        self.controller.fan_check()

    def fan_auto_mode(self, data):
        self.controller.set_fan_auto_mode(data)

    def fan_speed(self, data):
        self.controller.process_fan_speed(data)

    def eject_cd(self, data):
        self.controller.eject_cd()

    def printer_test(self, data):
        self.controller.parent.printer_begin_test()

    def printer_test_cancel(self, data):
        self.controller.parent.printer_end_test()

    def pir_mode(self, data):
        self.controller.set_pir_mode(data)

    def md5check(self, data):
        self.controller.md5check()

    def autofeed_mode(self, data):
        self.controller.set_autofeed_mode(data)

    def get_autofeed_mode(self, data):
        self.controller.get_autofeed_mode()

    def reset_device(self, data):
        self.controller.reset_device(data)

    def print_quality(self, data):
        self.controller.set_print_quality(data)

    def get_print_quality(self, data):
        self.controller.get_print_quality()

    def refresh(self, data):
        self.controller.get_temperature()
        self.controller.get_fan_speed()
        self.controller.get_fan_mode(True)
        self.controller.get_power_source()

    def refresh_batteries_status(self, data):
        self.controller.get_battery_status()

    def log(self, data):
        self.sesion.logger.debug("LOG >>> %s" % data)


class ControllerAdmin(WebContainerController):

    """Controller para la interfaz web de voto."""

    def __init__(self, parent):
        global _audio_player
        super(ControllerAdmin, self).__init__()
        self.sesion = get_sesion()
        self.parent = parent
        self.interna = None
        self.add_processor("admin", Actions(self))

        if not _audio_player or not _audio_player.is_alive():
            _audio_player = WavPlayer()
            _audio_player.start()
            _audio_player.set_volume(VOLUMEN_GENERAL)
        self._player = _audio_player

    def cargar_botones(self, mesa_abierta):
        self.send_command("mostrar_pantalla",
                          {'mesa_abierta': mesa_abierta,
                           'USAR_ASISTIDA': USAR_ASISTIDA,
                           'USAR_TOTALIZADOR': USAR_TOTALIZADOR})

    def show_maintenance_button(self):
        self.send_command("mostrar_boton_mantenimiento")

    def inicio_mantenimiento(self):
        self.get_volume()
        self.get_brightness()
        self.get_rfid_antenna_level()
        self.get_build()
        self.get_fan_mode(True)
        self.get_fan_speed()
        self.get_temperature()
        self.get_power_source()
        self.get_pir_status()
        self.get_pir_mode(True)

        self.timeout_bateria = gobject.timeout_add(10000,
                                                   self.get_battery_status)

    def get_volume(self):
        self.volume_level = self._player.get_volume()
        self.send_command("mostrar_volumen", {'volumen': self.volume_level})

    def set_volume(self, data):

        if data == "arriba" and \
                int(self.volume_level) + INCREMENTO_VOLUMEN <= 100:
            self.volume_level += INCREMENTO_VOLUMEN
        elif data == "abajo" and \
                int(self.volume_level) - DECREMENTO_VOLUMEN >= 0:
            self.volume_level -= DECREMENTO_VOLUMEN

        self.volume_level = int(round(self.volume_level, -1))
        if self.volume_level < 0:
            self.volume_level = 0
        elif self.volume_level > 100:
            self.volume_level = 100

        if not int(self._player.get_volume()) == int(self.volume_level):
            self._player.set_volume(self.volume_level)
            sonido = os.path.join(PATH_SONIDOS_VOTO, 'ok.wav')
            self._player.play(sonido)

        # muestra volumen y resetea semaforo
        self.send_command("mostrar_volumen", {'volumen': self.volume_level})

    def get_power_source(self):
        if hasattr(self.sesion, "powermanager"):
            self.power_source = self.sesion.powermanager.get_power_source()
            try:
                self.power_source = self.power_source['byte']
                self.send_command("mostrar_fuente_energia",
                                  {'power_source': self.power_source})
            except:
                pass
        else:
            self.send_command("mostrar_fuente_energia",
                              {'power_source': 0})


    def get_battery_status(self):
        if hasattr(self.sesion, "powermanager"):
            battery_data = self.sesion.powermanager.get_power_status()
            batteries = 0

            if battery_data is not None:
                json_data = json.loads(battery_data)
                if json_data["batt_number"] > 0:
                    json_battery = json_data["batt_data"]
                    batteries = []
                    lowest_current = 0
                    battery_discharging = 0
                    for battery in json_battery:
                        full_charge = battery["full_charge"]
                        remaining = battery["remaining"]
                        battery["battery_level"] = \
                            int(remaining) * 100 / (full_charge)
                        battery["discharging"] = False
                        if battery["corriente"] < lowest_current:
                            lowest_current = battery["corriente"]
                            battery_discharging = battery["slot_number"]
                        elif battery["corriente"] > BATTERY_THRESHOLD:
                            battery["charging"] = True
                        batteries.append(battery)

                    if battery_discharging:
                        for battery in batteries:
                            if battery["slot_number"] == battery_discharging:
                                battery["discharging"] = True
                    batteries.reverse()

            self.send_command("mostrar_bateria", {'baterias': batteries})
        return True

    def get_brightness(self):
        if hasattr(self.sesion, "backlight"):
            brightness = self.sesion.backlight.get_brightness()
            self.brightness_level = int(brightness)
            self.send_command("mostrar_brillo", {'brillo': self.brightness_level})

    def set_brightness(self, data):
        if data == "arriba" and int(self.brightness_level) < 100:
            self.brightness_level = self.brightness_level + INCREMENTO_BRILLO
        elif data == "abajo" and int(self.brightness_level) > 0:
            self.brightness_level = self.brightness_level - DECREMENTO_BRILLO
        self.sesion.backlight.set_brightness(self.brightness_level)
        self.send_command("mostrar_brillo", {'brillo': self.brightness_level})

    def get_build(self):
        if USA_ARMVE:
            build = self.sesion.agent.get_build()
            machine_type = self.sesion.agent.get_machine_type()
            self.send_command("mostrar_build", {'build': build,
                                                'machine': machine_type})
        else:
            self.send_command("mostrar_build", {'build': [1, 0, 0],
                                                'machine': "MALATA"})

    def get_rfid_antenna_level(self):
        if USA_ARMVE:
            level = self.sesion.lector.get_antenna_level()
            try:
                level = json.loads(level)
                level = level['byte']
                if level:
                    antenna_level = POTENCIA_ALTA
                else:
                    antenna_level = POTENCIA_BAJA
                self.send_command("mostrar_potencia_rfid",
                                {'potencia': antenna_level})
            except:
                pass
        else:
            self.send_command("mostrar_potencia_rfid",
                              {'potencia': "N/A"})

    def rfid_check(self, data):
        self.send_command("mostrar_rfid", data)

    def get_fan_speed(self):
        if hasattr(self.sesion, "fancoolers"):
            self.fan_speed = self.sesion.fancoolers.get_fan_speed()
            try:
                self.fan_speed = json.loads(self.fan_speed)
                self.fan_speed = self.fan_speed['byte']
                self.send_command("mostrar_velocidad_ventilador",
                                {'velocidad': self.fan_speed})
            except:
                pass

    def set_fan_speed(self, data):
        self.sesion.fancoolers.set_fan_speed(data)

    def get_fan_mode(self, display=False):
        #True = modo automatico. False = modo manual
        try:
            modo_actual = self.fan_mode
        except:
            if hasattr(self.sesion, "fancoolers"):
                self.fan_mode = self.sesion.fancoolers.get_fan_mode()
            else:
                self.fan_mode = "Automatico"
            modo_actual = self.fan_mode
        if display:
            self.send_command("mostrar_modo_ventilador",
                              {'modo_auto': modo_actual})
        return modo_actual

    def set_fan_auto_mode(self, data):
        #True = modo automatico. False = modo manual
        self.fan_mode = int(data)
        self.sesion.fancoolers.set_fan_auto_mode(self.fan_mode)

    def process_fan_speed(self, data):
        if data == "arriba" and int(self.fan_speed) < 100:
            self.fan_speed = self.fan_speed + INCREMENTO_VOLUMEN
        elif data == "abajo" and int(self.fan_speed) > 0:
            self.fan_speed = self.fan_speed - DECREMENTO_VOLUMEN
        self.set_fan_speed(self.fan_speed)
        self.send_command("mostrar_velocidad_ventilador",
                          {'velocidad': self.fan_speed})

    def fan_check(self):
        current_mode_auto = self.get_fan_mode()
        if current_mode_auto:
            reset_auto_mode = True
            self.set_fan_auto_mode(False)
        else:
            reset_auto_mode = False
            pre_velocity = self.fan_speed
        self.set_fan_speed(0)
        sleep(1)
        self.set_fan_speed(100)
        sleep(8)
        self.set_fan_speed(0)
        sleep(1)
        if reset_auto_mode:
            self.set_fan_auto_mode(True)
        else:
            self.set_fan_speed(pre_velocity)

    def get_temperature(self):
        temperature = get_temp()
        self.send_command("mostrar_temperatura", {'temperatura': temperature})

    def refresh_batteries(self):
        self.get_power_source()
        self.send_command("refresh_batteries")

    def eject_cd(self):
        os.system('eject /dev/sr0 -i off; eject /dev/sr0')

    def get_pir_status(self):
        if hasattr(self.sesion, "pir"):
            pir_status = self.sesion.pir.get_pir_status()
            try:
                pir_status = pir_status['byte']
                self.send_command("mostrar_estado_pir", {'estado': pir_status})
            except:
                pass

    def pir_detection_status(self, detection_status):
        self.detection_status = detection_status
        self.send_command("mostrar_estado_pir",
                          {'estado': detection_status})

    def print_test(self):
        self.send_command("mostrar_test_impresora", {'estado': 'imprimiendo'})
        tipo_tag = "Prueba"
        seleccion_tag = ""
        self.sesion.impresora.imprimir_serializado(
            tipo_tag, seleccion_tag, transpose=False, only_buffer=True)
        self.sesion.impresora.do_print()

    def printer_begin_test(self):
        self.send_command("mostrar_test_impresora", {'estado': 'esperando'})

    def printer_end_test(self):
        self.send_command("ocultar_test_impresora")

    def get_pir_mode(self, display=False):
        if USA_ARMVE:
            try:
                modo_actual = self.pir_mode
            except:
                self.pir_mode = self.sesion.pir.get_pir_mode()
                modo_actual = self.pir_mode
            if display:
                self.send_command("mostrar_modo_pir",
                                {'pir_activado': modo_actual})
            return modo_actual

    def set_pir_mode(self, data):
        self.pir_mode = int(data)
        self.sesion.pir.set_pir_mode(self.pir_mode)

    def get_autofeed_mode(self):
        mode = self.sesion.impresora.get_autofeed_mode()
        self.autofeed_mode = mode.get('af_type')

        if self.autofeed_mode == AUTOFEED_1:
            modo = 1
        elif self.autofeed_mode == AUTOFEED_2:
            modo = 2
        else:
            modo = 0
        self.send_command("mostrar_autofeed",
                          {'autofeed': modo})

    def set_autofeed_mode(self, data):
        modo = int(data)
        if modo == 0:
            self.autofeed_mode = AUTOFEED_SELECT
        elif modo == 1:
            self.autofeed_mode = AUTOFEED_1
        else:
            self.autofeed_mode = AUTOFEED_2
        self.sesion.impresora.set_autofeed_mode(self.autofeed_mode)

    def md5check(self):
        md5 = self.parent.md5_checkfiles(PATH_CD)
        if not md5:
            md5 = "La prueba de integridad ha finalizado correctamente"
        else:
            md5 = "La prueba de integridad ha fallado"
        md5 = json.dumps(md5)
        self.send_command("mostrar_md5", {'md5': md5})

    def reset_device(self, data):
        device_name = data
        if device_name == "rfid":
            device_id = DEV_RFID
        elif device_name == "printer":
            device_id = DEV_PRINTER
        else:
            device_id = DEV_AGENT

        self.sesion.agent.reset(device_id)

    def set_print_quality(self, data):
        quality = int(data)
        self.sesion.impresora.set_quality(quality)

    def get_print_quality(self):
        data = self.sesion.impresora.get_quality()
        self.print_quality = data[0]['byte']

        error = PRINT_STEP / 2
        if self.print_quality < (PRINT_SLOW + error):
            print_quality_adjusted = PRINT_SLOW
        elif self.print_quality < (PRINT_LOW + error):
            print_quality_adjusted = PRINT_LOW
        elif self.print_quality < (PRINT_MID + error):
            print_quality_adjusted = PRINT_MID
        elif self.print_quality < (PRINT_HIGH + error):
            print_quality_adjusted = PRINT_HIGH
        else:
            print_quality_adjusted = PRINT_SHIGH

        self.send_command("mostrar_print_quality",
                          {'print_quality': print_quality_adjusted})

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants()
        self.send_command("set_constants", constants_dict)


def get_constants():
    translations = ("titulo_menu", "totalizacion",
                    "apertura_de_mesa", "sistema_boleta_electronica",
                    "cierre_y_escrutinio", "reiniciar", "version_demo",
                    "votacion_asistida", "expulsar_boleta", "salir",
                    "mesa", "mantenimiento", "auto", "manual", "rfid",
                    "titulo_mantenimiento", "volumen", "brillo",
                    "gestion_energia", "version_firmware", "chequeo_rfid",
                    "volver_al_inicio", "potencia_rfid", "temperatura",
                    "iniciar_chequeo", "modo_ventilador", "no_hay_tag",
                    "descripcion_chequeo_rfid", "cargando", "expulsar_cd",
                    "estado_pir", "pir_prendido", "pir_apagado", "pir",
                    "cancelar", "pir_activado", "pir_desactivado",
                    "chequeo_cd", "prueba_impresora", "aceptar",
                    "reset_devices", "modo_autofeed", "seleccione_boleta",
                    "edicion_2013", "edicion_2015", "autodetectar",
                    "calidad_impresion")
    encabezado = get_config('datos_eleccion')
    niveles_impresion = [PRINT_SLOW, PRINT_LOW, PRINT_MID, PRINT_HIGH,
                         PRINT_SHIGH]

    constants_dict = {
        "juego_de_datos": JUEGO_DE_DATOS,
        "mostrar_cursor": MOSTRAR_CURSOR,
        "intervalo_refresco": INTERVALO_REFRESCO,
        "intervalo_refresco_bateria": INTERVALO_REFRESCO_BATERIA,
        "tiempo_desactivacion_chequeo": TIEMPO_DESACTIVACION_CHEQUEO,
        "niveles_impresion": niveles_impresion,
        "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
        "i18n": [(trans, _(trans)) for trans in translations],
        "effects": EFECTOS_ADMIN,
        "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO,
        "usa_armve": USA_ARMVE,
    }
    return constants_dict
