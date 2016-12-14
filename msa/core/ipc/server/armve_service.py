#!/usr/bin/env python

"""
Servicio de manejo de interaccion entre pyVoto y el hardware de las maquinas
ARMVE (P2, P3 y P4).
"""
import sys

from codecs import decode
from base64 import b64decode
from dbus.service import method, signal
from gi.repository.GObject import timeout_add
from json import dumps, loads
from logging import INFO, ERROR
from serial import Serial
from serial.serialutil import SerialException
from time import sleep

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
                                      MSG_EV_PUB, PRINT_DEFAULT)

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
from msa.core.ipc.server.dbus_service import MSADbusService
from msa.core.ipc.settings import DBUS_ARMVE_PATH, DBUS_BUSNAME_ARMVE
from msa.core.logging import get_logger, StreamToLogger
from msa.core.logging.settings import LOG_CAPTURE_STDOUT


levantar_locales()
logger = get_logger("armve_service")

if LOG_CAPTURE_STDOUT:
    sys.stdout = StreamToLogger(logger, INFO)
    sys.stderr = StreamToLogger(logger, ERROR)


class ARMVEDBus(MSADbusService):

    """Server de DBus para ARMVE."""

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
        self.impresion_v2 = False
        # Registro eventos a despachar
        self._init_map()
        # Corro el loop de eventos después de inicializar
        MSADbusService.__init__(self, True)
        # Abro el canal e inicializo
        self.precache_data()
        self.connect_and_load()

    def connect_and_load(self):
        """Conecta y carga el servicio."""
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
        """Inicializa el agente."""
        logger.debug("Inicializando agent")
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
            self.connection(self._conn)

    def _process_init_data(self, init_data):
        """Procesa la informacion recibida en la inicializacion del ARM."""
        self._free_page_mem = init_data.get('free_page_mem', 0)
        build = init_data.get('build')
        self._build = [init_data.get("machine_type"),
                       build]
        self.impresion_v2 = USAR_IMPRESION_V2 and build >= [2, 1, 0]
        if self.impresion_v2:
            logger.warning("Usando funcion nueva de impresion")

    def _set_autofeed(self):
        """Establece el autofeed al inicio."""
        logger.debug("estableciendo Autofeed")
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
        logger.debug("estableciendo calidad de impresion")
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
        logger.debug("creando dispositivos")
        self.printer = Printer(self.buffer)
        self.power_manager = PowerManager(self.buffer)
        self.rfid = RFID(self.buffer)
        self.backlight = Backlight(self.buffer)
        self.fancoolers = FanCoolers(self.buffer)
        self.pir = PIR(self.buffer)
        self.device = Device(self.buffer)

    def precache_data(self):
        """Precachea la data para que la primera impresion sea rapida."""
        classes = (Candidatura, Categoria, Partido, Lista, Ubicacion,
                   TemplateImpresion, TemplateMap)
        for class_ in classes:
            class_.all()

    def encender_monitor(self):
        """Enciende el backlight."""
        #logger.debug("Recibido evento de PIR detectado")
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

    def reset_device(self, number):
        """Resetea el dispositivo.

        Argumentos:
            number -- el numero de dispositivo a reiniciar.
        """
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
            timeout_add(100, func)

    @method(DBUS_BUSNAME_ARMVE)
    def reset_rfid(self):
        """Resetea el rfid."""
        self.agent_reset(DEV_RFID)

    def _eventos_rfid(self):
        """Registra los eventos de rfid."""
        logger.info("registrando evento de cambio de tag")
        self.rfid.register_new_tag(100)

    def _eventos_impresora(self):
        """Registra los eventos de impresora."""
        logger.info("registrando evento de papel insertado")
        self.printer.register_paper_inserted()
        logger.info("registrando evento de sensor 1")
        self.printer.register_sensor_1()
        logger.info("registrando evento de sensor 2")
        self.printer.register_sensor_2()

    def _eventos_power(self):
        """Registra los eventos de power."""
        logger.info("registrando evento de conexion de AC")
        self.power_manager.register_switch_ac()
        logger.info("registrando evento de descarga de baterias")
        self.power_manager.register_battery_discharge()
        logger.info("registrando evento de conexion de baterias")
        self.power_manager.register_battery_unplugged()
        logger.info("registrando evento de desconexion de baterias")
        self.power_manager.register_battery_plugged()

    def _eventos_pir(self):
        """Registra los eventos de PIR."""
        logger.info("registrando evento de presencia de pir")
        self.pir.register_detected()
        logger.info("registrando evento de no presencia de pir")
        self.pir.register_not_detected()

    @method(DBUS_BUSNAME_ARMVE)
    def register_events(self):
        """Registra eventos."""
        self._eventos_rfid()
        self._eventos_impresora()
        self._eventos_power()
        if USAR_PIR:
            self._eventos_pir()

    @method(DBUS_BUSNAME_ARMVE)
    def unregister_events(self):
        """Desregistra todos los eventos via agent."""
        self.agent.unregister_events()

    @method(DBUS_BUSNAME_ARMVE)
    def list_events(self):
        """Lista todos los eventos registrados."""
        events = self.agent.list_events()[0]
        filt_events = [self._prepare_response(event, False) for event in
                       events['event']]
        events = self._prepare_response(filt_events)
        return events

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
        event_map[(DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER)] = \
            "buffer_loaded"
        event_map[(DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER_FULL)] = \
            "buffer_loaded"
        event_map[(DEV_PIR, EVT_PIR_DETECTED)] = "pir_detected"
        event_map[(DEV_PIR, EVT_PIR_NOT_DETECTED)] = "pir_not_detected"
        self.event_map = event_map

    def _init_channel(self):
        """Inicializa el canal."""
        channel = None
        serial_port = get_arm_port()
        if serial_port is not None:
            channel = Serial(serial_port, timeout=SERIAL_TIMEOUT)
            if not channel.isOpen():
                channel.open()
        return channel

    def temp_manager(self):
        """Manager de temperatura. Ee ejecuta cada N tiempo."""
        if self._usa_fan:
            temperature = get_temp()
            if self._conn and (temperature > self._last_temp or
                               temperature <= FAN_THRESHOLD_OFF) \
                    and self._fan_auto_mode:
                new_speed = get_fan_speed(temperature)
                if new_speed != self._last_speed:
                    logger.info("Cambiando velocidad del fan a %s" % new_speed)
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
        self.connection(self._conn)

    def reset_off_counter(self):
        """Reinicia el contador de apagado de monitor."""
        logger.debug("Recibido evento de PIR no detectado")
        self._off_counter = 0

    def backlight_manager(self):
        """Maneja el backlight."""
        if self._off_counter == ITERACIONES_APAGADO:
            self.apagar_monitor()
        if not self._ac_power_source:
            self._off_counter += 1
        return True

    def _service_init(self):
        """Inicializacion real del canal y corrida del service loop."""
        logger.info("corriendo el canal, inicializando el service loop")

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
            except (SerialException, TypeError):
                logger.error("problema de lectura del canal, desconectando")
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

    @method(DBUS_BUSNAME_ARMVE)
    def quit(self):
        """ Cierra el servicio DBUS, útil para casos de reinicio"""
        if self._loop.is_running():
            self._loop.quit()

    def _info(self, func):
        """Decorador de logging de llamado a funciones."""
        logger.info("llamando a %s" % func)

    def _prepare_response(self, response, use_json=True):
        """Prepara la respuesta para adaptarse al formato de DBus."""
        if hasattr(response, "__dict__"):
            respose_dict = response.__dict__
        else:
            respose_dict = response
        if use_json:
            respose_dict = dumps(respose_dict)
        return respose_dict

    @method(DBUS_BUSNAME_ARMVE)
    def get_power_source(self):
        """Devuelve cual es la fuente de alimentacion."""
        self._info("get_power_source")
        response = self.power_manager.get_power_source()
        if response is not None:
            response = response[0]
            response = self._prepare_response(response, False)
            self.controller.get_power_source_cb(response)
            return response

    @method(DBUS_BUSNAME_ARMVE)
    def get_connected_batteries(self):
        """Indica las baterias conectadas."""
        self._info("get_connected_batteries")
        return self.power_manager.get_connected_batteries()

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_discharging(self):
        """Evento de descarga de baterias."""
        self.controller.power_source_change(False)
        self._info("battery_discharging")
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_level_min(self, response):
        """Evento de bateria al minimo."""
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_level_critical(self, response):
        """Evento de bateria critica."""
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_level_max(self, response):
        """Evento de bateria al maximo."""
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def switch_ac(self):
        """Evento de switcheo a AC."""
        self.controller.power_source_change(True)
        self._info("switch_ac")
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_unplugged(self):
        """Evento de bateria desenchufada."""
        self._info("battery_unplugged")
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def battery_plugged(self):
        """Evento de bateria enchufada."""
        self._info("battery_plugged")
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def pir_detected(self):
        """Evento de PIR detectado."""
        self._info("pir_detected")
        self.controller.pir_detected_cb(True)
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def pir_not_detected(self):
        """Evento de PIR no detectado."""
        self._info("pir_not_detected")
        self.controller.pir_not_detected_cb(True)
        return True

    @signal(DBUS_BUSNAME_ARMVE)
    def tag_leido(self, tipo_tag, tag):
        """Evento de tag leido."""
        self._info("tag_leido")
        return tipo_tag, tag

    @signal(DBUS_BUSNAME_ARMVE)
    def fin_impresion(self):
        """Evento de fin de impresion."""
        self._info("fin_impresion")
        self.expulsar_boleta()
        return None

    @signal(DBUS_BUSNAME_ARMVE)
    def boleta_expulsada(self):
        """Evento de Boleta expulsada."""
        self._info("boleta_expulsada")
        return None

    @signal(DBUS_BUSNAME_ARMVE)
    def con_tarjeta(self, response):
        """Eventonto de tengo papel."""
        self._info("con tarjeta")
        return response

    @method(DBUS_BUSNAME_ARMVE)
    def imprimiendo(self):
        """Me dice si estoy imprimiendo o no."""
        self._info("imprimiendo")
        return self.printing

    @method(DBUS_BUSNAME_ARMVE)
    def _get_type(self):
        """Devuelve el tipo de impresora."""
        self._info("get_type")
        return self.printer.get_type()

    @method(DBUS_BUSNAME_ARMVE)
    def _get_vendor(self):
        """Devuelve el vendor de impresora."""
        self._info("get_vendor")
        return self.printer.get_vendor()

    @method(DBUS_BUSNAME_ARMVE)
    def linefeed(self, n):
        """Mueve n pasos el papel."""
        self._info("linefeed")
        return self.printer.move(n * 8)

    @method(DBUS_BUSNAME_ARMVE)
    def backfeed(self, n):
        """Mueve n pasos asia atras el papel."""
        self._info("backfeed")
        return self.printer.move(-n * 8)

    @method(DBUS_BUSNAME_ARMVE)
    def expulsar_boleta(self):
        """Expulsa la boleta."""
        self._info("expulsar_boleta")
        if hasattr(self, "power_manager"):
            self.power_manager.set_leds(1, 1, 200, 400)
            self.printer.register_paper_eject()
            self.printer.paper_eject()
        return True

    @method(DBUS_BUSNAME_ARMVE)
    def limpiar_cola(self):
        """Limpia el buffer de impresion."""
        self._info("limpiar_cola")
        self.printer.clear_buffer()

    @method(DBUS_BUSNAME_ARMVE)
    def imprimir_image(self, filepath, mode, size, dpi, transpose, compress,
                       only_buffer):
        """Imprime una imagen pasandole el path y las settings.

        Argumentos:
            filepath -- el path en disco de la imagen.
            mode -- El modo de la imagen.
            size -- el tamaño de la misma.
            dpi -- con cuantos DPI queremos imprimir.
            transpose -- Transpone la imagen.
            compress -- Comprime la imagen al comprimirla.
            only_buffer -- No la imprime, solo la guarda en buffer.
        """

        self._info("imprimir_image")
        self.controller.print_image(filepath, mode, size, transpose,
                                    only_buffer)
        return True

    @method(DBUS_BUSNAME_ARMVE)
    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer,
                             extra_data):
        """Imprime los documentos desde una serializacion del tag.

        Argumentos:
            tipo_tag -- el tipo de documento que queremos guardar.
            tag -- el contenido serializado del tag a guardar.
            transpose -- indica si queremos transponer la imagen.
            only_buffer -- no imprime la imagen, solo la guarda.
            extra_data -- datos que no se guardan en el chip pero se imprimen.
        """
        self._info("imprimir_serializado")
        self.controller.imprimir_serializado(tipo_tag, tag, transpose,
                                             only_buffer, extra_data)

    @method(DBUS_BUSNAME_ARMVE)
    def registrar(self, tag, solo_impimir=False, crypto_tag=None):
        """Registra un voto."""
        self._info("registrar")
        tag = b64decode(tag)
        if crypto_tag is not None:
            crypto_tag = b64decode(crypto_tag)
        return self.controller.registrar(tag, solo_impimir, crypto_tag)

    @method(DBUS_BUSNAME_ARMVE)
    def do_print(self):
        """Manda a imprimir lo que haya en buffer."""
        self._info("do_print")
        return self.controller.do_print()

    @method(DBUS_BUSNAME_ARMVE)
    def tarjeta_ingresada(self):
        """Dice si la impresora tiene o no papel."""
        self._info("tarjeta_ingresada")
        if hasattr(self, "printer"):
            ingresada = self.printer.has_paper()
        else:
            ingresada = False
        return ingresada

    @method(DBUS_BUSNAME_ARMVE)
    def full_paper_status(self):
        """Devuelve el estado completo de los sensores de papel."""
        printer_status = self.printer.get_status()
        if printer_status is not None:
            status = loads(self._prepare_response(printer_status[0]))
        else:
            status = None
        return status

    @method(DBUS_BUSNAME_ARMVE)
    def get_quality(self):
        """Devuelve la calidad de impresion."""
        return self.printer.get_quality()

    @method(DBUS_BUSNAME_ARMVE)
    def set_quality(self, level):
        """Establece la calidad de impresion."""
        self._info("set_quality")
        return self.printer.set_quality(level)

    @method(DBUS_BUSNAME_ARMVE)
    def estado(self, out_signature="b"):
        """Devuelve el estado de conexion al ARM."""
        self._info("estado")
        return self._conn

    @method(DBUS_BUSNAME_ARMVE)
    def read(self, out_signature="s"):
        """Lee un tag."""
        self._info("read")
        tag = self.controller.get_tag()
        tag = tag[1]
        return dumps(tag)

    @method(DBUS_BUSNAME_ARMVE)
    def read_metadata(self, out_signature="s"):
        """Devuelve la metadata del tag."""
        return dumps(self.controller.get_tag_metadata())

    @method(DBUS_BUSNAME_ARMVE)
    def is_read_only(self, serial_number):
        """Me dice si un tag es de solo lectura.

        Argumentos:
            serial_number -- el numero de serie del tag.
        """
        self._info("is_read_only")
        return self.rfid.is_tag_read_only(decode(serial_number, "hex_codec"))

    @method(DBUS_BUSNAME_ARMVE)
    def write(self, serial, tipo, data, marcar_ro=False):
        """Escribe un tag especifico.

        Argumentos:
            serial -- el numero de serie.
            tipo -- el tipo de tag.
            data -- los datos que se quieren guardar adentro del tag.
            marcar_ro -- si quemamos o no.
        """
        return self.controller.write(decode(serial, "hex_codec"), tipo,
                                     b64decode(data), marcar_ro)

    @signal(DBUS_BUSNAME_ARMVE)
    def connection(self, state):
        """Evento de conexion con el ARM."""
        self._info("connection: " + str(state))
        return state

    @signal(DBUS_BUSNAME_ARMVE)
    def insertando_papel(self, state):
        """Evento de insercion de papel."""
        self._info("insertando_papel")
        return state

    @signal(DBUS_BUSNAME_ARMVE)
    def autofeed_end(self, state):
        """Evento de fin de autofeed."""
        self._info("autofeed_end")
        return state

    @method(DBUS_BUSNAME_ARMVE)
    def guardar_tag(self, tipo_tag, data, marcar_ro):
        """Guarda un tag serializado.

        Argumentos:
            tipo_tag -- el tipo del tag que se quiere guardar.
            data -- los datos que se quieren guardar en el tag.
            marcar_ro -- quema el chip.
        """
        self._info("guardar_tag")
        return self.controller.guardar_tag(tipo_tag, b64decode(data),
                                           marcar_ro)

    @method(DBUS_BUSNAME_ARMVE)
    def set_tipo(self, serial, tipo):
        """Establece el tipo de tag del chip.

        Argumentos:
            serial --  el numero de serie del chip.
            tipo -- el tipo que se quiere cambiar.
        """
        return self.controller.set_tipo(decode(serial, "hex_codec"),
                                        b64decode(tipo).decode())

    @method(DBUS_BUSNAME_ARMVE)
    def get_map(self):
        """Devuelve le mapa del chip."""
        return self.controller.get_map()

    @method(DBUS_BUSNAME_ARMVE)
    def get_brightness(self):
        """Devuelve el brillo actual del backlight."""
        response = self.backlight.get_brightness()
        if response is not None:
            response = response[0]
        return self._prepare_response(response)

    @method(DBUS_BUSNAME_ARMVE)
    def set_brightness(self, value):
        """Establece el brillo del backlight."""
        return self.backlight.set_brightness(value)

    @method(DBUS_BUSNAME_ARMVE)
    def get_power_status(self):
        """Obtiene el estado de alimentacion de energia."""
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

    @method(DBUS_BUSNAME_ARMVE)
    def get_build(self):
        """Obtiene el build del firmware."""
        return self._build[1]

    @method(DBUS_BUSNAME_ARMVE)
    def get_machine_type(self):
        """Obtiene el modelo de maquina."""
        ret = None
        build = self._build
        if build is not None:
            ret = self._build[0]

        return ret

    @method(DBUS_BUSNAME_ARMVE)
    def get_antenna_level(self):
        """Obtiene el nivel de la antena."""
        response = self.rfid.get_antenna_level()
        response = response[0]
        return self._prepare_response(response)

    @method(DBUS_BUSNAME_ARMVE)
    def get_fan_speed(self):
        """Obtiene la velocidad de los fans."""
        response = self.fancoolers.get_speed()
        if response is not None:
            response = response[0]
            return self._prepare_response(response)

    @method(DBUS_BUSNAME_ARMVE)
    def set_fan_speed(self, value):
        """Establece la velocidad de los fans."""
        return self.fancoolers.set_speed(value)

    @method(DBUS_BUSNAME_ARMVE)
    def get_fan_mode(self):
        """Obtiene el modo de los fans."""
        return self._fan_auto_mode

    @method(DBUS_BUSNAME_ARMVE)
    def set_fan_auto_mode(self, value):
        """Establece el modo de los fans."""
        return self.controller.set_fan_auto_mode(value)

    @method(DBUS_BUSNAME_ARMVE)
    def agent_reset(self, device):
        """Reinicia un dispositivo."""
        return self.agent.reset(device)

    @method(DBUS_BUSNAME_ARMVE)
    def get_pir_status(self):
        """Obtiene el estado del PIR."""
        response = self.pir.status()
        response = self._prepare_response(response[0])
        return response

    @method(DBUS_BUSNAME_ARMVE)
    def get_pir_mode(self):
        """Obtiene el modo del PIR."""
        return self._usa_pir

    @method(DBUS_BUSNAME_ARMVE)
    def set_pir_mode(self, mode):
        """Establece el modo del PIR."""
        self._info("set_pir_mode")
        return self.controller.set_pir_mode(mode)

    @method(DBUS_BUSNAME_ARMVE)
    def get_autofeed_mode(self):
        """Obtiene el modo de autofeed."""
        mode = self.printer.get_autofeed()
        if mode is not None:
            mode = mode[0]
        return mode

    @method(DBUS_BUSNAME_ARMVE)
    def set_autofeed_mode(self, mode):
        """Establece el modo de autofeed."""
        self._info("set_autofeed_mode")
        return self.controller.set_autofeed_mode(mode)


if __name__ == '__main__':
    ARMVEDBus()
