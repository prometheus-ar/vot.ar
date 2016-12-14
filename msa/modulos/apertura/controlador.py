"""Controlador del modulo apertura."""

from urllib.parse import quote
from gi.repository.GObject import timeout_add

from msa.core.settings import USAR_BUFFER_IMPRESION
from msa.modulos.apertura.constants import TEXTOS
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.base.actions import BaseActionController


class Actions(BaseActionController):
    """Actions del controlador de interaccion/"""

    def msg_confirmar_apertura(self, data):
        """Muestra el mensaje de confirmar la apertura."""
        self.async(self.controlador.msg_confirmar_apertura, data)


class Controlador(ControladorBase):

    """Controller para las pantallas de ingreso de datos."""

    def __init__(self, modulo):
        """
        Constructor del controlador de interaccion.
        Argumentos:
            modulo -- una referencia al modulo del que se está corriendo este
            controlador.

        """
        super(Controlador, self).__init__(modulo)
        self.set_actions(Actions(self))
        self.textos = TEXTOS

    def document_ready(self, data):
        """
        Callback que llama el browser en el document.ready().
        Argumentos:
            data -- datos que llegan desde la vista del browser via Zaguan.
        """
        self.send_constants()
        self._inicializa_pantalla()

    def _inicializa_pantalla(self):
        """Inicializa la pantalla de previsualizacion de la apertura."""
        if self.sesion._tmp_apertura is not None:
            imagen_acta = self.sesion._tmp_apertura.a_imagen(svg=True,
                                                             de_muestra=True)
            imagen_data = quote(imagen_acta.encode("utf-8"))
            self.set_pantalla_confirmacion(imagen_data)
        else:
            timeout_add(100, self.modulo.salir)

    def set_pantalla_confirmacion(self, imagen):
        """Carga la pantalla de confirmacion de apertura.
        Argumentos:
            imagen -- la imagen de previsualizacion de la apertura.
        """
        self.send_command("pantalla_confirmacion_apertura",
                          [_("acta_apertura_mesa"), imagen])

    def proxima_acta(self):
        """Muesta el boton para imprimir la siguiente acta."""
        self.send_command("pantalla_proxima_acta")

    def reimprimir(self):
        """Muesta el mensaje de imprimir y manda a imprimir otra Apertura."""
        self.send_command("confirmar_apertura")

    def _procesar_callback(self):
        """Procesa el callback."""
        self.sesion.impresora.remover_consultar_tarjeta()
        self.callback()

    def hide_dialogo(self):
        """Esconde el dialogo."""
        self.send_command("hide_dialogo")

    def mostrar_imprimiendo(self):
        """Muestra el mensaje de Imprimiendo."""
        self.send_command("imprimiendo")

    def msg_confirmar_apertura(self, respuesta):
        """Muestra el mensaje de confirmar la apertura."""
        self.modulo.play_sonido_tecla()
        if respuesta:
            self.modulo.confirmar_apertura()
        else:
            self.modulo.volver_atras()

    def msg_error_apertura(self, hay_tag=False):
        """
        Muestra el mensaje de error de la apertura.
        Argumentos:
            hay_tag -- booleano que expresa si hay un tag introducido.

        """
        if not hay_tag:
            callback_template = "msg_papel_no_puesto"
        else:
            callback_template = "msg_apertura_no_almacenada"
        self.send_command("pantalla_proxima_acta")
        self.cargar_dialogo(callback_template,
                            aceptar=None,
                            cancelar=self.modulo.salir)

    def reintenta_apertura(self, *args, **kwargs):
        """Reintenta la impresion de la apertura."""
        self.hide_dialogo()
        self.modulo.confirmar_apertura()

    def get_constants(self):
        """Genera las constantes propias de cada modulo."""

        constants_dict = {
            "USAR_BUFFER_IMPRESION": USAR_BUFFER_IMPRESION,
            "realizar_apertura": self.modulo.config("realizar_apertura"),
            "usa_login_desde_inicio":
                self.modulo.config("usa_login_desde_inicio"),
        }
        base_constants_dict = self.base_constants_dict()
        base_constants_dict.update(constants_dict)
        return base_constants_dict
