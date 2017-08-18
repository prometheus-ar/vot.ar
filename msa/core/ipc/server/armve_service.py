#!/usr/bin/env python

"""
Servicio de manejo de interaccion entre pyVoto y el hardware de las maquinas
ARMVE (P2, P3 y P4).
"""
import sys

from logging import ERROR, INFO
from time import sleep

from gi.repository.GObject import MainLoop, timeout_add
from serial import Serial
from serial.serialutil import SerialException

from msa.core.armve.constants import (AUTOFEED_1, AUTOFEED_2, AUTOFEED_DEFAULT,
                                      AUTOFEED_SELECT,
                                      CMD_PRINTER_LOAD_COMP_BUFFER,
                                      CMD_PRINTER_LOAD_COMP_BUFFER_FULL,
                                      CMD_PRINTER_PAPER_REMOVE,
                                      CMD_PRINTER_PRINT, DEV_AGENT, DEV_PIR,
                                      DEV_PRINTER, DEV_PWR, DEV_RFID,
                                      EVT_AGENT_RESET, EVT_PIR_DETECTED,
                                      EVT_PIR_NOT_DETECTED,
                                      EVT_PRINTER_PAPER_INSERTED,
                                      EVT_PRINTER_SENSOR_1,
                                      EVT_PRINTER_SENSOR_2, EVT_PWR_DISCHARGE,
                                      EVT_PWR_EMPTY, EVT_PWR_LVL_CRI,
                                      EVT_PWR_LVL_MAX, EVT_PWR_LVL_MIN,
                                      EVT_PWR_PLUGGED, EVT_PWR_SWITCH_AC,
                                      EVT_PWR_UNPLUGGED, EVT_RFID_NEW_TAG,
                                      MSG_EV_PUB, PRINT_DEFAULT,
                                      CMD_PRINTER_MOVE)

from msa.core.armve.helpers import get_arm_port
from msa.core.armve.protocol import (Agent, Backlight, Device, FanCoolers, PIR,
                                     PowerManager, Printer, RFID)
from msa.core.armve.settings import SERIAL_TIMEOUT, USAR_IMPRESION_V2
from msa.core.data import TemplateImpresion, TemplateMap, Ubicacion
from msa.core.data.candidaturas import Candidatura, Categoria, Lista, Partido
from msa.core.hardware.constants import FAN_THRESHOLD_OFF
from msa.core.hardware.settings import (DEFAULT_BRIGHTNESS,
                                        ITERACIONES_APAGADO, RFID_POWER,
                                        USAR_FAN, USAR_PIR)
from msa.core.hardware.temperature import get_fan_speed, get_temp
from msa.core.i18n import levantar_locales
from msa.core.ipc.server.armve_controller import ARMVEController
from msa.core.logging import get_logger, StreamToLogger
from msa.core.logging.settings import LOG_CAPTURE_STDOUT
from msa.core.ipc.server import IPCServer


levantar_locales()


