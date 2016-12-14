# -*- coding: utf-8 -*-
"""
Clase para el manejo de la impresion de las actas de apertura.
"""

from base64 import b64encode
from time import sleep

from gi.repository.GObject import timeout_add, idle_add

from msa.core.rfid.constants import TAG_APERTURA
from msa.modulos.constants import E_REGISTRANDO, E_INICIAL
from msa.modulos.apertura.constants import CANTIDAD_APERTURAS
from msa.settings import QUEMA


class RegistradorApertura():

    """Registrador para la Apertura."""

    def __init__(self, modulo, callback_salir, callback_proxima_acta):
        """
        Constructor del registrador de apertura.
        Argumentos:
            modulo -- una referencia al modulo al que pertenece.
        """
        self.modulo = modulo
        self.sesion = self.modulo.sesion
        self.actas_impresas = 0
        self.callback_salir = callback_salir
        self.callback_proxima_acta = callback_proxima_acta

    def registrar(self, *args):
        """Funcion de entrada para registrar el acta de apertura."""
        logger = self.sesion.logger
        logger.info("registrando")
        rampa = self.modulo.rampa
        rampa.remover_nuevo_papel()

        def _fin_impresion(printer_status=None):
            """Maneja el fin de la impresion.

            Desregistra los eventos. Si todas las actas que tenian que ser
            impresas salen impresas sale del modulo, sino registra el evento de
            espera de papel.
            """
            logger.debug("FIN IMPRESION")
            rampa.remover_boleta_expulsada()
            rampa.remover_nuevo_papel()
            self.actas_impresas += 1
            logger.info("Fin de la impresion del acta.")
            if self.actas_impresas == CANTIDAD_APERTURAS:
                logger.info("Saliendo.")
                del self.sesion._tmp_apertura
                self.callback_salir()
            else:
                logger.info("Pidiendo otra.")
                self.modulo.estado = E_INICIAL
                self.callback_proxima_acta()
                rampa.registrar_nuevo_papel(self.modulo.reimprimir)

        logger.info("Empezando a registrar acta de Apertura.")
        self.modulo.estado = E_REGISTRANDO

        if self._guardar_e_imprimir():
            # hookeo el evento de fin de impresion para salir del modulo
            logger.info("Hookeando evento de fin de impresion.")
            rampa.registrar_boleta_expulsada(_fin_impresion)
        else:
            logger.error("Lanzando mensaje de error a la UI.")
            self.modulo.controlador.msg_error_apertura(rampa.datos_tag)
            rampa.expulsar_boleta()
            def _fin_expulsion():
                rampa.remover_boleta_expulsada()
                def _hide_and_try(status):
                    rampa.remover_nuevo_papel()
                    self.modulo.hide_dialogo()
                    self.modulo.controlador.mostrar_imprimiendo()
                    timeout_add(100, self.registrar)
                rampa.registrar_nuevo_papel(_hide_and_try)
            rampa.remover_nuevo_papel()
            rampa.registrar_boleta_expulsada(_fin_expulsion)

    def _guardar_e_imprimir(self):
        """Se encarga primero de guardar los datos y corroborar que esté todo
           ok. Si es así imprime y devuelve True si está todo bien o False
           en cualquier caso contrario.
        """
        exito = False
        logger = self.sesion.logger
        tag = self.modulo.rampa.datos_tag

        if tag is None:
            sleep(1)
            tag = self.sesion.lector.get_tag()
            self.modulo.rampa.datos_tag = tag

        if not tag or not self.sesion.impresora:
            logger.error("No tengo un tag insertado para guardar la apertura.")
        else:
            # Chequeo que el tag esté vacío
            datos_tag = tag['datos']
            if datos_tag != b'':
                logger.error("El tag tiene datos.")
            else:
                # Todo ok, guardo el acta de apertura, si devuelve True imprimo
                if self._guardar_apertura():
                    logger.info("El tag se guardó correctamente.")
                    self.sesion.apertura = self.sesion._tmp_apertura
                    exito = True
                    self._imprimir_acta()
                else:
                    logger.error("Ocurrió un error al guardar la Apertura.")
        return exito

    def _guardar_apertura(self):
        """ Guarda los datos en el tag, lo vuelve a leer y compara los dos
            strings para verificar la correcta escritura.
            Devuelve True si el guardado y la comprobación están correctos,
            False en caso contrario.
        """
        self.sesion.logger.info("Guardando el tag de Apertura.")
        datos = self.sesion._tmp_apertura.a_tag()
        guardado_ok = self.sesion.lector.guardar_tag(TAG_APERTURA, datos,
                                                     QUEMA)
        return guardado_ok

    def _imprimir_acta(self):
        """Efectivamente manda a imprimir el acta."""
        def _imprimir():
            self.sesion.logger.info("Imprimiendo acta de Apertura.")
            tipo_tag = self.sesion._tmp_apertura.__class__.__name__
            tag = self.sesion._tmp_apertura.a_tag()
            self.sesion.impresora.imprimir_serializado(tipo_tag,
                                                       b64encode(tag))
        timeout_add(100, _imprimir)
