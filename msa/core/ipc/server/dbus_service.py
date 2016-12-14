# -*- coding: utf-8 -*-
from __future__ import absolute_import

from dbus import service, SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository.GObject import MainLoop

from msa.core.logging import get_logger

logger = get_logger("core")


class MSADbusService(service.Object):
    """
        Clase Base para generar un servicio via DBUS.
    """

    def __init__(self, set_as_default=True):
        DBusGMainLoop(set_as_default=set_as_default)

        self.session_bus = SessionBus()
        # WARNING, NO BORRAR la asignación a la variable name aunque ésta no se
        # use, sino Dbus restartea el servicio N veces una por cada reintento
        # del cliente.
        name = service.BusName(self.bus_name, self.session_bus)
        self._service_init()
        service.Object.__init__(self, self.session_bus, self.object_path)

        self._loop = MainLoop()
        try:
            self._loop.run()
        except KeyboardInterrupt:
            pass

    def quit(self):
        """ Cierra el servicio DBUS, útil para casos de reinicio.
            DEBE ser implementado por los hijos de esta clase. """
        pass
