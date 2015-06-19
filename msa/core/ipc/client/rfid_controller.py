# coding: utf-8
import dbus
from json import loads
import gobject

from base64 import b64encode, b64decode

from msa import get_logger
from msa.core.settings import DBUS_BUSNAME_RFID, DBUS_LECTOR_PATH
from msa.core.rfid.constants import CLASE_ICODE, CLASE_ICODE2, CLASE_MIFARE


logger = get_logger("lector_client")


class DbusLectorController():
    def __init__(self, loop=None):
        self.bus = dbus.SessionBus(mainloop=loop)
        self._signal_tag = None

    def _get_lector(self, loop=None):
        try:
            lector = self.bus.get_object(DBUS_BUSNAME_RFID,
                                         DBUS_LECTOR_PATH)
        except dbus.exceptions.DBusException:
            lector = None
        return lector

    def enable_events(self):
        """ Habilita la notificación de eventos para uso automático,
            sólo funciona en ARMVE.
        """
        lector = self._get_lector()
        register_events = lector.get_dbus_method('register_events')
        register_events()

    def disable_events(self):
        """ Deshabilita la notificación de eventos para modo manual,
            sólo funciona en ARMVE.
        """
        lector = self._get_lector()
        unregister_events = lector.get_dbus_method('unregister_events')
        unregister_events()

    def events_enabled(self):
        """ Retorna True/False según estén habilitados los eventos """
        lector = self._get_lector()
        list_events = lector.get_dbus_method('list_events')
        enabled = len(loads(list_events())) > 0
        return enabled

    def get_tag(self):
        lector = self._get_lector()
        read_tag = lector.get_dbus_method('read')
        tag = read_tag()
        if tag is not None:
            tag = loads(tag)
            if tag is not None and tag.get("datos") is not None:
                tag['datos'] = b64decode(tag['datos'])
        return tag

    def get_tag_metadata(self):
        lector = self._get_lector()
        read_tag_meta = lector.get_dbus_method('read_metadata')
        tag_meta = read_tag_meta()
        if tag_meta is not None:
            tag_meta = loads(tag_meta)
        return tag_meta

    def escribe_datos(self, tag, datos, tipo_tag, marcar_ro=False):
        if tag['clase'] in (CLASE_ICODE, CLASE_ICODE2):
            try:
                lector = self._get_lector()
                write_method = lector.get_dbus_method('write')
                datos = b64encode(datos)
                write_method(tag['serial'], tipo_tag, datos, marcar_ro)
            except dbus.exceptions.DBusException:
                return False
        elif tag['clase'] == CLASE_MIFARE:
            return False
        return True

    def _intentar_conectar(self, funcion):
        ret = True
        lector = self._get_lector()
        if lector is not None:
            self.consultar_lector(funcion)
            ret = False
        return ret

    def consultar_lector(self, funcion):
        logger.debug("Registrando callback lector %s", funcion)

        def _inner(*args, **kwargs):
            funcion(*args, **kwargs)

        lector = self._get_lector()
        if lector is not None:
            self.remover_consultar_lector()
            self._signal_tag = lector.connect_to_signal("tag_leido", _inner)
        else:
            gobject.timeout_add(1000, self._intentar_conectar, _inner)

    def remover_consultar_lector(self):
        if self._signal_tag is not None:
            self._signal_tag.remove()
            self._signal_tag = None

    def update_tag(self, tipo_tag):
        """Para los poder pushear cosas al dummy."""
        lector = self._get_lector()
        update_tag = lector.get_dbus_method('update_tag')
        return update_tag(tipo_tag)

    def is_read_only(self, serial_number):
        """Para los poder pushear cosas al dummy."""
        lector = self._get_lector()
        read_only = lector.get_dbus_method('is_read_only')
        return read_only(serial_number)

    def guardar_tag(self, tipo_tag, datos, marcar_ro):
        """Guarda el tag y lo comprueba."""
        lector = self._get_lector()
        guardar_tag = lector.get_dbus_method("guardar_tag")
        return guardar_tag(tipo_tag, b64encode(datos), marcar_ro)

    def set_tipo(self, serial, tipo):
        """Establece el tipo de tag"""
        lector = self._get_lector()
        set_tipo = lector.get_dbus_method("set_tipo")
        return set_tipo(serial, tipo)

    def get_map(self):
        """Obtiene el mapa de un tag"""
        lector = self._get_lector()
        get_map = lector.get_dbus_method("get_map")
        return loads(get_map())

    def get_antenna_level(self):
        lector = self._get_lector()
        get_antenna_level = lector.get_dbus_method("get_antenna_level")
        return get_antenna_level()

    def quit(self):
        lector = self._get_lector()
        quit_method = lector.get_dbus_method('quit')
        return quit_method()

    def reset(self):
        """Resetea el lector on demand."""
        lector = self._get_lector()
        reset = lector.get_dbus_method('reset_rfid')
        return reset()
