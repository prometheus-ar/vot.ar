# -*- coding: utf-8 -*-

import time

from json import dumps
from base64 import b64decode, b64encode


from msa import get_logger
from msa.core.settings import TOKEN
from msa.desktop.transmision.conexion import Conexion
from msa.desktop.transmision.helpers import estados_mesas_dict
from msa.desktop.transmision.helpers_dummy import (
    get_usuario, get_estado_mesas, guardar_recuento, get_categorias,
    generar_recuento, simular_delay_conexion, generar_acta_svg,
    generar_recuento_total)


logger = get_logger("trasmision-conexion")


class ConexionDummy(Conexion):

    UNKNOW_ERROR = 1
    SSL_ERROR = 2
    CONNECTION_ERROR = 3

    """ Esta Clase brinda un nivel de abstracción para el manejo del tráfico de
    red contra el servidor """
    def __init__(self, url, debug=True, timeout=None, desglosada=False):
        Conexion.__init__(self, url, debug, timeout)
        self._estados = {}
        self._acta_desglosada = desglosada

    def set_https_keys(self, key_file, cert_file):
        """ Configura las claves https """
        pass

    def set_ca_certificate(self, ca_file):
        """ Establece el certificado del CA para validar la conexión HTTPS
        desde el lado del cliente """
        pass

    def __get_https_opener(self):
        """ Devuelve una instancia del opener adecuado para interactuar vía
        https con client key y soporte de cookies """
        pass

    def __get_http_opener(self):
        """ Devuelve una instancia del opener adecuado para interactuar vía
        https con client key y soporte de cookies """
        pass

    def _enviar(self, funcion, **datos):
        """ Llama a la función del servidor pasada por parámetro,
            con los parámetros de la tupla de datos, siempre sobre la url del
            constructor de Conexion.
            En este caso simula las rutas del servidor llamando a las
            funciones locales correspondientes.
        """
        if funcion == 'echo':
            func = self._test_conexion
        elif funcion == 'datos':
            func = self._obtener_datos_servidor
        elif funcion == 'login':
            func = self._autenticar
        elif funcion == 'cargar_recuento':
            func = self._enviar_recuento
        elif funcion == 'confirmar_acta':
            func = self._confirmar_acta

        return func(**datos)

    def _enviar_recuento(self, datos_tag):
        """ Envía un recuento al servidor """
        respuesta = {}
        status = "ER"
        mensaje = ""
        datos_tag = b64decode(datos_tag)
        recuento = generar_recuento(datos_tag)
        if recuento is not None:
            codigo = guardar_recuento(self._estados, recuento.mesa.codigo,
                                      recuento.cod_categoria,
                                      recuento.mesa.cod_datos)
            respuesta['id_ubicacion'] = recuento.mesa.codigo
            mesa_str = "Mesa %s" % recuento.mesa.numero
            if codigo == 0:
                mensaje = "La %s no esta autorizada para su Usuario. Por " \
                          "favor consulte con Operaciones" % mesa_str
            elif codigo == 1:
                status = "OK"
                mensaje = "Recuento de la %s recibido y procesado " \
                          "correctamente.\nSe muestra el Parte " \
                          "Electr\u00f3nico BORRADOR.\nPara confirmarlo " \
                          "definitivamente, pase el Recuento por el lector " \
                          "nuevamente.\nSi ha ingresado el papel en la " \
                          "impresora, acerque su credencial al lector para " \
                          "expulsarlo." % mesa_str
                respuesta["acta_borrador"] = "SI"
                respuesta["img_acta"] = generar_acta_svg(
                    recuento,
                    categorias=get_categorias(recuento.mesa.cod_datos,
                                              self._acta_desglosada))
                # Revisar los otros parámetros: url, filename, alerta
                self._estados[recuento.mesa.codigo]['estado'] = 'En Proceso'
                self.__reset_estado_cargos(recuento.mesa.codigo)
            elif codigo == 2:
                status = "OK"
                mensaje = "Por favor, Confirme la \u00faltima acta en " \
                          "borrador de la %s.\n\u00bfes Definitiva?" % mesa_str
                respuesta["mesa"] = mesa_str
                respuesta["confirma_definitiva"] = "SI"
                respuesta["img_acta"] = generar_acta_svg(
                    recuento,
                    categorias=get_categorias(recuento.mesa.codigo,
                                              self._acta_desglosada))
            elif codigo == 3:
                status = "OK"
                categorias = get_categorias(recuento.mesa.cod_datos,
                                            self._acta_desglosada)
                desc_categoria = [c[1] for c in categorias if
                                  c[0] == recuento.cod_categoria]
                mensaje = "Recuento de la <i>%s</i> para el cargo <i>%s</i>" \
                          " recibido y procesado correctamente.\n" % \
                          desc_categoria[0]
                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['estado'] = 1
                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['recuento'] = recuento.a_tag()
                respuesta["cod_categoria"] = recuento.cod_categoria
            elif codigo == 4:
                status = "OK"
                mensaje = "Recuento de la %s recibido y procesado " \
                          "correctamente.\nSe muestra el Parte " \
                          "Electr\u00f3nico BORRADOR.\nPara confirmarlo " \
                          "definitivamente, pase el Recuento por el lector " \
                          "nuevamente.\nSi ha ingresado el papel en la " \
                          "impresora, acerque su credencial al lector para " \
                          "expulsarlo." % mesa_str
                respuesta["acta_borrador"] = "SI"

                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['estado'] = 1
                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['recuento'] = recuento.a_tag()

                actas = [c['recuento'] for c in
                         self._estados[recuento.mesa.codigo]['cargos'].values()]
                categorias = get_categorias(recuento.mesa.cod_datos,
                                            self._acta_desglosada)
                recuento_total = generar_recuento_total(actas)
                respuesta["img_acta"] = generar_acta_svg(
                    recuento_total, categorias=categorias,
                    acta_desglosada=self._acta_desglosada)
                respuesta["cod_categoria"] = recuento.cod_categoria

                self._estados[recuento.mesa.codigo]['estado'] = 'En Proceso'
                self.__reset_estado_cargos(recuento.mesa.codigo)
            elif codigo == 5:
                status = "OK"
                mensaje = "Por favor, Confirme la \u00faltima acta en " \
                          "borrador de la %s.\n\u00bfes Definitiva?" % mesa_str
                respuesta["mesa"] = mesa_str
                respuesta["confirma_definitiva"] = "SI"

                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['estado'] = 1
                self._estados[recuento.mesa.codigo]['cargos'] \
                    [recuento.cod_categoria]['recuento'] = recuento.a_tag()

                actas = [c['recuento'] for c in
                         self._estados[recuento.mesa.codigo]['cargos'].values()]
                categorias = get_categorias(recuento.mesa.cod_datos,
                                            self._acta_desglosada)
                recuento_total = generar_recuento_total(actas)
                respuesta["img_acta"] = generar_acta_svg(
                    recuento_total, categorias=categorias,
                    acta_desglosada=self._acta_desglosada)
                respuesta["cod_categoria"] = recuento.cod_categoria
            elif codigo == 6:
                mensaje = "El acta de la %s ya est\u00e1 confirmada y" \
                          " emitida." % mesa_str
        else:
            mensaje = "Recuento no válido."

        respuesta["status"] = status
        respuesta["mensaje"] = mensaje

        simular_delay_conexion()
        return dumps(respuesta)

    def _autenticar(self, usuario, clave):
        """ Autentica este cliente contra el servidor.
            El parámetro datos es el string de autenticación.
        """

        respuesta = {}
        user = get_usuario(usuario)

        status = "ER"
        if user is not None:
            if user.clave == clave:
                status = "OK"
                mensaje = "Bienvenido %s al sistema de transmisi\u00f3n.\n" \
                          "Ingrese los certificados de mesa a transmitir en" \
                          " la impresora." % user.nombre
                mesas = get_estado_mesas(user.ubicacion, self._acta_desglosada)

                # Genero un diccionario de estados para poder realizar luego
                # la validación
                _, self._estados = estados_mesas_dict(mesas)

                respuesta["estado_mesas"] = mesas
            else:
                mensaje = "La clave ingresada para el usuario %s es " \
                          "incorrecta" % user.nombre
        else:
            mensaje = 'Usuario no Autenticado'

        respuesta["status"] = status
        respuesta["mensaje"] = mensaje

        simular_delay_conexion()
        return dumps(respuesta)

    def _test_conexion(self):
        """ Conecta con el servidor, intercambia algo de tráfico de prueba y
        devuelve True en caso de éxito o False en caso contrario.
        respuesta_servidor {"status": "OK", "tags": ["MUM="]}

        """
        respuesta = {"status": "OK",
                     "tags": [b64encode(TOKEN)]}

        simular_delay_conexion()
        return dumps(respuesta)

    def diagnosticar(self):
        """ Conecta con el servidor, intercambia algo de tráfico de prueba y
            devuelve un diagnostico si fue fallida la prueba.
        """
        try:
            error = self.UNKNOW_ERROR
            # Me fijo que el error tiene una *antiguedad* de 1 seg.
            # No es la solución óptima, pero para esta caso es la más sencilla.
            if self._tmp_error[0] > time.time() - 1:
                e = self._tmp_error[1]
                if hasattr(e, 'reason'):
                    error = self.CONNECTION_ERROR
                return error
        except Exception, e:
            logger.debug('Funcion: diagnosticar, Error: %s' % e)
        return None

    def descargar(self, url_address, destino):
        """ Descarga un recurso del servidor y lo almacena en el destino local
            LEER: Esta funcion atualmente se utiliza para descargar la imagen
                  del acta desde el servidor, hago magia y levanto la imagen
                  generada en el paso confirmar acta y almacenada en tmp.
        """
        #filename = destino.split('/')[-1]
        #descargar_recuento(filename, destino)
        pass

    def _obtener_datos_servidor(self, db_version):
        """ Descarga los datos actalizados del servidor y lo almacena en el
            destino local
        """
        respuesta = {"status": "OK",
                     "archivo": "",
                     "version": db_version}

        simular_delay_conexion()
        return dumps(respuesta)

    def _confirmar_acta(self, datos_tag):
        """ Llama a la función del servidor para confirmar el acta """
        respuesta = {}
        status = "ER"
        datos_tag = b64decode(datos_tag)
        recuento = generar_recuento(datos_tag)
        if recuento is not None:
            codigo = guardar_recuento(self._estados, recuento.mesa.codigo,
                                      recuento.cod_categoria,
                                      recuento.mesa.cod_datos)
            mesa = recuento.mesa
            mesa_str = "Mesa %s" % mesa.numero
            # El acta fue ingresada previamente y está en espera de confirmar
            if codigo in (2, 5):
                status = "OK"
                mensaje = "Recuento de la %s recibido y " \
                          "procesado correctamente" % mesa_str
                respuesta["acta_definitiva"] = "SI"
                # Revisar los otros parámetros: url, filename, alerta
                self._estados[recuento.mesa.codigo]['estado'] = 'OK'
                respuesta['mesa'] = mesa_str
                respuesta['id_ubicacion'] = recuento.mesa.codigo
                if self._acta_desglosada:
                    respuesta["cod_categoria"] = recuento.cod_categoria
            elif codigo == 6:
                mensaje = "El acta de la %s ya est\u00e1 confirmada y" \
                          " emitida." % mesa_str
        else:
            mensaje = "Recuento no válido."

        respuesta["status"] = status
        respuesta["mensaje"] = mensaje

        simular_delay_conexion()
        return dumps(respuesta)

    def __reset_estado_cargos(self, id_ubicacion):
        for cargo in self._estados[id_ubicacion]['cargos'].keys():
            self._estados[id_ubicacion]['cargos'][cargo]['estado'] = 0
            self._estados[id_ubicacion]['cargos'][cargo]['recuento'] = ''
