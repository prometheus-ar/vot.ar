from base64 import b64encode
from os import urandom

from construct.core import FieldError
from cryptography.exceptions import InvalidTag

from msa.core.documentos.soporte_digital import SoporteDigital
from msa.core.ipc import IPC
from msa.core.ipc.settings import DOWNSTREAM_CHANNEL, UPSTREAM_CHANNEL
from msa.core.logging import get_logger
from msa.core.rfid.constants import TAG_VOTO


class IPCClient(IPC):

    """IPC para el cliente."""

    def __init__(self, sesion, in_path=DOWNSTREAM_CHANNEL,
                 out_path=UPSTREAM_CHANNEL):
        """Constructor.

        Argumentos:
            sesion -- un objeto de tipo Sesion.
            in_path -- un pipe para comunicarse con el servicio
            out_path -- un pipe para recibir las comunicaciones que manda el
            servicio
        """
        self.sesion = sesion
        self.signals = {}
        IPC.__init__(self, in_path, out_path, self.callback)
        self.tiene_papel = self._estado_papel()
        self.logger = get_logger("ipc_client")

    def connect_to_signal(self, signal, callback):
        """Conecta una señal a un callback.

        Argumentos:
            signal -- un string con el nombre de la señal.
            callback -- el callback al que llama cuando dispara la señal.
        """
        self.signals[signal] = callback

    def remove_signal(self, signal):
        """desconecta el callback de una señal.

        Argumentos:
            signal -- un string con el nombre de la señal.
        """
        if signal in self.signals:
            del self.signals[signal]

    def callback(self, channel, rsp_type, signal, params):
        """Callback de llamada de las respuestas. Despacha los eventos.

        Argumentos:
            channel -- el canal de comunicacion en el que ser produce la
                respuesta.
            rsp_type -- tipo de respuestas.
            signal -- el identificador d ela señal que llegó.
            params -- los parametros de la respuesta.
        """
        if rsp_type == "event":
            func = self.signals.get(signal)
            if func is not None:
                func(params)

    def async(self, method_name, callback, params=None):
        """llama a una funcion del servicio y llama a un callback para
        procesar la respuesta asincronicamente.

        Argumentos:
            method_name -- nombre del metodo del servicio que queremos correr.
            callback -- el callback que se va a llamar con la respuesta.
            params -- los parametros que le vamos a mandar al servicio.

        """
        # generamos un nombre de señal aleatorio.
        signal_id = b64encode(urandom(8)).decode("utf8")

        def _inner(ret_params):
            """Remueve la señal efimera que creamos y llama al callback con
                los parametros."""
            self.remove_signal(signal_id)
            callback(ret_params)


        # registramos el callback efimero
        self.connect_to_signal(signal_id, _inner)

        # ejecutamos el parametro async
        method = self.get_ipc_method("async")
        if params is None:
            params = []
        method([signal_id, method_name, params])

    def _estado_papel(self):
        """Devuelve el estado del papel."""
        method = self.get_ipc_method('tarjeta_ingresada', True)
        return method()

    def expulsar_boleta(self):
        """Envia la señal de expulsar la boleta."""
        func = self.get_ipc_method('expulsar_boleta')
        func()

    def remover_consultar_tarjeta(self):
        """Desregistra el evento de consultar tarjeta."""
        self.remove_signal("con_tarjeta")

    def remover_error_impresion(self):
        """Desregistra el evento de consultar tarjeta."""
        self.remove_signal("error_impresion")

    def remover_fin_impresion(self):
        """Desregistra el evento de fin de impresion."""
        self.remove_signal("fin_impresion")

    def remover_consultar_lector(self):
        """Desregistra evento de consultar_lector."""
        self.remove_signal("tag_leido")

    def remover_insertando_papel(self):
        """Remueve el evento de inserción de papel."""
        self.remove_signal("insertando_papel")

    def remover_autofeed_end(self):
        """Remueve el evento de final de autofeed."""
        self.remove_signal("autofeed_end")

    def remover_boleta_expulsada(self):
        """Remueve el evento de boleta expulsada."""
        self.remove_signal("boleta_expulsada")

    def registrar_autofeed_end(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            final de autofeed.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """
        def _inner(data):
            """Intercepta el callback para establecer el estado local del
            papel.
            """
            if data is not None and 'sensor_1' in data:
                self.tiene_papel = data['sensor_1']
            callback(data)
        self.connect_to_signal("autofeed_end", _inner)

    def consultar_lector(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            cambio de estado de RFID.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """

        def _inner(params):
            """Parsea el tag del evento que recibimos.

            Argumentos:
                params -- los parametros que envia el evento.
            """
            tipo_lectura, tag_dict = params
            tag = self._parse_tag(tag_dict)
            callback(tipo_lectura, tag)

        self.connect_to_signal("tag_leido", _inner)

    def registrar_fin_impresion(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            fin de impresion.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """

        def _inner(data):
            """Remueve el evento de fin de impresion y llama al callback."""
            self.remover_fin_impresion()
            callback()

        self.connect_to_signal("fin_impresion", _inner)

    def registrar_error_impresion(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            error de impresion.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """

        def _inner(data):
            """Remueve el evento de erro de impresion y llama al callback."""
            self.remover_error_impresion()
            callback()

        self.connect_to_signal("error_impresion", _inner)

    def registrar_insertando_papel(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            inserción de papel.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """

        def _inner(data):
            """Intercepta el callback para establecer el estado local del
            papel.
            """
            if data is not None and 'sensor_1' in data:
                self.tiene_papel = data['sensor_1']
            callback(data)

        self.connect_to_signal("insertando_papel", _inner)

    def consultar_tarjeta(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            consultar_tarjeta.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """
        def _inner(data):
            """Intercepta el callback para establecer el estado local del
            papel.
            """
            if data is not None and 'sensor_1' in data:
                self.tiene_papel = data['sensor_1']
            callback(data)

        self.connect_to_signal("con_tarjeta", _inner)

    def registrar_boleta_expulsada(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            boleta expulsada.

        Argumentos:
            callback -- la funcion que se va a ejecutar.
        """
        self.connect_to_signal("boleta_expulsada", callback)

    def get_tag(self):
        """Devuelve el tag que esté puesto en el lector."""
        read_tag = self.get_ipc_method('read', True)
        tag_data = read_tag()
        return self._parse_tag(tag_data)

    def get_tag_metadata(self):
        """Devuelve la metadata del tag que esté puesto en el lector."""
        read_tag_metadata = self.get_ipc_method('read_metadata', True)
        meta = read_tag_metadata()
        return meta

    def is_read_only(self, serial):
        """Nos indica si un tag es de solo lectura.

        Argumentos:
            serial -- el numero de serie del tag.
        """
        method = self.get_ipc_method('is_read_only', True)
        return method([serial])

    def set_tipo_tag(self, serial, tipo):
        """Establece el tipo de tag.

        Argumentos:
            serial -- el numero de serie del tag.
            tipo -- el tipo de tag que queremos establecer.
        """
        method = self.get_ipc_method('set_tipo_tag', True)
        return method([serial, tipo])

    def get_map(self):
        """Devuelve el mapa completo del user space del tag."""
        method = self.get_ipc_method('get_map', True)
        return method()

    def _parse_tag(self, tag_data):
        """Parsea el tag. Devuelve un objeto SoporteDigital.

        Argumentos:
            tag_data -- la data del tag que queremos parsear
        """
        tag = None
        # viene en None si no hay tag presente.
        if tag_data is not None:
            try:
                # parseamos el tag y lo metemos en un SoporteDigital
                tag = SoporteDigital.desde_dict(tag_data)
            except TypeError:
                pass

        # si es un tag vamos a desencriptarlo (si esta encriptado y es válido)
        if tag is not None and tag.tipo == TAG_VOTO:
            try:
                # conseguimos la aes key para desencriptarlo
                aes_key = self.sesion.mesa.get_aes_key()
                # si la clave aes está presente tratamos de desencritar,
                # si falla devolvemos lo mismo que devolvería el evento de "no
                # tengo mas tag"
                if aes_key is not None:
                    try:
                        # el tag se sabe desencriptar a si mismo.
                        tag.desencriptar_voto(aes_key)
                    except InvalidTag:
                        self.logger.debug("Falló la validacion de CGM Tag.")
                        tag = None
                    except FieldError:
                        self.logger.debug("Tag con información invalida.")
                        tag = None
            except AttributeError:
                self.logger.debug("Sin AES key en sesión.")

        return tag

    def registrar_voto(self, seleccion, solo_impimir, aes_key, callback):
        """Registra (Guarda el tag + imprime el papel) el voto.
        Llama a un callback con el estado cuanto termina de registrar.

        Argumentos:
            seleccion -- el objeto Seleccion con el voto que queremos grabar.
            solo_impimir -- si queremos imprimir pero no guardar el tag.
            aes_key -- la clave aes con la que vamos a encriptar.
            callback -- el callback que vamos a llamar cuando termine el
                proceso de registro
        """
        tag = b64encode(seleccion.a_tag())
        aes_key = b64encode(aes_key)

        self.async("registrar", callback, [tag, solo_impimir, aes_key])

    def guardar_tag(self, tipo_tag, datos, marcar_ro):
        """Guarda el tag y lo comprueba.

        Argumentos:
            tipo_tag -- el tipo de tag que queremos guardar.
            datos -- los datos que queremos guardar en el tag.
            marcar_ro -- si quemamos o no el tag despues de guardar.
        """
        guardar_tag = self.get_ipc_method("guardar_tag", True)
        return guardar_tag([tipo_tag, b64encode(datos), marcar_ro])

    def guardar_tag_async(self, callback, tipo_tag, datos, marcar_ro):
        """Guarda el tag y lo comprueba. Igual que guardar_tag pero lo hace
        asincronicamente y llama a un callback cuando termina.

        Argumentos:
            callback -- el callback que llama cuando termina de guardar.
            tipo_tag -- el tipo de tag que queremos guardar.
            datos -- los datos que queremos guardar en el tag.
            marcar_ro -- si quemamos o no el tag despues de guardar.
        """
        return self.async("guardar_tag", callback, [tipo_tag, b64encode(datos),
                                                    marcar_ro])

    def imprimir_serializado(self, tipo_tag, tag, transpose=False,
                             only_buffer=False, extra_data=None):
        """Imprime un documento mandando la informacion para armar el documento
        en vez de el documento en cuestion.

        Argumentos:
            tipo_tag -- el tipo de tag que queremos guardar.
            tag -- el tag que usamos para obtener la imagen.
            transpose -- transpone la imagen (se usa para las actas).
            only_buffer -- solo carga el buffer de impresion.
            extra_data -- los datos extras que necesitemos apra generar la
                imagen
        """
        if extra_data is None:
            extra_data = "{}"

        method = self.get_ipc_method('imprimir_serializado')
        return method([tipo_tag, tag, transpose, only_buffer, extra_data])

    def reset(self, device):
        """Resetea un dispositivo.

        Argumentos:
            device -- el identificador de dispositivo que queremos reinicial
        """
        reset = self.get_ipc_method("reset_device")
        return reset([device])

    def reset_rfid(self):
        """Resetea el RFID y espera que termine de resetear para devolver el
        control.
        """

        reset = self.get_ipc_method("reset_rfid", True)
        return reset()

    def get_arm_version(self):
        """Devuelve la version del ARM."""
        method = self.get_ipc_method("get_arm_version", True)
        return method()

    def get_arm_build(self):
        """Devuelve el build del ARM."""
        method = self.get_ipc_method("get_arm_build", True)
        return method()

    def get_antenna_level(self):
        """Devuelve el nivel de la antena."""
        method = self.get_ipc_method("get_antenna_level", True)
        return method()

    def get_brightness(self):
        """Devuelve el brillo de la pantalla."""
        method = self.get_ipc_method("get_brightness", True)
        return method()

    def set_brightness(self, value):
        """Establece el brillo de la pantalla.

        Argumentos:
            value -- el valor de brillo que queremos establecer.
        """
        method = self.get_ipc_method("set_brightness")
        return method([value])

    def get_fan_mode(self):
        """Devuelve el modo del fan."""
        method = self.get_ipc_method("get_fan_mode", True)
        return method()

    def set_fan_mode(self, value):
        """Establece el modo del fan.

        Argumentos:
            value -- el modo que queremos establecer.
        """
        method = self.get_ipc_method("set_fan_mode")
        return method([value])

    def get_fan_speed(self):
        """Devuelve la velocidad del fan."""
        method = self.get_ipc_method("get_fan_speed", True)
        return method()

    def set_fan_speed(self, value):
        """Establece la velocidad del fan.

        Argumentos:
            value -- el valor de velocidad de los fans que queremos establecer.
        """
        method = self.get_ipc_method("set_fan_speed")
        return method([value])

    def get_autofeed_mode(self):
        """Devuelve el modo del autofeed."""
        method = self.get_ipc_method("get_autofeed_mode", True)
        return method()

    def set_autofeed_mode(self, value):
        """Establece el modo del autofeed.

        Argumentos:
            value -- el valor del autofeed.
        """
        method = self.get_ipc_method("set_autofeed_mode")
        return method([value])

    def get_printer_quality(self):
        method = self.get_ipc_method("get_printer_quality", True)
        return method()

    def set_printer_quality(self, value):
        """Establece la calidad de la impresora.

        Argumentos:
            value -- el valor que queremos establecer.
        """
        method = self.get_ipc_method("set_printer_quality")
        return method([value])

    def registrar_ac(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            cambio de fuente de alimentación a AC.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("switch_ac", callback)

    def registrar_battery_discharging(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            bateria descargandose.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("battery_discharging", _inner)

    def registrar_battery_plugged(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            bateria conectada.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("battery_plugged", _inner)

    def registrar_battery_unplugged(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            bateria desconectada.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("battery_unplugged", _inner)

    def registrar_pir_detected(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            PIR detectado.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("pir_detected", _inner)

    def registrar_pir_not_detected(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            PIR no detectado.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("pir_not_detected", _inner)

    def remover_ac(self):
        """Remueve el evento de cambio de AC."""
        self.remove_signal("switch_ac")

    def remover_battery_discharging(self):
        """Remueve el evento de descarga de bateria."""
        self.remove_signal("battery_discharging")

    def remover_battery_plugged(self):
        """Remueve el evento de bateria conectada."""
        self.remove_signal("battery_plugged")

    def remover_battery_unplugged(self):
        """Remueve el evento de bateria desconectada."""
        self.remove_signal("battery_unplugged")

    def remover_pir_detected(self):
        """Remueve el evento de pir detectado."""
        self.remove_signal("pir_detected")

    def remover_pir_not_detected(self):
        """Remueve el evento de pir no detectado."""
        self.remove_signal("pir_not_detected")

    def get_power_source(self):
        """Devuelve la fuente de alimentación."""
        method = self.get_ipc_method("get_power_source", True)
        return method()

    def get_power_status(self):
        """Devuelve el estado de las fuentes de energía."""
        method = self.get_ipc_method("get_power_status", True)
        return method()

    def get_pir_status(self):
        """Devuelve el estado del PIR."""
        method = self.get_ipc_method("get_pir_status", True)
        return method()

    def get_pir_mode(self):
        """Devuelve el modo del PIR."""
        method = self.get_ipc_method("get_pir_mode", True)
        return method()

    def registrar_reset_device(self, callback):
        """Registra el callback que se ejecuta cuando recibe el evento de
            dispositivo registrado.

        Argumentos:
            callback -- el callback que se llama cuando se dispara el evento.
        """
        def _inner(data):
            callback(data)
        self.connect_to_signal("reset_device", _inner)

    def remover_reset_device(self):
        """Remueve el evento de dispositivo reseteado."""
        self.remove_signal("reset_device")
