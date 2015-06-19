#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus
import gobject
import sys

from base64 import b64decode
from json import dumps, loads
from logging import INFO, ERROR
from serial import Serial
from serial.serialutil import SerialException
from time import sleep

from msa import get_logger, StreamToLogger
from msa.core.armve.protocol import Device, PowerManager, Printer, RFID, \
    Backlight, FanCoolers, PIR, Agent
from msa.core.armve.constants import DEV_PWR, EVT_PWR_DISCHARGE, \
    EVT_PWR_LVL_MIN, EVT_PWR_LVL_CRI, EVT_PWR_LVL_MAX, \
    EVT_PWR_SWITCH_AC, EVT_PWR_UNPLUGGED, EVT_PWR_EMPTY, DEV_RFID, \
    EVT_RFID_NEW_TAG, DEV_PRINTER, EVT_PRINTER_PAPER_INSERTED, \
    CMD_PRINTER_PRINT, EVT_PRINTER_PAPER_OUT_1, EVT_PRINTER_PAPER_OUT_2, \
    CMD_PRINTER_PAPER_REMOVE, DEV_PIR, EVT_PIR_DETECTED, \
    EVT_PIR_NOT_DETECTED, CMD_PRINTER_LOAD_COMP_BUFFER, EVT_PWR_PLUGGED, \
    AUTOFEED_DEFAULT, DEV_AGENT, EVT_AGENT_RESET, AUTOFEED_1, AUTOFEED_2, \
    MSG_EV_PUB, AUTOFEED_SELECT, PRINT_DEFAULT
from msa.core.armve.helpers import get_arm_port
from msa.core.armve.settings import SERIAL_TIMEOUT
from msa.core.constants import FAN_THRESHOLD_OFF
from msa.core.data import TemplateImpresion, TemplateMap, Ubicacion
from msa.core.data.candidaturas import Candidato, Categoria, Partido, Lista
from msa.core.ipc.server.armve_controller import ARMVEController
from msa.core.ipc.server.dbus_service import MSADbusService
from msa.core.temperature import get_fan_speed, get_temp
from msa.core.settings import DBUS_ARMVE_PATH, DBUS_BUSNAME_ARMVE, USAR_PIR, \
    ITERACIONES_APAGADO, DEFAULT_BRIGHTNESS, RFID_POWER, USAR_FAN
from msa.helpers import levantar_locales
from msa.settings import LOG_CAPTURE_STDOUT


levantar_locales()
logger = get_logger("armve_service")

if LOG_CAPTURE_STDOUT:
    sys.stdout = StreamToLogger(logger, INFO)
    sys.stderr = StreamToLogger(logger, ERROR)


