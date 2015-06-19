# -*- coding: utf-8 -*-
from zaguan import WebContainerController
from zaguan.actions import BaseActionController
from zaguan.functions import asynchronous_gtk_message

from msa.core import get_config
from msa.core.clases import Seleccion
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.voto.sesion import get_sesion
from msa.voto.settings import MOSTRAR_CURSOR, EFECTOS_INICIO, \
    PATH_TEMPLATES_VOTO


class Actions(BaseActionController):
    pass


class ControllerInicio(WebContainerController):

    """Controller para la interfaz web de voto."""

    def __init__(self, parent):
        super(ControllerInicio, self).__init__()
        self.sesion = get_sesion()
        self.parent = parent
        self.interna = None
        self.add_processor("inicio", Actions(self))

        self.callback_aceptar = None
        self.callback_cancelar = None

    def document_ready(self, data):
        self.parent._inicio()
        self.parent._pantalla_principal()

    def calibrar(self, data):
        asynchronous_gtk_message(self.parent.calibrar_pantalla)()

    def apagar(self, data):
        self.parent._btn_apagar_clicked()

    def dialogo(self, data):
        self.procesar_dialogo(data)

    def reiniciar_seleccion(self):
        """Resetea la seleccion. Elimina lo que el usuario eligió."""
        self.parent.seleccion = Seleccion(self.sesion.mesa)

    def procesar_dialogo(self, respuesta):
        if respuesta:
            if self.callback_aceptar is not None:
                self.callback_aceptar()
        else:
            if self.callback_cancelar is not None:
                self.callback_cancelar()

    def show_dialogo(self, mensaje, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=False,
                     btn_aceptar=False):
        self.callback_aceptar = callback_aceptar
        self.callback_cancelar = callback_cancelar
        dialogo = {"mensaje": mensaje,
                   "btn_aceptar": btn_aceptar,
                   "btn_cancelar": btn_cancelar}
        self.send_command("show_dialogo", dialogo)

    def hide_dialogo(self):
        self.send_command("hide_dialogo")

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants()
        self.send_command("set_constants", constants_dict)


def get_constants():
    translations = ("calibrar", "apagar", "cancelar_apagado",
                    "bienvenido", "presente_credencial_acta")
    encabezado = get_config('datos_eleccion')

    constants_dict = {
        "juego_de_datos": JUEGO_DE_DATOS,
        "mostrar_cursor": MOSTRAR_CURSOR,
        "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
        "i18n": [(trans, _(trans)) for trans in translations],
        "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO,
        "effects": EFECTOS_INICIO}
    return constants_dict
