"""Contiene el controlador base para la interaccion con la web view."""
from zaguan import WebContainerController

from msa.core.data.helpers import get_config
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.modulos import get_sesion
from msa.modulos.constants import (EXT_IMG_VOTO, PATH_FOTOS_ORIGINALES,
                                   PATH_TEMPLATES_MODULOS,
                                   PATH_TEMPLATES_FLAVORS)
from msa.modulos.gui.settings import MOSTRAR_CURSOR


class ControladorBase(WebContainerController):
    """
        Controlador base para los controladores de todos los modulos.
    """
    def __init__(self, modulo):
        WebContainerController.__init__(self)
        self.modulo = modulo
        self.sesion = get_sesion()

        self._callback_aceptar = None
        self._callback_cancelar = None
        self.textos = None

    def cargar_dialogo(self, callback_template, aceptar=None, cancelar=None):
        self._callback_aceptar = aceptar
        self._callback_cancelar = cancelar
        self.send_command("cargar_dialogo", callback_template)

    def procesar_dialogo(self, respuesta_afirmativa):
        """Procesa el dialogo."""
        self.modulo.play_sonido_tecla()
        callback_dialogo = None
        if respuesta_afirmativa:
            if self._callback_aceptar is not None:
                callback_dialogo = self._callback_aceptar
        else:
            if self._callback_cancelar is not None:
                callback_dialogo = self._callback_cancelar

        self._callback_aceptar = None
        self._callback_cancelar = None

        if callback_dialogo is not None:
            callback_dialogo()

    def set_actions(self, action):
        self.add_processor("voto", action)

    def do_click(self, selector):
        self.send_function('$("{}").click()'.format(selector))

    def do_set_value(self, selector, value):
        self.send_function('$("{}").val("{}")'.format(selector, value))

    def hide_dialogo(self):
        """Oculta el dialogo."""
        self.send_command("hide_dialogo")

    def get_encabezado(self):
        return get_config("datos_eleccion")

    def base_constants_dict(self):
        flavor = self.modulo.config("flavor")
        encabezado = self.get_encabezado()
        constants_dict = {
            "encabezado": {texto: encabezado[texto] for texto in encabezado},
            "ext_img_voto": EXT_IMG_VOTO,
            "flavor": flavor,
            "juego_de_datos": JUEGO_DE_DATOS,
            "mostrar_cursor": MOSTRAR_CURSOR,
            "PATH_TEMPLATES_MODULOS": "file:///%s/" % PATH_TEMPLATES_MODULOS,
            "PATH_TEMPLATES_FLAVORS": "file:///%s/" % PATH_TEMPLATES_FLAVORS,
            "path_imagenes_candidaturas": "file:///%s/" % PATH_FOTOS_ORIGINALES,
        }
        if self.textos is not None:
            constants_dict["i18n"] = {trans: _(trans) for trans in self.textos}

        return constants_dict

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = self.get_constants()
        self.send_command("set_constants", constants_dict)

    def get_constants(self):
        constants_dict = self.base_constants_dict()
        return constants_dict
