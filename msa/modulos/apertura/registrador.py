"""
Clase para el manejo de la impresion de las actas de apertura.
"""
from base64 import b64encode

from msa.core.rfid.constants import TAG_APERTURA
from msa.modulos.constants import E_REGISTRANDO, E_INICIAL
from msa.modulos.apertura.constants import CANTIDAD_APERTURAS
from msa.settings import QUEMA


class RegistradorApertura():

    """Registrador para la Apertura."""

    def __init__(self, modulo):
        """
        Constructor del registrador de apertura.
        Argumentos:
            modulo -- una referencia al modulo al que pertenece.
        """
        self.modulo = modulo
        self.rampa = modulo.rampa
        self.logger = modulo.sesion.logger

        self.actas_impresas = 0

    def registrar(self, apertura):
        """Registra una (o más) apertura.

        Argumentos:
            apertura -- apertura que queremos imprimir.
        """
        self.logger.info("registrando")
        self.modulo.estado = E_REGISTRANDO
        self.rampa.remover_nuevo_papel()

        self._datos = apertura.a_tag()
        # El modulo Apertura tiene la particularidad de ser el unico modo que
        # levanta con un papel puesto, por lo tanto no estamos 100% seguros a
        # alto nivel de que efectivamente el papel esté puesto (podemos tener
        # falsos negativos), por lo tanto hacemos este shortcut para
        # preguntarlo explicitamente al backend.
        tiene_papel = self.rampa._servicio._estado_papel()

        if not tiene_papel or self.rampa.tag_leido is None:
            self.logger.error("No tengo papel")
            self._error()
        else:
            self._guardar_tag()

    def _error(self):
        """Maneja un error al intentar registrar un acta."""
        self.rampa.remover_boleta_expulsada()
        self.modulo.controlador.msg_error_apertura(self.rampa.tag_leido)
        self.rampa.expulsar_boleta()
        self.rampa.registrar_nuevo_papel(self._reintentar)

    def _reintentar(self, *args):
        """Reintenta imprimir un acta."""
        self.rampa.tiene_papel = True
        self.modulo.hide_dialogo()
        self.modulo.reimprimir()

    def _guardar_tag(self):
        """Guarda un tag de una apertura."""
        self.logger.debug("guardando_tag")
        self.rampa.guardar_tag_async(self._tag_guardado, TAG_APERTURA,
                                     self._datos, QUEMA)

    def _tag_guardado(self, exito):
        """Callback que se ejecuta luego de intentar guardar un tag.

        Argumentos:
            exito -- un booleano que indica si el tag se guardó exitosamente.
        """
        if not exito:
            self.logger.error("El tag NO se guardó correctamente.")
            # Por las dudas reseteamos el RFID
            self.rampa.reset_rfid()
            self._error()
        else:
            self.logger.info("El tag se guardó correctamente.")
            self._imprimir()

    def _imprimir(self):
        """Imprime una Apertura."""
        self.logger.info("Imprimiendo acta de Apertura.")
        self.rampa.registrar_boleta_expulsada(self._fin_impresion)
        self.rampa.registrar_error_impresion(self._error)
        self.modulo.rampa.imprimir_serializado("Apertura",
                                               b64encode(self._datos))

    def _fin_impresion(self, *args):
        """Callback que se llama una vez que se terminó de imprimir un acta."""
        self.logger.debug("Fin de la impresion del acta.")
        self.rampa.remover_boleta_expulsada()

        self.actas_impresas += 1
        if self.actas_impresas == CANTIDAD_APERTURAS:
            self.logger.debug("Saliendo.")
            self.modulo.callback_salir()
        else:
            self.logger.debug("Pidiendo otra acta.")
            self.modulo.estado = E_INICIAL
            self.modulo.callback_proxima_acta()
            self.rampa.registrar_nuevo_papel(self.modulo.reimprimir)

