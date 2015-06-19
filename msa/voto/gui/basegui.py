# -*- coding: utf-8 -*-
"""Modulo con algunas clases base para las interfaces graficas de gtk.
"""
import gtk

from msa.voto.constants import DEFAULT_FONT


class MsgDialog(gtk.MessageDialog):

    """Muestra un dialogo modal de error o de información."""

    ERROR = gtk.MESSAGE_ERROR
    INFO = gtk.MESSAGE_INFO
    QUESTION = gtk.MESSAGE_QUESTION
    WARNING = gtk.MESSAGE_WARNING

    CLOSE = gtk.BUTTONS_CLOSE
    OK_CANCEL = gtk.BUTTONS_OK_CANCEL
    OK = gtk.BUTTONS_OK
    NONE = gtk.BUTTONS_NONE

    def __init__(self, mensaje='Error', tipo=None, botones=None,
                 callback_ok=None, callback_cancel=None):
        """Constructor.

        Argumentos:
        mensaje -- El mensaje a mostrar. (default 'Error')
        tipo -- El tipo de mensaje
        botones -- Conjunto de botones a mostrar
        callback_ok, callback_cancel -- En caso de mostrar el conjunto de
            botones OK_CANCEL, estas funciones son llamadas
        """
        self._callbacks_ok = [callback_ok]
        self._callbacks_cancel = [callback_cancel]

        if tipo is None:
            tipo = self.ERROR
        if botones is None:
            botones = self.CLOSE

        gtk.MessageDialog.__init__(self, parent=None, flags=gtk.DIALOG_MODAL,
                                   type=tipo, buttons=botones,
                                   message_format=mensaje)

        # Modifico un poco el estilo para distinguirlo, porque al no tener
        # decoracion (borde + barra de titulo) queda medio "pelado"
        COLOR_FONDO = gtk.gdk.color_parse('#d5d5d5')
        self.modify_bg(gtk.STATE_NORMAL, COLOR_FONDO)
        self.set_border_width(30)
        self.vbox.set_spacing(80)

        self.connect('response', self._cerrar)
        self.set_decorated(False)
        # agrandar botones
        try:
            self.children = self.get_children()[0].get_children()[-1]\
                .get_children()
            label = self.get_children()[0].get_children()[0].get_children()[1]\
                .get_children()[1]
            label.modify_font(DEFAULT_FONT)
            for boton in self.children:
                boton.set_size_request(150, 75)
                label = boton.child.child.get_children()[1]
                label.modify_font(DEFAULT_FONT)
        except:
            pass

    def add_callback_ok(self, callback):
        self._callbacks_ok.append(callback)

    def add_callback_cancel(self, callback):
        self._callbacks_cancel.append(callback)

    def _cerrar(self, dialog, response, data=None):
        # Metodo que se llama al recibir cualquier señal del dialogo.
        if response == gtk.RESPONSE_OK:
            for callback in self._callbacks_ok:
                if callback is not None:
                    callback()
        elif response == gtk.RESPONSE_CANCEL:
            for callback in self._callbacks_cancel:
                if callback is not None:
                    callback()
        self.hide()
