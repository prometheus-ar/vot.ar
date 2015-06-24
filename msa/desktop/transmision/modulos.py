# -*- coding:utf-8 -*-
""" Módulo que abstrae del manejo del lector de chips"""

from dbus.mainloop.glib import DBusGMainLoop
from json import loads
from base64 import b64decode

from msa import get_logger
from msa.core.ipc.client.rfid_controller import DbusLectorController

logger = get_logger("transmision-modulos")

# Constantes usadas para consultar el tipo de tag detectado.
NO_TAG = 'sin tag'
TAG_VACIO = 'tag vacio'
TAG_DATOS = 'tag con datos'
TAG_ERROR = 'error en tag'
TAG_COLISION = 'colision al leer tag'
TAG_ADMIN = 'tag admin'


class ModuloLector(object):
    """ Modulo con soporte para lector RFID.
        Lo único que pide su constructor es una función a ser llamada cuando
        se hace el polling (función callback).
        Para iniciar la consulta al lector, utilizar el método run(), para
        cerrarla, close().
    """

    def __init__(self, callback, comprobar_tag=True):
        """Constructor"""
        self.callback = callback
        self.loop_lector = True
        DBusGMainLoop(set_as_default=True)
        self.lector = DbusLectorController()
        self.ultimo_tag = None
        # Inicializo y limpio los callbacks adicionales
        self.clear_callbacks()
        #settings.COMPROBAR_TAG = check_tag
        self.signal = None

    def add_to_loop(self, funcion):
        self._callbacks.append(funcion)

    def clear_callbacks(self):
        self._callbacks = []

    def conectar_lector(self):
        def _callback_wrapper(mensaje, tag=None):
            if hasattr(self, 'callback') and tag is not None:
                tag = loads(tag)
                if tag is not None:
                    tag['datos'] = b64decode(tag['datos'])
                    self.callback(mensaje, tag)
                else:
                    self.callback(mensaje, {})
        if self.lector is not None:
            self.signal = self.lector.consultar_lector(_callback_wrapper)

    def desconectar_lector(self):
        self.loop_lector = False
        if self.signal is not None:
            self.signal.remove()
