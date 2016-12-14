"""Registrador del modulo escrutinio.

Orquesta el orden y maneja la impresion de actas y certificados.
"""
from base64 import b64encode
from json import dumps

from dbus.exceptions import DBusException

from gi.repository.GObject import timeout_add
from msa.core.data.candidaturas import Categoria
from msa.core.documentos.constants import (CIERRE_CERTIFICADO,
                                           CIERRE_COPIA_FIEL,
                                           CIERRE_ESCRUTINIO, CIERRE_RECUENTO,
                                           CIERRE_TRANSMISION)
from msa.core.rfid.constants import TAG_RECUENTO
from msa.modulos import get_sesion
from msa.settings import QUEMA


class RegistradorCierre(object):

    """Registrador para la Apertura."""

    def __init__(self, callback_generando=None, callback_error_registro=None,
                 callback_imprimiendo=None):
        """Constructor del registrador del cierre."""
        self.callback_generando = callback_generando
        self.callback_error_registro = callback_error_registro
        self.callback_imprimiendo = callback_imprimiendo

        self.actas_con_chip = (CIERRE_RECUENTO, CIERRE_TRANSMISION)
        self.actas_sin_chip = (CIERRE_ESCRUTINIO, CIERRE_COPIA_FIEL,
                               CIERRE_CERTIFICADO)
        self.sesion = get_sesion()

    def _guardar_tag(self, tag, categoria=None):
        """ Guarda los datos en el tag, lo vuelve a leer y compara los dos
            strings para verificar la correcta escritura.
            Devuelve True si el guardado y la comprobación están correctos,
            False en caso contrario.
        """
        guardado_ok = False
        datos = self.sesion.recuento.a_tag(categoria)

        def _intento(datos):
            """Un intento de grabacion."""
            return self.sesion.lector.guardar_tag(TAG_RECUENTO, datos, QUEMA)

        # Solo guardo el tag si no tiene datos.
        if tag['datos'] == b'':
            guardado_ok = _intento(datos)
            # ni no lo puede grabar trato de nuevo depues de resetear el
            # lector.
            if not guardado_ok:
                self.sesion.lector.reset()
                guardado_ok = _intento(datos)

        return guardado_ok

    def registrar_acta(self, tipo_acta):
        """ Función que se encarga primero de guardar los datos y corroborar
        que esté todo ok. Si es así imprime y devuelve True o False en
        cualquier caso contrario
        """
        registrada = False
        tag = self.sesion.lector.get_tag()
        if tipo_acta[0] in self.actas_con_chip:
            # Si el acta tiene chip se guarda en el mismo y se imprime
            registrada = self._registrar_acta_con_chip(tag, tipo_acta)
        else:
            # Si no tiene chip solo se imprime
            registrada = self._registrar_acta_sin_chip(tag, tipo_acta)
        return registrada

    def _registrar_acta_con_chip(self, tag, tipo_acta):
        """Registra el acta en caso de ser 'con chip' (no es un certificado)."""
        registrada = False
        acta, cod_categoria = tipo_acta
        # Tiene que si o si tener tag.
        if tag is not None:
            registrada = self._guardar_tag(tag, cod_categoria)
            # si se guardó el chip se imprime. Sino no.
            if registrada:
                self._imprimir_acta(tipo_acta)

        return registrada

    def _registrar_acta_sin_chip(self, tag, tipo_acta):
        """Registra los certificados."""
        registrada = False
        acta, cod_categoria = tipo_acta
        # si tiene tag no imprime.
        if tag is None:
            self._imprimir_acta(tipo_acta)
            registrada = True

        return registrada

    def _get_extra_data(self, tipo_acta):
        """Genera la data extra para mandarle al servicio de impresion."""
        if self.sesion.recuento.autoridades:
            autoridades = [aut.a_dict() for aut in
                           self.sesion.recuento.autoridades]
        else:
            autoridades = None

        extra_data = {
            "tipo_acta": tipo_acta,
            "autoridades": autoridades,
            "hora": self.sesion.recuento.hora
        }
        return dumps(extra_data)

    def _imprimir_acta(self, tipo_acta):
        """Imprime las actas."""
        def _imprimir():
            encoded_data = b64encode(self.sesion.recuento.a_tag(tipo_acta[1]))
            extra_data = self._get_extra_data(tipo_acta)
            try:
                self.sesion.impresora.imprimir_serializado(
                    "Recuento", encoded_data, extra_data=extra_data)
            except DBusException:
                # ignorando posible timeout de dbus para carga de buffer
                # el zen de python me pide que lo haga explicito :D
                pass
        timeout_add(100, _imprimir)


