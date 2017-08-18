from base64 import b64decode
from codecs import decode

from gi.repository.GObject import timeout_add

from msa.core.armve.constants import DEV_AGENT, DEV_PRINTER, DEV_PWR, DEV_RFID
from msa.core.ipc import IPC
from msa.core.ipc.server.decorators import method, signal
from msa.core.ipc.settings import DOWNSTREAM_CHANNEL, UPSTREAM_CHANNEL
from msa.core.logging import get_logger


class IPCServer(IPC):
    def __init__(self, callback, parent):
        """Constructor overrideado para el server."""
        IPC.__init__(self, UPSTREAM_CHANNEL, DOWNSTREAM_CHANNEL, callback)
        self.parent = parent
        self.controller = parent.controller
        self.logger = get_logger("ipc_server")

    def _info(self, func):
        """Decorador de logging de llamado a funciones."""
        self.logger.info("llamando a %s" % func)

    @signal
    def tag_leido(self, tipo_tag, tag):
        return tipo_tag, tag

    @signal
    def connection(self, conn_status):
        return conn_status

    @signal
    def con_tarjeta(self, response):
        """Eventonto de tengo papel."""
        self._info("con tarjeta")
        return response

    @signal
    def autofeed_end(self, response):
        """Evento de fin de autofeed."""
        self._info("autofeed_end")
        return response

    @method
    def read(self):
        tag = self.controller.get_tag()
        tag = tag[1]
        return self.dumps(tag)

    @method
    def read_metadata(self):
        """Devuelve la metadata del tag."""
        return self.parent.controller.get_tag_metadata()

    @method
    def is_read_only(self, serial_number):
        """Me dice si un tag es de solo lectura.

        Argumentos:
            serial_number -- el numero de serie del tag.
        """
        self._info("is_read_only")
        return self.parent.rfid.is_tag_read_only(decode(serial_number,
                                                        "hex_codec"))

    @method
    def set_tipo_tag(self, serial, tipo):
        """Establece el tipo de tag del chip.

        Argumentos:
            serial --  el numero de serie del chip.
            tipo -- el tipo que se quiere cambiar.
        """
        return self.parent.controller.set_tipo(decode(serial, "hex_codec"),
                                               tipo)

    @method
    def get_map(self):
        """Devuelve le mapa del chip."""
        return self.parent.controller.get_map()

    @method
    def tarjeta_ingresada(self):
        """Dice si la impresora tiene o no papel."""
        self._info("tarjeta_ingresada")
        if hasattr(self.parent, "printer"):
            ingresada = self.parent.printer.has_paper()
        else:
            ingresada = False

        return ingresada

    @method
    def registrar(self, tag, solo_impimir, aes_key):
        """Registra un voto."""
        self._info("registrar")
        exito = False
        try:
            tag = b64decode(tag)
            aes_key = b64decode(aes_key)
            exito = self.controller.registrar(tag, solo_impimir, aes_key)
        except Exception as exc:
            self.logger.exception(exc)

        return exito

    @method
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

    @method
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
        try:
            self.controller.imprimir_serializado(tipo_tag, tag, transpose,
                                                 only_buffer, extra_data)
        except Exception as exc:
            # Agarramos todos los errores de impresión que no hayamos agarrrado
            self.error_impresion()
            self.logger.exception(exc)

    @signal
    def reset_device(self, number):
        """Resetea el dispositivo.

        Argumentos:
            number -- el numero de dispositivo a reiniciar.
        """
        self.logger.info("Reinicializando dispositivo %s", number)
        if hasattr(self.parent, "power_manager"):
            self.parent.power_manager.set_leds(7, 1, 200, 1000)
        func = None
        if number == DEV_AGENT:
            func = self.parent.initialize
        elif number == DEV_PWR:
            func = self.parent._eventos_power
        elif number == DEV_PRINTER:

            def _inner():
                self.parent._eventos_impresora()
                self.parent._set_autofeed()
                self.parent._set_print_quality()

            func = _inner
        elif number == DEV_RFID:
            func = self.parent._eventos_rfid

        if func is not None:
            timeout_add(100, func)

        return number

    @signal
    def expulsar_boleta(self):
        """Expulsa la boleta."""
        self._info("expulsar_boleta")
        if hasattr(self.parent, "power_manager"):
            self.parent.power_manager.set_leds(1, 1, 200, 400)
            self.parent.printer.register_paper_eject()
            self.parent.printer.paper_eject()

    @signal
    def fin_impresion(self):
        self._info("fin_impresion")
        self.expulsar_boleta()

    @signal
    def boleta_expulsada(self):
        """Evento de Boleta expulsada."""
        self._info("boleta_expulsada")
        return None

    @signal
    def insertando_papel(self, state):
        """Evento de insercion de papel."""
        self._info("insertando_papel")
        return state

    @method
    def async(self, signal_id, method_name, params):
        method = getattr(self, method_name)
        if method is not None:
            response = method(*params)
            self.send(self.dumps(["event", signal_id, response]))

    @method
    def get_arm_build(self):
        """Obtiene el build del firmware."""
        return self.parent._build[1]

    @method
    def get_arm_version(self):
        """Obtiene el modelo de maquina."""
        ret = None
        build = self.parent._build
        if build is not None:
            ret = build[0]

        return ret

    @method
    def get_antenna_level(self):
        """Obtiene el nivel de la antena."""
        response = self.parent.rfid.get_antenna_level()
        response = response[0]
        return response

    @method
    def get_brightness(self):
        """Devuelve el brillo actual del backlight."""
        response = self.parent.backlight.get_brightness()
        if response is not None:
            response = response[0]
        return response

    @method
    def set_brightness(self, value):
        """Establece el brillo del backlight."""
        self.parent.backlight.set_brightness(value)

    @method
    def get_fan_mode(self):
        """Obtiene el modo de los fans."""
        return self.parent._fan_auto_mode

    @method
    def set_fan_mode(self, value):
        """Establece el modo de los fans."""
        return self.parent.controller.set_fan_auto_mode(value)

    @method
    def get_fan_speed(self):
        """Obtiene la velocidad de los fans."""
        response = self.parent.fancoolers.get_speed()
        if response is not None:
            response = response[0]
            return response

    @method
    def set_fan_speed(self, value):
        """Establece la velocidad de los fans."""
        self.parent.fancoolers.set_speed(value)

    @method
    def get_autofeed_mode(self):
        """Obtiene el modo de autofeed."""
        mode = self.parent.printer.get_autofeed()
        if mode is not None:
            mode = mode[0]
        return mode

    @method
    def set_autofeed_mode(self, mode):
        """Establece el modo de autofeed."""
        self._info("set_autofeed_mode")
        self.parent.controller.set_autofeed_mode(mode)

    @method
    def get_printer_quality(self):
        """Devuelve la calidad de impresion."""
        return self.parent.printer.get_quality()

    @method
    def set_printer_quality(self, level):
        """Establece la calidad de impresion."""
        self._info("set_quality")
        self.parent.printer.set_quality(level)

    @signal
    def battery_discharging(self):
        """Evento de descarga de baterias."""
        self.parent.controller.power_source_change(False)
        self._info("battery_discharging")

    @signal
    def switch_ac(self):
        """Evento de switcheo a AC."""
        self.parent.controller.power_source_change(True)
        self._info("switch_ac")

    @signal
    def battery_unplugged(self):
        """Evento de bateria desenchufada."""
        self._info("battery_unplugged")

    @signal
    def battery_plugged(self):
        """Evento de bateria enchufada."""
        self._info("battery_plugged")

    @signal
    def pir_detected(self):
        """Evento de PIR detectado."""
        self._info("pir_detected")
        self.parent.controller.pir_detected_cb(True)

    @signal
    def pir_not_detected(self):
        """Evento de PIR no detectado."""
        self._info("pir_not_detected")
        self.parent.controller.pir_not_detected_cb(True)

    @method
    def get_power_source(self):
        """Devuelve cual es la fuente de alimentacion."""
        self._info("get_power_source")
        response = self.parent.power_manager.get_power_source()
        if response is not None:
            response = response[0]
            self.parent.controller.get_power_source_cb(response)
            return response

    @method
    def get_power_status(self):
        """Obtiene el estado de alimentacion de energia."""
        response = self.parent.power_manager.get_status()
        if response is not None:
            response = response[0]

            batteries = []
            for batt in response["batt_data"]:
                batteries.append(batt)
            response["batt_data"] = batteries

            return response

    @method
    def get_pir_status(self):
        """Obtiene el estado del PIR."""
        response = self.parent.pir.status()
        return response[0]

    @method
    def get_pir_mode(self):
        """Obtiene el modo del PIR."""
        return self.parent._usa_pir

    @signal
    def error_impresion(self):
        """Evento de fin de autofeed."""
        self._info("error_impresion")

    @method
    def reset_rfid(self):
        self.reset_device(DEV_RFID)

