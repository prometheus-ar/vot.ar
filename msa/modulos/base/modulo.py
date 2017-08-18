"""
Los modulos que componen al sistema.

Cada modulo es independiente, pero todos pueden heredar de Modulo para
facilitar la implementacion y mantenimiento.

Cada modulo debe tener un método main(), que puede o no devolver un
string. Si este string existe como indice del diccionario del script
de inicio, ejecuta el modulo relacionado a ese indice.
"""
import gi
# Si no Establecemos explicitamente las versiones de los modulos del
# repositorio de pygi muestra un warning
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
# Establecemos la version de WebKit (API 3.0)
try:
    gi.require_version('WebKit', '3.0')
except ValueError:
    pass
# Establecemos la version de WebKit (API 4.0)
try:
    gi.require_version('WebKit2', '4.0')
except ValueError:
    pass

from os.path import exists, join
from time import sleep
from urllib.request import pathname2url
from gi.repository import Gdk, GObject, Gtk

from msa.core.audio.player import WavPlayer
from msa.core.config_manager import Config
from msa.core.i18n import cambiar_po
from msa.modulos import get_sesion
from msa.core.config_manager.constants import COMMON_SETTINGS
from msa.modulos.base.plugins import PluginManager
from msa.modulos.constants import (APP_TITLE, MODULO_MENU, PATH_SONIDOS_VOTO,
                                   PATH_TEMPLATES_MODULOS, WINDOW_BORDER_WIDTH,
                                   PATH_MODULOS)
from msa.modulos.gui.settings import (DEBUG_ZAGUAN, FULLSCREEN, MOSTRAR_CURSOR,
                                      SCREEN_SIZE, WEBKIT_VERSION,
                                      USAR_SONIDOS_UI)

# Hilo Global del módulo para reproducir sonidos
_audio_player = None


def print_zaguan_input(msg):
    from ujson import loads
    from re import search
    from pprint import pprint

    exp = '(run_op)\\([\'"](\\w+)[\'"], [\'"](.*)[\'"]\\)'
    matches = search(exp, msg)
    if matches is not None:
        groups =  matches.groups()
        if groups[0] == "run_op":
            comando = groups[1]
            json_str = groups[2]
            print(">>>", comando)
            if comando == "set_constants":
                pprint(loads(json_str), depth=1)
            elif json_str != "null":
                print("\t", json_str[:80], "..." if len(json_str) > 80 else "")

        else:
            print(msg)
    else:
        print(msg)


