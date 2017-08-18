"""Registrador del modulo sufragio.

Se encarga de manejar el almacenamiento e impresion de las BUE.
"""
from datetime import datetime

from gi.repository.GObject import timeout_add, source_remove



class Registrador(object):

    """La clase que maneja el registro en la boleta.
       Por "registrar" entendemos imprimir + guardar el chip.
    """

    def __init__(self, callback, modulo, callback_error):
        """Constructor del registrador de boletas."""
        self.callback = callback
        self.modulo = modulo
        self.callback_error = callback_error
        self.logger = self.modulo.sesion.logger

        # vamos a lanzar el evento de fin de impresion una sola vez.
        self._evento_ya_lanzado = False
        self.seleccion = None
        self._timeout_error = None

        self._start = None

    def _evaluar_grabacion_tag(self, tag_guardado):
        """Evalua el exito al fin de la grabación del tag.

        Argumentos:
            tag_guardado -- un booleano que indica si el tag fue
                guardado o no
        """
        self.logger.info("Fin del registro.")
        now = datetime.now()
        tiempo = now - self._start
        self._start = now
        self.logger.debug("Tiempo de grabación del tag %s", tiempo)
        if not tag_guardado:
            self.logger.error("Recibido el mensaje de tag no guardado.")
            self.callback_error()
        else:
            # Despues de que se graba el tag tenemos n segundos para recibir
            # el evento de fin de impresion si no es así tiramos un error
            if self._timeout_error is not None:
                self.logger.warning("Eliminando timeout anterior")
                source_remove(self._timeout_error)
            self._timeout_error = timeout_add(25000, self._error_impresion)

    def _error_impresion(self):
        """Callback que se llama cuando no se imprimió la boleta."""
        if self._timeout_error is not None:
            source_remove(self._timeout_error)
            self._timeout_error = None
        self.callback_error(cambiar_estado=False)

    def _fin_de_la_impresion(self, estado=None):
        """Callback que se llama cuando se terminó de imprimir una BUE."""
        self.logger.info("Terminó de imprimir.")
        now = datetime.now()
        tiempo = now - self._start
        self.logger.debug("Tiempo de impresión de la boleta %s", tiempo)
        if self._timeout_error is not None:
            source_remove(self._timeout_error)
            self._timeout_error = None
        self._evento_ya_lanzado = True
        self.modulo.rampa.tiene_papel = False
        self.modulo.rampa.tag_leido = None
        self.modulo.rampa.registrar_default_sensor_1()
        self.logger.info("Llamando al callback post impresión.")
        self.callback()

    def registrar_voto(self, solo_impimir=False):
        """La funcion que explicitamente manda a registrar el voto."""
        self.logger.info("Registrando voto.")
        rampa = self.modulo.rampa
        self._start = datetime.now()

        self._evento_ya_lanzado = False
        if rampa.tiene_conexion:
            rampa.registrar_fin_impresion(self._fin_de_la_impresion)

            self.logger.info("Enviando comando de impresion.")
            # traemos la key de encriptación del voto.
            aes_key = self.modulo.sesion.mesa.get_aes_key()
            # Guardamos el tag e imprimimos la boleta.
            rampa.registrar_error_impresion(self._error_impresion)
            rampa.registrar_voto(self.seleccion, solo_impimir, aes_key,
                                 self._evaluar_grabacion_tag)
        else:
            self.callback_error()

    def _prepara_impresion(self, seleccion):
        """Guarda la seleccion en el objeto registrador."""
        self.seleccion = seleccion