class ARMVEDBus(MSADbusService):
    def __init__(self):
        """Constructor"""
        self.object_path = DBUS_ARMVE_PATH
        self.bus_name = DBUS_BUSNAME_ARMVE
        self._conn = False
        self.buffer = None
        self.printing = False
        self._fan_auto_mode = True
        self.controller = ARMVEController(self)
        self._last_temp = 0
        self._off_counter = 0
        self._last_speed = -1
        self._ac_power_source = True
        self._usa_pir = USAR_PIR
        self._usa_fan = USAR_FAN
        self._autofeed_mode = AUTOFEED_DEFAULT
        self._print_quality = PRINT_DEFAULT
        self._screen_on = None
        self._build = None
        self.device = None
        # Registro eventos a despachar
        self._init_map()
        # Corro el loop de eventos después de inicializar
        MSADbusService.__init__(self, True)
        # Abro el canal e inicializo
        self.precache_data()
        self.connect_and_load()

    def connect_and_load(self):
        self.buffer = self._init_channel()
        if self.buffer is not None:
            logger.debug("Canal Inicializado")
            logger.debug("Flusheando buffer")
            self._flush_all(self.buffer)
            logger.debug("Creando agent")
            self.agent = Agent(self.buffer)
            if not self.agent:
                self._conn = False
                return self.connection(self._conn)
            sleep(1)
            self.initialize()

    def initialize(self):
        logger.debug("Inicializando agent")
        init_data = self.agent.initialize()
        if init_data is not None:
            init_data = init_data[0]
            self._free_page_mem = init_data.get('free_page_mem', 0)
            self._build = [init_data.get("machine_type"),
                           init_data.get('build')]
            self._flush_all(self.buffer)

            self._create_devices()
            self._set_autofeed()
            self._set_print_quality()
            self.register_events()
            self._conn = True
            self.backlight.set_brightness(DEFAULT_BRIGHTNESS)
            self.rfid.set_antenna_level(RFID_POWER)
            self.connection(self._conn)

    def _set_autofeed(self):
        logger.debug("estableciendo Autofeed")
        autofeed = self._autofeed_mode
        if autofeed == AUTOFEED_SELECT:
            autofeed = AUTOFEED_1
            status = self.printer.get_status()
            if status is not None:
                if status[0]['paper_out_1']:
                    self.printer.paper_eject()
                    sleep(5)
                    status = self.printer.get_status()
                    while status is None:
                        sleep(1)
                        status = self.printer.get_status()

                if not status[0]['lever_open']:
                    autofeed = AUTOFEED_2

        self._autofeed_mode = autofeed
        self.printer.set_autofeed(autofeed)

    def _set_print_quality(self):
        logger.debug("estableciendo calidad de impresion")
        self.printer.set_quality(PRINT_DEFAULT)

    def _flush_all(self, channel):
        if channel is not None:
            channel.flushInput()
            channel.flushOutput()
            channel.flush()
            while channel.inWaiting() > 0:
                channel.flushInput()

    def _create_devices(self):
        logger.debug("creando dispositivos")
        self.printer = Printer(self.buffer)
        self.power_manager = PowerManager(self.buffer)
        self.rfid = RFID(self.buffer)
        self.backlight = Backlight(self.buffer)
        self.fancoolers = FanCoolers(self.buffer)
        self.pir = PIR(self.buffer)
        self.device = Device(self.buffer)

    def precache_data(self):
        classes = (Candidato, Categoria, Partido, Lista, Ubicacion,
                   TemplateImpresion, TemplateMap)
        for class_ in classes:
            class_.all()

    def encender_monitor(self):
        #logger.debug("Recibido evento de PIR detectado")
        if self._usa_pir and not self._screen_on:
            self._screen_on = True
            self._off_counter = 0
            self.backlight.set_status(True)

    def apagar_monitor(self):
        if self._usa_pir and not self.printer.has_paper() and \
           not self._ac_power_source and self._screen_on:
            self._screen_on = False
            self.backlight.set_status(False)

    def reset_device(self, number):
        logger.info("Reinicializando dispositivo %s", number)
        self.power_manager.set_leds(7, 1, 200, 1000)
        func = None
        if number == DEV_AGENT:
            func = self.initialize
        elif number == DEV_PWR:
            func = self._eventos_power
        elif number == DEV_PRINTER:

            def _inner():
                self._eventos_impresora()
                self._set_autofeed()
                self._set_print_quality()

            func = _inner
        elif number == DEV_RFID:
            func = self._eventos_rfid

        if func is not None:
            gobject.timeout_add(100, func)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def reset_rfid(self):
        self.agent_reset(DEV_RFID)

    def _eventos_rfid(self):
        logger.info("registrando evento de cambio de tag")
        self.rfid.register_new_tag(100)

    def _eventos_impresora(self):
        logger.info("registrando evento de papel insertado")
        self.printer.register_paper_inserted()
        logger.info("registrando evento de paper out 1")
        self.printer.register_paper_out_1()
        logger.info("registrando evento de paper out 2")
        self.printer.register_paper_out_2()

    def _eventos_power(self):
        logger.info("registrando evento de conexion de AC")
        self.power_manager.register_switch_ac()
        logger.info("registrando evento de descarga de baterias")
        self.power_manager.register_battery_discharge()
        logger.info("registrando evento de conexion de baterias")
        self.power_manager.register_battery_unplugged()
        logger.info("registrando evento de desconexion de baterias")
        self.power_manager.register_battery_plugged()

    def _eventos_pir(self):
        logger.info("registrando evento de presencia de pir")
        self.pir.register_detected()
        logger.info("registrando evento de no presencia de pir")
        self.pir.register_not_detected()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def register_events(self):
        self._eventos_rfid()
        self._eventos_impresora()
        self._eventos_power()
        self._eventos_pir()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def unregister_events(self):
        self.agent.unregister_events()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def list_events(self):
        events = self.agent.list_events()[0]
        filt_events = [self._prepare_response(event, False) for event in
                       events['event']]
        events = self._prepare_response(filt_events)
        return events

    def _init_map(self):
        event_map = {}
        event_map[(DEV_AGENT, EVT_AGENT_RESET)] = "reset_device"
        event_map[(DEV_PWR, EVT_PWR_DISCHARGE)] = "battery_discharging"
        event_map[(DEV_PWR, EVT_PWR_LVL_MIN)] = "battery_level_min"
        event_map[(DEV_PWR, EVT_PWR_LVL_CRI)] = "battery_level_critical"
        event_map[(DEV_PWR, EVT_PWR_LVL_MAX)] = "battery_level_max"
        event_map[(DEV_PWR, EVT_PWR_SWITCH_AC)] = "switch_ac"
        event_map[(DEV_PWR, EVT_PWR_UNPLUGGED)] = "battery_unplugged"
        event_map[(DEV_PWR, EVT_PWR_PLUGGED)] = "battery_plugged"
        event_map[(DEV_PWR, EVT_PWR_EMPTY)] = "battery_empty"
        event_map[(DEV_RFID, EVT_RFID_NEW_TAG)] = "tag_leido"
        event_map[(DEV_PRINTER, EVT_PRINTER_PAPER_INSERTED)] = "autofeed_end"
        event_map[(DEV_PRINTER, EVT_PRINTER_PAPER_OUT_1)] = "insertando_papel"
        event_map[(DEV_PRINTER, EVT_PRINTER_PAPER_OUT_2)] = "con_tarjeta"
        event_map[(DEV_PRINTER, CMD_PRINTER_PRINT)] = "fin_impresion"
        event_map[(DEV_PRINTER, CMD_PRINTER_PAPER_REMOVE)] = "boleta_expulsada"
        event_map[(DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER)] = \
            "buffer_loaded"
        event_map[(DEV_PIR, EVT_PIR_DETECTED)] = "pir_detected"
        event_map[(DEV_PIR, EVT_PIR_NOT_DETECTED)] = "pir_not_detected"
        self.event_map = event_map

    def _init_channel(self):
        channel = None
        serial_port = get_arm_port()
        if serial_port is not None:
            channel = Serial(serial_port, timeout=SERIAL_TIMEOUT)
            if not channel.isOpen():
                channel.open()
        return channel

    def temp_manager(self):
        if self._usa_fan:
            temperature = get_temp()
            if self._conn and (temperature > self._last_temp or \
                temperature <= FAN_THRESHOLD_OFF) and self._fan_auto_mode:
                    new_speed = get_fan_speed(temperature)
                    if new_speed != self._last_speed:
                        logger.info("Cambiando velocidad del fan a %s" % new_speed)
                        self.fancoolers.set_speed(new_speed)
                        self._last_speed = new_speed
                    self._last_temp = temperature
            return True
        else:
            if hasattr(self, "fancoolers"):
                self.fancoolers.set_speed(0)
            return False

    def reset_off_counter(self):
        logger.debug("Recibido evento de PIR no detectado")
        self._off_counter = 0

    def backlight_manager(self):
        if self._off_counter == ITERACIONES_APAGADO:
            self.apagar_monitor()
        if not self._ac_power_source:
            self._off_counter += 1
        return True

    def _real_init(self):
        logger.info("corriendo real init")
        def _service_loop():
            try:
                if self.buffer is not None and self.device is not None:
                    arm_data = self.device.read(True)
                    if arm_data is not None:
                        response, device_id, command_id, response_type = \
                            arm_data
                        self._process_arm_data(response, device_id, command_id,
                                               response_type)
                else:
                    self.connect_and_load()
            except SerialException:
                logger.error("problema de lectura del canal, desconectando")
                self.buffer = None
                self._conn = False
                self.connection(self._conn)
            return True

        gobject.timeout_add(100, _service_loop)

        gobject.timeout_add(10000, self.temp_manager)

        if self._usa_pir:
            gobject.timeout_add(10000, self.backlight_manager)

    def _process_arm_data(self, response, device_id, command_id, response_type):
        # Existe el evento en el mapa?
        callback = self.event_map.get((device_id, command_id))
        if callback is not None and response_type == MSG_EV_PUB:
            # Llamo al método del controller con la respuesta
            # como dict
            controller_func = getattr(self.controller, callback, None)
            response = self._prepare_response(response, False)
            if controller_func:
                response = controller_func(response)
            else:
                response = ()
            # Llamo al método de esta clase con ese nombre si
            # existe
            callback = getattr(self, callback, None)
            if callback:
                callback(*response)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def quit(self):
        """ Cierra el servicio DBUS, útil para casos de reinicio"""
        if self._loop.is_running():
            self._loop.quit()

    def _info(self, func):
        logger.info("llamando a %s" % func)

    def _prepare_response(self, response, use_json=True):
        if hasattr(response, "__dict__"):
            respose_dict = response.__dict__
        else:
            respose_dict = response
        if use_json:
            respose_dict = dumps(respose_dict)
        return respose_dict

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_power_source(self):
        self._info("get_power_source")
        response = self.power_manager.get_power_source()
        if response is not None:
            response = response[0]
            response = self._prepare_response(response, False)
            self.controller.get_power_source_cb(response)
            return response

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_connected_batteries(self):
        self._info("get_connected_batteries")
        return self.power_manager.get_connected_batteries()

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_discharging(self):
        self.controller.power_source_change(False)
        self._info("battery_discharging")
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_level_min(self, response):
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_level_critical(self, response):
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_level_max(self, response):
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def switch_ac(self):
        self.controller.power_source_change(True)
        self._info("switch_ac")
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_unplugged(self):
        self._info("battery_unplugged")
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def battery_plugged(self):
        self._info("battery_plugged")
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def pir_detected(self):
        self._info("pir_detected")
        self.controller.pir_detected_cb(True)
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def pir_not_detected(self):
        self._info("pir_not_detected")
        self.controller.pir_not_detected_cb(True)
        return True

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def tag_leido(self, tipo_tag, tag):
        self._info("tag_leido")
        return tipo_tag, tag

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def fin_impresion(self):
        self._info("fin_impresion")
        self.expulsar_boleta()
        return None

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def boleta_expulsada(self):
        self._info("boleta_expulsada")
        return None

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def con_tarjeta(self, response):
        self._info("con tarjeta")
        return response

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def imprimiendo(self):
        self._info("imprimiendo")
        return self.printing

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def _get_type(self):
        self._info("get_type")
        return self.printer.get_type()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def _get_vendor(self):
        self._info("get_vendor")
        return self.printer.get_vendor()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def linefeed(self, n):
        self._info("linefeed")
        return self.printer.move(n * 8)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def backfeed(self, n):
        self._info("backfeed")
        return self.printer.move(-n * 8)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def expulsar_boleta(self):
        self._info("expulsar_boleta")
        self.power_manager.set_leds(1, 1, 200, 400)
        self.printer.register_paper_eject()
        self.printer.paper_eject()
        return True

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def tomar_tarjeta(self, loops):
        self._info("tomar_tarjeta")
        # en principio en la maquina con ARMVE no tiene sentido este comando
        return True

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def posicionar_al_inicio(self):
        self._info("posicionar_al_inicio")
        # en principio en la maquina con ARMVE no tiene sentido este comando
        return True

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def limpiar_cola(self):
        self._info("limpiar_cola")
        self.printer.clear_buffer()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def imprimir_image(self, filepath, mode, size, dpi, transpose, compress,
                       only_buffer):
        # TODO: Eliminar este método
        self._info("imprimir_image")
        self.controller.print_image(filepath, mode, size, transpose,
                                    only_buffer)
        return True

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer,
                             extra_data):
        self._info("imprimir_serializado")
        self.controller.imprimir_serializado(tipo_tag, tag, transpose,
                                             only_buffer, extra_data)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def registrar(self, tag):
        self._info("registrar")
        tag = b64decode(tag)
        return self.controller.registrar(tag)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def do_print(self):
        self._info("do_print")
        return self.controller.do_print()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def tarjeta_ingresada(self):
        self._info("tarjeta_ingresada")
        if hasattr(self, "printer"):
            ingresada = self.printer.has_paper()
        else:
            ingresada = False
        return ingresada

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def tarjeta_sin_retirar(self):
        self._info("tarjeta_sin_retirar")
        estado = self.printer.has_paper()
        return estado

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def full_paper_status(self):
        printer_status = self.printer.get_status()
        if printer_status is not None:
            status = loads(self._prepare_response(printer_status[0]))
        else:
            status = None
        return status

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_quality(self):
        return self.printer.get_quality()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_quality(self, level):
        self._info("set_quality")
        return self.printer.set_quality(level)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def ping(self):
        return 'pong'

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def estado(self, out_signature="b"):
        self._info("estado")
        return self._conn

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def read(self, out_signature="s"):
        self._info("read")
        tag = self.controller.get_tag()
        tag = tag[1]
        return dumps(tag)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def read_metadata(self, out_signature="s"):
        return dumps(self.controller.get_tag_metadata())

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def is_read_only(self, serial_number):
        self._info("is_read_only")
        return self.rfid.is_tag_read_only(serial_number)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def write(self, serial, tipo, data, marcar_ro=False):
        self._info("write")
        return self.controller.write(serial, tipo, b64decode(data), marcar_ro)

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def connection(self, state):
        self._info("connection: " + str(state))
        return state

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def insertando_papel(self, state):
        self._info("insertando_papel")
        return state

    @dbus.service.signal(DBUS_BUSNAME_ARMVE)
    def autofeed_end(self, state):
        self._info("autofeed_end")
        return state

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def guardar_tag(self, tipo_tag, data, marcar_ro):
        self._info("guardar_tag")
        return self.controller.guardar_tag(tipo_tag, b64decode(data),
                                           marcar_ro)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_tipo(self, serial, tipo):
        return self.controller.set_tipo(serial, b64decode(tipo))

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_map(self):
        return self.controller.get_map()

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_brightness(self):
        response = self.backlight.get_brightness()
        response = response[0]
        return self._prepare_response(response)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_brightness(self, value):
        return self.backlight.set_brightness(value)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_power_status(self):
        response = self.power_manager.get_status()
        if response is not None:
            response = response[0]
            response = self._prepare_response(response, False)

            batteries = []
            for element in response["batt_data"]:
                batt = self._prepare_response(element, False)
                batteries.append(batt)
            response["batt_data"] = batteries

            return dumps(response)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_build(self):
        return self._build[1]

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_machine_type(self):
        return self._build[0]

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_antenna_level(self):
        response = self.rfid.get_antenna_level()
        response = response[0]
        return self._prepare_response(response)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_fan_speed(self):
        response = self.fancoolers.get_speed()
        if response is not None:
            response = response[0]
            return self._prepare_response(response)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_fan_speed(self, value):
        return self.fancoolers.set_speed(value)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_fan_mode(self):
        return self._fan_auto_mode

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_fan_auto_mode(self, value):
        return self.controller.set_fan_auto_mode(value)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def agent_reset(self, device):
        return self.agent.reset(device)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_pir_status(self):
        response = self.pir.status()
        response = self._prepare_response(response[0])
        return response

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_pir_mode(self):
        return self._usa_pir

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_pir_mode(self, mode):
        self._info("set_pir_mode")
        return self.controller.set_pir_mode(mode)

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def get_autofeed_mode(self):
        mode = self.printer.get_autofeed()
        if mode is not None:
            mode = mode[0]
        return mode

    @dbus.service.method(DBUS_BUSNAME_ARMVE)
    def set_autofeed_mode(self, mode):
        self._info("set_autofeed_mode")
        return self.controller.set_autofeed_mode(mode)


if __name__ == '__main__':
    ARMVEDBus()