class SecuenciaActas(object):

    """Clase que maneja la secuencia de impresion de actas."""

    _imprimiendo = False

    def __init__(self, modulo, callback_espera, callback_error_registro,
                 callback_imprimiendo, callback_fin_secuencia,
                 callback_post_fin_secuencia=None):
        """Constructor la clase de la secuencia de impresion de actas."""
        self.modulo = modulo
        # Se llama cuando se esta esperando el ingreso de papel.
        self.callback_espera = callback_espera
        # Se llama cuando hay un error de registro.
        self.callback_error_registro = callback_error_registro
        # se llama cuando se está por imprimir
        self.callback_imprimiendo = callback_imprimiendo
        # se llama cuando termina la secuencia de impresion de actas
        self.callback_fin_secuencia = callback_fin_secuencia
        self.callback_post_fin_secuencia = callback_post_fin_secuencia

        self.orden_actas = self.modulo.orden_actas

        self.logger = modulo.sesion.logger
        self.sesion = modulo.sesion
        self.actas_a_imprimir = self._crear_lista_actas()
        self.registrador = RegistradorCierre()
        self.acta_actual = None
        self._finalizado = False
        self.rampa = self.modulo.rampa
        self.logger.info("Creado objeto de secuencia de actas")

    def _crear_lista_actas(self):
        """Crea la lista de la secuencia de impresion de actas."""
        actas = []
        categorias = Categoria.many(sorted="posicion")
        grupos = sorted(list(set([cat.id_grupo for cat in categorias])))

        for tipo_acta in self.orden_actas:
            for grupo in grupos:
                datos_grupo = [tipo_acta, grupo]
                actas.append(datos_grupo)
        self.logger.info("Creanda lista de actas. %s actas a imprimir",
                         len(actas))
        return actas

    def ejecutar(self):
        """Ejecuta la secuencia de impresion de actas."""
        self.logger.info("Ejecutando secuencia de impresion")
        try:
            self.sesion.impresora.remover_boleta_expulsada()
            self.acta_actual = self.actas_a_imprimir.pop(0)
            self._pedir_acta()
        except IndexError:
            # cuando terminamos de imprimir todas las actas cambiamos los
            # callbacks para la impresion extra de actas para fiscales.
            self._finalizado = True
            self.acta_actual[0] = CIERRE_CERTIFICADO

            self.acta_actual[1] = self.acta_actual[1] + 1
            grupos = list(set([cat.id_grupo for cat in Categoria.all()]))
            if self.acta_actual[1] > len(grupos):
                self.acta_actual[1] = 1

            self.acta_actual[1] = self.acta_actual[1]

            if self.callback_fin_secuencia is not None:
                self.callback_fin_secuencia()
                self.callback_fin_secuencia = self.callback_post_fin_secuencia
            self.callback_espera = None

    def _pedir_acta(self):
        """Pedimos el ingreso del acta."""
        self.logger.info("Pidiendo acta: %s", self.acta_actual[0])
        self.callback_espera(self.acta_actual)
        self.sesion.impresora.remover_insertando_papel()
        self.sesion.impresora.remover_consultar_tarjeta()
        self.rampa.registrar_nuevo_papel(self._imprimir_acta)

    def _fin_impresion(self):
        """Se llama cuando termina de imprimir."""
        self.logger.info("Fin de la impresion")
        self._imprimiendo = False
        self.ejecutar()

    def _imprimir_acta(self, data_sensores):
        """Manda a imprimir el acta."""
        if not self._imprimiendo:
            self._imprimiendo = True
            self.sesion.impresora.remover_insertando_papel()
            self.sesion.impresora.remover_consultar_tarjeta()

            self.logger.info("Imprimiendo acta")
            if self.callback_imprimiendo is not None:
                self.logger.info("callback_imprimiendo")
                self.callback_imprimiendo(self.acta_actual, self._finalizado)
            # tiramos este timeout por que sino no actualiza el panel de estado
            timeout_add(200, self._impresion_real)
        else:
            self.logger.warning("Frenado intento de impresion concurrente")

    def _impresion_real(self):
        """Efectivamente manda a imprimir el acta."""
        self.logger.info("Por registrar acta")
        registrado = self.registrador.registrar_acta(self.acta_actual)
        if registrado:
            self.logger.info("Acta registrada")
            # una vez que termine de imprimir ejecutamos la secuencia para
            # que levante el proximo elemento.
            self.sesion.impresora.registrar_boleta_expulsada(
                self._fin_impresion)
        else:
            self.logger.info("Acta NO registrada")
            self.callback_error_registro(self.acta_actual, self._finalizado)
            self._imprimiendo = False
