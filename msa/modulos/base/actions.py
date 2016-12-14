"""Contiene la clase base para el manejo de las Actions de Zaguan."""
from zaguan.actions import BaseActionController as ZaguanAction
from zaguan.functions import asynchronous_gtk_message


class BaseActionController(ZaguanAction):

    def __init__(self, controlador):
        """Constructor."""
        ZaguanAction.__init__(self, controlador)
        self.controlador = controlador

    """Controlador de Acciones Basico para los modulos."""
    def log(self, data):
        """Loguea desde la UI."""
        self.controlador.sesion.logger.debug("LOG >>>%s" % data)

    def respuesta_dialogo(self, data):
        self.controlador.procesar_dialogo(data)

    def document_ready(self, data):
        self.controlador.document_ready(data)
        # usado para el testing framework
        if hasattr(self.controlador, "_after_ready"):
            self.async(self.controlador._after_ready)

    def volver(self, data):
        """Pasamanos para el boton volver."""
        self.controlador.modulo.volver()

    def salir(self, data):
        """Lllama al metodo salir."""
        self.controlador.modulo.salir()

    def administrador(self, data):
        """Lllama a la salida al administrador."""
        self.controlador.modulo.administrador()

    def async(self, func, params=None):
        async_func = asynchronous_gtk_message(func)
        if params is not None:
            async_func(params)
        else:
            async_func()

    def sonido_tecla(self, data):
        self.controlador.modulo.play_sonido_tecla()

    def sonido_error(self, data):
        self.controlador.modulo.play_sonido_error()

    def sonido_warning(self, data):
        self.controlador.modulo.play_sonido_warning()

    def sonido_ok(self, data):
        self.controlador.modulo.play_sonido_ok()