class ARMVEService():
    def __init__(self):
        self.set_logger()
        self._conn = False
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
        self.impresion_v2 = False
        # Registro eventos a despachar
        self._init_map()
        # Corro el loop de eventos después de inicializar
        # Abro el canal e inicializo
        self.precache_data()
        self.connect_and_load()
        self.ipc = IPCServer(self.procesar_lectura, self)
        self._service_init()

    def set_logger(self):
        logger = get_logger("armve_service")

        if LOG_CAPTURE_STDOUT:
            sys.stdout = StreamToLogger(logger, INFO)
            sys.stderr = StreamToLogger(logger, ERROR)
        self.logger = logger

    def procesar_lectura(self, channel, msg_type, signal, params):
        method = getattr(self.ipc, signal)
        if method is not None:
            if params is not None:
                method(*params)
            else:
                method()

    def connect_and_load(self):
        """Conecta y carga el servicio."""
        try:
            self.buffer = self._init_channel()
            if self.buffer is not None:
                self.logger.debug("Canal Inicializado")
                self.logger.debug("Flusheando buffer")
                self._flush_all(self.buffer)
                self.logger.debug("Creando agent")
                self.agent = Agent(self.buffer)
                if not self.agent:
                    self._conn = False
                    try:
                        self.ipc.connection(self._conn)
                    except AttributeError:
                        pass
                    return self._conn
                sleep(1)
                self.initialize()
        except SerialException:
            pass

    def initialize(self):
        """Inicializa el agente."""
        self.logger.debug("Inicializando agent")
        init_data = self.agent.initialize()
        if init_data is not None and init_data[0] is not None:
            init_data = init_data[0]
            self._process_init_data(init_data)
            self._flush_all(self.buffer)

            self._create_devices()
            self._set_autofeed()
            self._set_print_quality()
            self.register_events()
            self._conn = True
            self.backlight.set_brightness(DEFAULT_BRIGHTNESS)
            self.rfid.set_antenna_level(RFID_POWER)
            try:
                self.ipc.connection(self._conn)
            except AttributeError:
                pass

    def _process_init_data(self, init_data):
        """Procesa la informacion recibida en la inicializacion del ARM."""
        self._free_page_mem = init_data.get('free_page_mem', 0)
        build = init_data.get('build')
        self._build = [init_data.get("machine_type"),
                       build]
        self.impresion_v2 = USAR_IMPRESION_V2 and build >= [2, 1, 0]
        if self.impresion_v2:
            self.logger.warning("Usando funcion nueva de impresion")

    def _set_autofeed(self):
        """Establece el autofeed al inicio."""
        self.logger.debug("estableciendo Autofeed")
        autofeed = self._autofeed_mode
        if autofeed == AUTOFEED_SELECT:
            autofeed = AUTOFEED_1
            status = self.printer.get_status()
            if status is not None:
                if status[0]['sensor_1']:
                    self.printer.paper_eject()
                    sleep(5)
                    status = self.printer.get_status()
                    while status is None:
                        sleep(1)
                        status = self.printer.get_status()

                if not status[0]['sensor_3']:
                    autofeed = AUTOFEED_2

        self._autofeed_mode = autofeed
        self.printer.set_autofeed(autofeed)

    def _set_print_quality(self):
        """Estableceblece la calidad de impresion inicial."""
        self.logger.debug("estableciendo calidad de impresion")
        self.printer.set_quality(PRINT_DEFAULT)

    def _flush_all(self, channel):
        """Flushea el canal completamente."""
        if channel is not None:
            channel.flushInput()
            channel.flushOutput()
            channel.flush()
            while channel.inWaiting() > 0:
                channel.flushInput()

    def _create_devices(self):
        """Instancia todos los dispositivos."""
        self.logger.debug("creando dispositivos")
        self.printer = Printer(self.buffer)
        self.power_manager = PowerManager(self.buffer)
        self.rfid = RFID(self.buffer)
        self.backlight = Backlight(self.buffer)
        self.fancoolers = FanCoolers(self.buffer)
        self.pir = PIR(self.buffer)
        self.device = Device(self.buffer)

    def _service_init(self):
        """Inicializacion real del canal y corrida del service loop."""
        self.logger.info("corriendo el canal, inicializando el service loop")

        def _service_loop():
            """El loop del servicio. Se corre cada 100ms."""
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
            except Exception as error:
                self.logger.error("problema de lectura del canal.")
                self.logger.exception(error)
                self._reset_connection()
            return True

        timeout_add(100, _service_loop)

        if self._usa_fan:
            timeout_add(10000, self.temp_manager)

        if self._usa_pir:
            timeout_add(10000, self.backlight_manager)

    def _process_arm_data(self, response, device_id, command_id,
                          response_type):
        """Procesa la data que llega del ARM.

        Argumentos:
            response -- Respuesta recibida.
            device_id -- dispositivo.
            command_id -- comando.
            response_type -- tipo de respuesta.
        """
        # Existe el evento en el mapa?
        callback_name = self.event_map.get((device_id, command_id))
        try:
            if callback_name is not None and response_type == MSG_EV_PUB:
                # Llamo al método del controller con la respuesta
                # como dict
                controller_func = getattr(self.controller, callback_name, None)
                if controller_func:
                    response = controller_func(response)
                else:
                    response = ()
                # Llamo al método de esta clase con ese nombre si existe
                callback = getattr(self.ipc, callback_name, None)
                if callback is not None:
                    callback(*response)
        except AssertionError:
            pass

    def _init_map(self):
        """Inicializa el mapa de callbacks."""
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
        event_map[(DEV_PRINTER, EVT_PRINTER_SENSOR_1)] = "insertando_papel"
        event_map[(DEV_PRINTER, EVT_PRINTER_SENSOR_2)] = "con_tarjeta"
        event_map[(DEV_PRINTER, CMD_PRINTER_PRINT)] = "fin_impresion"
        event_map[(DEV_PRINTER, CMD_PRINTER_PAPER_REMOVE)] = "boleta_expulsada"
        event_map[(DEV_PRINTER, CMD_PRINTER_MOVE)] = "fin_mover"
        event_map[(DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER)] = \
            "buffer_loaded"
        event_map[(DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER_FULL)] = \
            "buffer_loaded"
        event_map[(DEV_PIR, EVT_PIR_DETECTED)] = "pir_detected"
        event_map[(DEV_PIR, EVT_PIR_NOT_DETECTED)] = "pir_not_detected"
        self.event_map = event_map

    def precache_data(self):
        """Precachea la data para que la primera impresion sea rapida."""
        classes = (Candidatura, Categoria, Partido, Lista, Ubicacion,
                   TemplateImpresion, TemplateMap)
        for class_ in classes:
            class_.all()

    def _init_channel(self):
        """Inicializa el canal."""
        channel = None
        serial_port = get_arm_port()
        if serial_port is not None:
            channel = Serial(serial_port, timeout=SERIAL_TIMEOUT)
            if not channel.isOpen():
                channel.open()
        return channel

    def _eventos_rfid(self):
        """Registra los eventos de rfid."""
        if hasattr(self, "rfid"):
            self.logger.info("registrando evento de cambio de tag")
            self.rfid.register_new_tag(100)

    def _eventos_impresora(self):
        """Registra los eventos de impresora."""
        self.logger.info("registrando evento de papel insertado")
        self.printer.register_paper_inserted()
        self.logger.info("registrando evento de sensor 1")
        self.printer.register_sensor_1()
        self.logger.info("registrando evento de sensor 2")
        self.printer.register_sensor_2()

    def _eventos_power(self):
        """Registra los eventos de power."""
        self.logger.info("registrando evento de conexion de AC")
        self.power_manager.register_switch_ac()
        self.logger.info("registrando evento de descarga de baterias")
        self.power_manager.register_battery_discharge()
        self.logger.info("registrando evento de conexion de baterias")
        self.power_manager.register_battery_unplugged()
        self.logger.info("registrando evento de desconexion de baterias")
        self.power_manager.register_battery_plugged()

    def _eventos_pir(self):
        """Registra los eventos de PIR."""
        self.logger.info("registrando evento de presencia de pir")
        self.pir.register_detected()
        self.logger.info("registrando evento de no presencia de pir")
        self.pir.register_not_detected()

    def register_events(self):
        """Registra eventos."""
        self._eventos_rfid()
        self._eventos_impresora()
        self._eventos_power()
        if USAR_PIR:
            self._eventos_pir()

    def temp_manager(self):
        """Manager de temperatura. Ee ejecuta cada N tiempo."""
        if self._usa_fan:
            temperature = get_temp()
            if self._conn and (temperature > self._last_temp or
                               temperature <= FAN_THRESHOLD_OFF) \
                    and self._fan_auto_mode:
                new_speed = get_fan_speed(temperature)
                if new_speed != self._last_speed:
                    self.logger.info("Cambiando velocidad del fan a %s" % new_speed)
                    self.fancoolers.set_speed(new_speed)
                    self._last_speed = new_speed
                self._last_temp = temperature
            return True
        else:
            if hasattr(self, "fancoolers"):
                try:
                    self.fancoolers.set_speed(0)
                except SerialException:
                    self._reset_connection()
            return False

    def _reset_connection(self):
        """Resetea la conexion."""
        self.buffer = None
        self._conn = False
        self.ipc.connection(self._conn)

    def reset_off_counter(self):
        """Reinicia el contador de apagado de monitor."""
        self.logger.debug("Recibido evento de PIR no detectado")
        self._off_counter = 0

    def backlight_manager(self):
        """Maneja el backlight."""
        if self._off_counter == ITERACIONES_APAGADO:
            self.apagar_monitor()
        if not self._ac_power_source:
            self._off_counter += 1
        return True

    def encender_monitor(self):
        """Enciende el backlight."""
        if self._usa_pir and not self._screen_on:
            self._screen_on = True
            self._off_counter = 0
            self.backlight.set_status(True)

    def apagar_monitor(self):
        """Apaga el backlight."""
        if self._usa_pir and not self.printer.has_paper() and \
           not self._ac_power_source and self._screen_on:
            self._screen_on = False
            self.backlight.set_status(False)

    def error_impresion(self):
        self.logger.warning("Reiniciando IMPRESORA preventivamente")
        self.agent.reset(DEV_PRINTER)
        # despachar el evento en diferido para dar tiempo al hw a reiniciar:
        timeout_add(2000, self.ipc.error_impresion)


def main():
    # inicia el main loop
    loop = MainLoop()
    try:
        # instanciamos el servicio
        ARMVEService()
        # corremos el servicio hasta el fin de los tiempos, o hasta recibir un
        # KeyboardInterrupt
        loop.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

