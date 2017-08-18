import os
from os import mkfifo
from time import sleep
from ujson import dumps, loads

from gi.repository.GLib import IOChannel, IOCondition, Error

from msa.core.logging import get_logger

class IPC():
    """Clase base de la comunicacion entre procesos.
    """
    def __init__(self, in_path, out_path, callback_lectura):
        assert in_path is not None
        assert out_path is not None
        assert callback_lectura is not None

        self.logger = get_logger("ipc")
        self.in_path = in_path
        self.out_path = out_path
        self.callback_lectura = callback_lectura
        self.init_channels()
        self.registrar_evento()
        self.waiting_response = False
        self._response = -1

    def dumps(self, datos):
        """Serializador de mensajes."""
        return dumps(datos)

    def loads(self, datos):
        """Desserializador de mensajes."""
        return loads(datos)

    def registrar_evento(self):
        """Registra el evento de lectura."""
        self.in_channel.add_watch(IOCondition.IN, self.read_channel)

    def init_channels(self):
        """Inicializa los canales de comunicacion (entrada y salida)."""
        # Si no existe el Pipe lo creamos
        try:
            mkfifo(self.in_path)
        except FileExistsError:
            pass
        # Traemos el file descriptor de lectura en modo no bloqueante.
        in_file = os.open(self.in_path, os.O_RDONLY|os.O_NONBLOCK)
        # Inicializamos en IOChannel de Glib.
        # https://lazka.github.io/pgi-docs/#GLib-2.0/classes/IOChannel.html#GLib.IOChannel.unix_new
        self.in_channel = IOChannel.unix_new(in_file)
        # Por las dudas borramos todos los mensajes y no hacemos nada con
        # ellos.
        self.in_channel.readlines()

        # Si no existe el Pipe lo creamos
        try:
            mkfifo(self.out_path)
        except (FileExistsError, Error):
            pass
        # Traemos el file descriptor de escritura
        out_file = os.open(self.out_path, os.O_WRONLY)
        # Inicializamos en IOChannel de Glib.
        self.out_channel = IOChannel.unix_new(out_file)

    def send(self, mensaje):
        """Envia un mensaje por el canal.

        Argumentos:
            mensaje - un string con un mensaje a enviar.
        """
        try:
            self.out_channel.flush()
        except Exception:
            self.init_channels()

        msg = bytes(mensaje + "\n", "utf8")
        self.out_channel.write_chars(msg, len(msg))
        self.out_channel.flush()
        self.logger.debug("---> Enviado mensaje {}".format(msg[:20]))

    def read_channel(self, channel, *args):
        """Lee todos los mensajes en el canal.

        Argumentos:
            channel -- el canal de lectura.
        """
        # leemos todas las lineas
        data = channel.readlines()
        # agregamos el watcher al canal
        self.registrar_evento()
        # recorremos todas las lineas ya que hay un mensaje por linea.
        for datum in data:
            if datum != '':
                # limpiamos el mensaje
                callback_params = datum.strip()
                # parseamos el mensaje
                msg_type, signal, params = self.loads(callback_params)
                self.logger.info(">>> %s %s %s", msg_type, signal, params)

                # y llamamos al callback adecuado
                if self.waiting_response and msg_type == "response":
                    func = self.procesar_respuesta
                else:
                    func = self.callback_lectura

                func(self, msg_type, signal, params)

    def procesar_respuesta(self, channel, rsp_type, signal, params):
        """Procesa la respuesta que estamos esperando."""
        self.waiting_response = False
        self._response = params

    def get_ipc_method(self, method, wait_response=False):
        """ Devuelve un metodo de IPC.

        Argumentos:
            method -- el nombre de la funcion que queremos llamar.
            waiting_response -- un booleano que representa si queremos esperar
                la respuesta o no
        """
        def _inner(params=None):
            ret = None
            self.waiting_response = wait_response
            request = ["request", method, params]

            self.send(self.dumps(request))

            if self.waiting_response:
                tries = 0
                while tries < 20:
                    self.read_channel(self.in_channel)
                    if self._response == -1:
                        sleep(0.1)
                        tries += 1
                    else:
                        ret = self._response
                        self._response = -1
                        break
            return ret
        return _inner