class ModuloBase(object):

    """Modulo base. Implementa una pantalla y la funcionalidad basica."""

    def __init__(self, nombre):
        """ Constructor."""
        self.sesion = get_sesion()
        self.logger = self.sesion.logger
        self.logger.info("Cargando modulo {}".format(nombre))

        self.config_files = [COMMON_SETTINGS, nombre]
        self._load_config()
        self.nombre = nombre
        self.pantalla = None
        self.ret_code = ''
        self.signal = None
        self.player = None
        self.plugin_manager = PluginManager
        self.plugin_manager.autoregister()

        self.ventana = self._inicializa_ventana()
        self._cargar_ui_web()
        sleep(0.2)
        self.ventana.show_all()

    def cambiar_po(self, nombre_po):
        """Cambia la localización."""
        cambiar_po(nombre_po)

    def _inicializa_ventana(self):
        """Inicializa la ventana básica, tamaño, layout básico y títulos."""
        ventana = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        ventana.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        ventana.set_size_request(*SCREEN_SIZE)
        ventana.set_resizable(False)
        ventana.set_support_multidevice(False)

        ventana.set_title(APP_TITLE)
        ventana.set_border_width(WINDOW_BORDER_WIDTH)

        ventana.connect('destroy', self.quit)

        root_wnd = ventana.get_root_window()
        if MOSTRAR_CURSOR:
            cursor_type = Gdk.CursorType.LEFT_PTR
        else:
            cursor_type = Gdk.CursorType.BLANK_CURSOR

        cursor = Gdk.Cursor(cursor_type)
        root_wnd.set_cursor(cursor)

        if FULLSCREEN:
            ventana.fullscreen()

        self.logger.debug("Fin de inicializacion ventana")
        return ventana

    def _get_uri(self):
        html_name = '{}.html'.format(self.web_template)
        file_ = join(PATH_TEMPLATES_MODULOS, html_name)
        uri = 'file://' + pathname2url(file_)
        return uri

    def get_browser(self, uri):
        debug_callback = print_zaguan_input if DEBUG_ZAGUAN else None
        return self.controlador.get_browser(uri, debug=DEBUG_ZAGUAN,
                                            webkit_version=WEBKIT_VERSION,
                                            debug_callback=debug_callback)

    def _webkit2_touch(self, widget, event):
        """ Webkitgtk 2 no lanza el evento del DOM touchend y touchmove por un
        bug https://bugs.webkit.org/show_bug.cgi?id=158531 Por lo tanto muchos
        clicks no son capturados correctamente.

        Esta funcion intenta parchear el comportamiento y emitir el click
        cuando la persona hace algo con el dedo que no sea "el tipico click
        con la punta del dedo" la mayoría de los clicks con la yema entran en
        por este camino.
        """
        # Agarro el evento de inicio del touch y guardo x, y timestamp
        if event.touch.type == Gdk.EventType.TOUCH_BEGIN:
            self.last_start = (event.x, event.y, event.get_time())
        elif event.touch.type == Gdk.EventType.TOUCH_END:
            # Establezco la diferencia para los dos ejes
            dx = abs(self.last_start[0] - event.x)
            dy = abs(self.last_start[1] - event.y)
            # si hubo algun evento de touch start (que debería siempre haber) y
            # los dedos se movieron menos de 20 pixeles en ambas direcciones
            if self.last_start is not None and dx < 20 and dy < 20:
                # en alguno de los dos ejes el dedo de tiene que haber movido
                # al menos dos pixeles
                dist_diff = dx > 2 or dy > 2
                time_diff = event.get_time() - self.last_start[2]
                # y el tiempo de click tiene que ser mayor a 250 milisegundos
                if dist_diff and time_diff > 250:
                    data = {
                        "x": event.x,
                        "y": event.y,
                        "dx": dx,
                        "dy": dy
                    }
                    # Lanzo un click en la posicion del final del click
                    self.controlador.send_command("lanzar_click", data)

    def _cargar_ui_web(self, agregar=True):
        """Carga el browser y lo mete en la ventana contenedora."""
        uri = self._get_uri()
        self.browser = self.get_browser(uri)

        self.last_start = None
        self.browser.connect('touch-event', self._webkit2_touch)

        self.ventana.set_border_width(0)
        if agregar and self.browser is not None:
            self._agregar_browser()

    def _agregar_browser(self):
        """Agrega el browser a la ventana."""
        self.ventana.add(self.browser)

    def _descargar_ui_web(self):
        """Descarga la UI web."""
        if self.browser is not None:
            self.ventana.remove(self.browser)

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

    def main(self, titulo=None):
        """ Ejecuta el sistema """

        Gdk.threads_init()

        # Habilito el modo touchscreen, que desactiva el hover del cursor
        #settings = Gtk.Settings.get_default()
        #settings.set_property('gtk-long-press-time', 5000)

        self.loop = GObject.MainLoop()
        if titulo is not None:
            self.ventana.set_title(titulo)
        self.loop.run()
        return self.ret_code

    def quit(self, w=None):
        """ Ejecuta Gtk.main_quit() y termina la ejecucion. """
        if hasattr(self, "rampa") and self.rampa is not None:
            self.rampa.remover_consultar_lector()
            self.rampa.remover_consultar_tarjeta()
            self.rampa.desregistrar_eventos()

        if hasattr(self, 'pantalla') and self.pantalla is not None:
            self.pantalla.destroy()
        if hasattr(self, "browser") and self.browser is not None:
            if hasattr(self, "ventana"):
                self.ventana.remove(self.browser)
            self.browser.destroy()
        if hasattr(self, "ventana"):
            self.ventana.destroy()
        if hasattr(self, "loop"):
            self.loop.quit()
        return False

    def admin(self):
        """Levanta el modulo menu."""
        self.salir_a_modulo(MODULO_MENU)

    def salir_a_modulo(self, modulo):
        """Sale a un cierto modulo.

        Argumentos:
            modulo -- el modulo al que sale.
        """
        self.logger.debug("Saliendo a modulo {}".format(modulo))
        self.ret_code = modulo
        self.quit()

    def hide_dialogo(self):
        """Esconde el dialogo."""
        self.controlador.hide_dialogo()

    def _start_audio(self):
        """Inicia el audioplayer."""
        global _audio_player
        if (USAR_SONIDOS_UI and (_audio_player is None or not
                                 _audio_player.is_alive())):
            _audio_player = WavPlayer()
            _audio_player.start()
        self._player = _audio_player

    def _stop_audio(self):
        """Para el audioplayer."""
        global _audio_player
        if _audio_player is not None:
            _audio_player.stop()

    def _play(self, nombre_sonido):
        """Ejecuta los audios de interacción con el usuario.

        Argumentos:
            nombre_sonido -- el nomre del archivo que queremos ejecutar.
        """
        if USAR_SONIDOS_UI:
            self._start_audio()
            sonido = join(PATH_SONIDOS_VOTO, '{}.wav'.format(nombre_sonido))
            self._player.play(sonido)

    def play_sonido_ok(self):
        """Ejecuta el sonido de "OK"."""
        self._play("ok")

    def play_sonido_warning(self):
        """Ejecuta el sonido de "Warning"."""
        self._play("warning")

    def play_sonido_error(self):
        """Ejecuta el sonido de "Error"."""
        self._play("error")

    def play_sonido_tecla(self):
        """Ejecuta el sonido de "Tecla presionada"."""
        self._play("tecla")

    def _load_config(self):
        """Carga las configuraciones para esta ubicación."""
        id_ubicacion = None
        if self.sesion.mesa is not None:
            id_ubicacion = self.sesion.mesa.codigo
        self._config = Config(self.config_files, id_ubicacion)

    def config(self, key):
        """Devuelve una cofiguracion particular para esta ubicación.

        Argumentos:
            key -- la key de la cual queremos traer el valor.
        """
        value, file_ = self._config.data(key)
        self.logger.debug("Trayendo config {}: {} desde {}".format(key, value,
                                                              file_))
        return value

    def en_disco(self, nombre_modulo):
        """Devuelve la existencia de un modulo.

        Argumentos:
            nombre_modulo -- el nombre del modulo que queremos averiguar si
                está en el disco actual
        """
        return exists(join(PATH_MODULOS, nombre_modulo))

