"""Registrador del modulo sufragio.

Se encarga de manejar el almacenamiento e impresion de las BUE.
"""
from gi.repository.GObject import timeout_add


class Registrador(object):

    """La clase que maneja el registro en la boleta.
       Por "registrar" entendemos imprimir + guardar el chip.
    """

    def __init__(self, callback, modulo, callback_error):
        """Constructor del registrador de boletas."""
        self.callback = callback
        self.modulo = modulo
        self.callback_error = callback_error

        self._evento_ya_lanzado = False
        self.seleccion = None

    def _registrar_voto(self, solo_impimir=False):
        """La funcion que explicitamente manda a registrar el voto."""
        logger = self.modulo.sesion.logger
        logger.info("Registrando voto.")
        fallo = False
        impresora = self.modulo.sesion.impresora

        def fin_de_la_impresion(estado=None):
            """Callback que se llama cuando se terminó de imprimir una BUE."""
            logger.info("Terminó de imprimir.")
            if not self._evento_ya_lanzado:
                logger.info("Rehookeando eventos.")
                self._evento_ya_lanzado = True
                impresora.remover_insertando_papel()
                rampa = self.modulo.rampa
                rampa.tiene_papel = False
                impresora.registrar_insertando_papel(rampa.cambio_sensor_2)
                if not fallo:
                    logger.info("Llamando al callback post impresión.")
                    self.callback()
            return False

        self._evento_ya_lanzado = False
        # hookeo el evento, pero tambien agrego un timeout para asegurarme de
        # que si por alguna razón no salta el evento de fin de impresión sigue
        # su curso y asume que la sesion de impresión terminó. El manejo del
        # error de esto se hace mas abajo y es syncronico, a diferencia de
        # esto que es asincronico.
        if impresora is not None:
            impresora.remover_insertando_papel()
            impresora.registrar_insertando_papel(fin_de_la_impresion)
            timeout_add(10000, fin_de_la_impresion)

            logger.info("Enviando comando de impresion.")
            self.seleccion.serial = \
                bytes(self.modulo.rampa.datos_tag['serial'], "utf8")
            respuesta = impresora.registrar(self.seleccion, solo_impimir)
            logger.info("Fin del registro.")
            if respuesta['status'] == "TAG_NO_GUARDADO":
                logger.error("Recibido el mensaje de tag no guardado.")
                fallo = True
                self.callback_error()
        else:
            fallo = True
            self.callback_error()

    def _prepara_impresion(self, seleccion):
        """Guarda la seleccion en el objeto registrador."""
        self.seleccion = seleccion
