
# -*- coding: utf-8 -*-
"""Los modulos que componen al sistema.

Cada modulo es independiente, pero todos pueden heredar de Modulo para
facilitar la implementacion y mantenimiento.

Cada modulo debe tener un método main(), que puede o no devolver un
string. Si este string existe como indice del diccionario del script
de inicio, ejecuta el modulo relacionado a ese indice.

Por ejemplo, sin en el script de inicio tenemos el diccionario:

modulos = {'voto': ModuloVoto, 'escrutinio': ModuloEscrutinio}

si al salir de un modulo devuelvo 'escrutinio', el script de inicio
deberia llamar instanciar un ModuloEscrutinio, y ejecutar su metodo
main():
"""

import gtk
import gobject
import os
import time
import urllib

from msa.voto.constants import MODULO_ADMIN, WINDOW_BORDER_WIDTH, APP_TITLE
from msa.voto.sesion import get_sesion
from msa.voto.settings import SCREEN_SIZE, MOSTRAR_CURSOR, FULLSCREEN, \
    PATH_TEMPLATES_VOTO, USAR_CEF, DEBUG_ZAGUAN

sesion = get_sesion()


class Modulo(object):

    """Modulo base. Implementa una pantalla y la funcionalidad basica."""

    def __init__(self):
        """ Constructor.
        """
        self.seleccion = None
        self.pantalla = None
        self.ret_code = ''
        self.signal = None
        self.exiting = False

        self.ventana = self._inicializa_ventana()
        es_modulo_web = getattr(self, "es_modulo_web", False)
        if es_modulo_web:
            self._cargar_ui_web()
        time.sleep(0.2)
        self.ventana.show_all()

    def crear_cursor_vacio(self):
        pix_data = """/* XPM */
        static char * invisible_xpm[] = {
        "1 1 1 1",
        "       c None",
        " "};"""
        color = gtk.gdk.Color()
        pix = gtk.gdk.pixmap_create_from_data(None, pix_data, 1, 1, 1, color,
                                              color)
        return gtk.gdk.Cursor(pix, pix, color, color, 0, 0)

    def _inicializa_ventana(self):
        # Inicializa la ventana básica, tamaño, layout básico y títulos
        ventana = gtk.Window(gtk.WINDOW_TOPLEVEL)
        ventana.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        ventana.set_size_request(*SCREEN_SIZE)
        ventana.connect('destroy', self.quit)
        ventana.set_title(APP_TITLE)
        ventana.set_border_width(WINDOW_BORDER_WIDTH)

        root_wnd = ventana.get_root_window()
        if MOSTRAR_CURSOR:
            root_wnd.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
        else:
            root_wnd.set_cursor(self.crear_cursor_vacio())
            ventana.realize()

        if FULLSCREEN:
            if os.name == 'posix':
                ventana.fullscreen()
            else:
                # Hack: En windows el fullscreen no funciona al 100%
                ventana.maximize()
                ventana.set_decorated(False)

        return ventana

    def _cargar_ui_web(self, agregar=True):
        file_ = os.path.join(PATH_TEMPLATES_VOTO,
                             '%s.html' % self.web_template)
        uri = 'file://' + urllib.pathname2url(file_)
        if USAR_CEF:
            self.browser = self.controller.get_cef_browser(uri, self.ventana,
                                                           debug=DEBUG_ZAGUAN)
        else:
            self.browser = self.controller.get_browser(uri, debug=DEBUG_ZAGUAN)

        self.ventana.set_border_width(0)
        if agregar and self.browser is not None:
            self._agregar_browser()
        elif self.browser is None and USAR_CEF:
            gobject.timeout_add(10, self.OnTimer)

    def OnTimer(self):
        if self.exiting:
            return False
        from cefpython3 import cefpython
        cefpython.MessageLoopWork()
        return True

    def _agregar_browser(self):
        self.ventana.add(self.browser)

    def _descargar_ui_web(self):
        if self.browser is not None:
            self.ventana.remove(self.browser)
        elif USAR_CEF:
            self.exiting = True
            if hasattr(self.controller, "cef_window"):
                self.controller.cef_window.CloseBrowser()

    def _set_titulo(self, titulo=None, subtitulo=None):
        if hasattr(self, "panel_superior"):
            self.panel_superior.set_titulos(titulo, subtitulo)

    def set_pantalla(self, pantalla):
        """ Establece y muestra la pantalla en el panel principal del modulo

            Argumentos:
            pantalla -- la pantalla a mostrar. En realidad se muestra el
                        atributo panel de esta pantalla
        """
        if hasattr(self, 'pantalla') and self.pantalla is not None and \
                len(self.panel.get_children()) > 0:
            self.panel.remove(self.pantalla)
            self.pantalla.destroy()
            self.pantalla = None

        self.pantalla = pantalla
        self.panel.add(self.pantalla)
        self.ventana.show_all()

    def main(self):
        """ Ejecuta el sistema """

        if os.name == 'posix':
            # Imprescindible para que funcionen los threads, en unix.
            gtk.gdk.threads_init()

        # Habilito el modo touchscreen, que desactiva el hover del cursor
        settings = gtk.settings_get_default()
        settings.set_property('gtk-touchscreen-mode', True)

        self.loop = gobject.MainLoop()
        self.loop.run()
        return self.ret_code

    def quit(self, w=None):
        """ Ejecuta gtk.main_quit() y termina la ejecucion. """
        if self.signal is not None:
            self.signal.remove()
        if hasattr(self, "signal_papel") and self.signal_papel is not None:
            self.signal_papel.remove()

        if sesion.lector is not None:
            sesion.lector.remover_consultar_lector()
        if sesion.impresora is not None:
            sesion.impresora.remover_consultar_tarjeta()
        if hasattr(self, "rampa"):
            self.rampa.desregistrar_eventos()

        self.browser.destroy()
        self.ventana.destroy()
        if hasattr(self, "loop"):
            self.loop.quit()
        return False

    def admin(self):
        self.ret_code = MODULO_ADMIN
        self.quit()
