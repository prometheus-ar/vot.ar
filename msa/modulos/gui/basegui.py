"""Modulo con algunas clases base para las interfaces graficas de Gtk.
"""
import gi

gi.require_version('Pango', '1.0')
from gi.repository.Pango import FontDescription

from gi.repository import Gtk, Gdk

from msa.modulos.constants import FONT_NAME


class MsgDialog(Gtk.MessageDialog):

    """Muestra un dialogo modal de error o de información."""



    def __init__(self, mensaje):
        """Constructor.

        Argumentos:
        mensaje -- El mddensaje a mostrar.
        """
        tipo = Gtk.MessageType.OTHER

        Gtk.MessageDialog.__init__(self, parent=None,
                                   flags=Gtk.DialogFlags.MODAL, type=tipo,
                                   message_format=mensaje)

        # Modifico un poco el estilo para distinguirlo, porque al no tener
        # decoracion (borde + barra de titulo) queda medio "pelado"
        COLOR_FONDO = Gdk.color_parse('#d5d5d5')
        self.modify_bg(Gtk.StateFlags.NORMAL, COLOR_FONDO)
        pangoFont = FontDescription("{} 20".format(FONT_NAME))
        self.modify_font(pangoFont)
        self.set_border_width(50)

        self.connect('response', self._cerrar)
        self.set_decorated(False)


    def _cerrar(self, dialog, response, data=None):
        self.hide()
