#!/usr/bin/env python
# -*- coding:utf-8 -*-

import thread
import gobject

from base64 import b64decode
from datetime import datetime
from ojota import set_data_source
from subprocess import Popen, PIPE

from msa import get_logger
from msa.constants import ESTADO_OK, ESTADO_ESPERA, ESTADO_PRIMERA_CARGA
from msa.core.data import Configuracion as ConfiguracionSistema
from msa.core.rfid.constants import TAG_RECUENTO, CLASE_ICODE2, \
    TAG_USUARIO_MSA, TAG_PRESIDENTE_MESA, CLASE_MIFARE, TAG_NO_ENTRA, \
    TAG_INICIO, TAG_ADDENDUM
#from msa.desktop.transmision.conexion_dummy import ConexionDummy as Conexion
from msa.desktop.transmision.conexion import Conexion
from msa.desktop.transmision.config import Configuracion
from msa.desktop.transmision.constants import (
    MSG_CONECTADO, MSG_CONECTANDO, MSG_LECTOR_DESCONECTADO,
    MSG_CONECTANDO_ESPERE, MSG_AHORA_PASE_TARJETA, MSG_COMPRUEBE_CONEXION,
    MSG_VERIFIQUE_CERTIFICADOS, MSG_INTENTE_NUEVAMENTE, MSG_CHIP_NO_AUTORIZADO,
    MSG_CHIP_DE_VACIO, MSG_CHIP_VACIO, MSG_AUTENTICANDO_USUARIO,
    MSG_CONTENIDO_CHIP, MSG_ENVIANDO_DATOS, MSG_CHIP_NO_TIPO_RECUENTO,
    MSG_CHIP_NO_ICODE2, MSG_CHIP_NO_RECUENTO, MSG_ERROR_COMUNICACION,
    MSG_TARJETA_INVALIDA, MSG_ERROR_BOLD, MSG_BOLD, MSG_ERROR_GENERICO,
    MSG_ERROR_LEER_CHIP, MSG_INICIO, MSG_RESTO_ACTAS, ST_CONECTADO,
    ST_DESCONECTADO, ST_NO_LECTOR, MSG_ST_CONEXION, MSG_ST_LECTOR,
    MSG_ST_IMPRESORA, MSG_ST_ULTIMA_CONEXION, MSG_CHIP_NO_ENTRA)
from msa.desktop.transmision.helpers import (
    bloqueante, desbloqueante, mostrar_espera, actualizar_datos,
    estados_mesas_dict, status_for_url)
from msa.desktop.transmision.modulos import ModuloLector, NO_TAG, TAG_ERROR, \
    TAG_VACIO, TAG_DATOS, TAG_ADMIN
from msa.desktop.transmision.settings import PING_EVERY, PROTOCOLO, DEBUG, \
    PROTOCOLO_CERTS, URL_LOGIN_CERTS
from msa.helpers import levantar_locales


levantar_locales()


class TransmisionCore(object):
    # Constantes de Estados
    DESCONECTADO = 0
    CONECTADO = 1
    AUTENTICADO = 2

    MARGEN_LECTURAS_CON_COLISION = 2
    MARGEN_LECTURAS_ERRONEAS = 2

    COLOR_OK = '#006600'
    COLOR_ERR = '#FF0000'
    COLOR_ALERTA = '#FF0000'

    def __init__(self, modo_local=False, hw_init=True):
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("EHLO")

        self.config = Configuracion()
        if self.config.USAR_LOCK == 'true':
            self.lock = thread.allocate_lock()
        else:
            self.lock = None
        self.logger.debug("__init__: lock = " + str(self.lock))
        self.__set_estado_conexion(self.DESCONECTADO)
        self.__modulo_lector = ModuloLector(self._evento_tag, False)

        self._conexion = None
        self._timeout_id = None
        self._recuento_anterior = None

        self.inicializar_variables()

    def inicializar_variables(self):
        self.valid_tags = None
        self._actas = {}
        self._estados_mesas = {}
        self._acta_desglosada = False

    @bloqueante
    def conectar(self):
        if self.__estado_conexion != self.DESCONECTADO:
            self.cb_actualizacion_informacion(MSG_CONECTADO)
            self.cb_actualizar_opciones([('conectar', False),
                                        ('desconectar', True),
                                        ('diagnostico', True)])
            self.cb_actualizacion_estado([("conexion", MSG_ST_CONEXION %
                                           ST_CONECTADO),
                                          ("ultima_conexion",
                                           MSG_ST_ULTIMA_CONEXION %
                                           self._ultima_conexion)])
        elif self._conexion is not None:
            self.cb_actualizacion_informacion(MSG_CONECTANDO)
        elif self.__modulo_lector is None:
            self.cb_actualizacion_informacion(MSG_LECTOR_DESCONECTADO)
            self.cb_actualizacion_estado([("lector", MSG_ST_LECTOR %
                                           ST_NO_LECTOR)])
        else:
            self.cb_actualizacion_informacion(MSG_CONECTANDO_ESPERE)
            self._conexion = Conexion(
                '%s://%s/' % (PROTOCOLO, self.config.HOST),
                DEBUG, self.config.TIMEOUT)
            self._conexion.set_https_keys(self.config.KEY_FILE,
                                          self.config.CERT_FILE)
            self._conexion.set_ca_certificate(self.config.CA_FILE)
            thread.start_new_thread(self.__conectar, ())
            self.__conectar_lector()
            return

        if self.lock:
            self.logger.debug("_conectar: libero lock manual!")
            self.lock.release()

    @desbloqueante
    def __conectar_lector(self):
        self.__modulo_lector.conectar_lector()
        return

    #@mostrar_espera
    @desbloqueante
    def __conectar(self):
        """
        Conectar al servidor web usando un thread en segundo plano
        """
        self.logger.info("llamando a conectar")
        result = self._conexion.test_conexion()
        if result is not False and result.status_ok():
            self._ultima_conexion = datetime.now().strftime('%H:%M:%S')
            # if self.config.VALIDAR_DATOS:
            #     self._validar_datos()
            self.valid_tags = [b64decode(tag).upper() for tag
                               in result._dict['tags']]

            self.__set_estado_conexion(self.CONECTADO)
            self.cb_actualizar_opciones([('conectar', False),
                                        ('desconectar', True),
                                        ('diagnostico', True)])
            self.cb_actualizacion_estado([("conexion", MSG_ST_CONEXION %
                                           ST_CONECTADO),
                                          ("ultima_conexion",
                                           MSG_ST_ULTIMA_CONEXION %
                                           self._ultima_conexion)])
            self.cb_actualizacion_informacion(MSG_AHORA_PASE_TARJETA,
                                              idle=True, color=self.COLOR_OK)
            self.logger.debug("Configurando envío de ECHO al servidor.")
            gobject.idle_add(self.__run_echo_loop)

        else:
            error = self._conexion.diagnosticar()
            if error is self._conexion.UNKNOW_ERROR:
                ayuda = ""
            elif error is self._conexion.CONNECTION_ERROR:
                ayuda = MSG_COMPRUEBE_CONEXION
            elif error is self._conexion.SSL_ERROR:
                ayuda = MSG_VERIFIQUE_CERTIFICADOS
            else:
                ayuda = ""

            self._conexion = None
            self.cb_actualizacion_informacion(MSG_INTENTE_NUEVAMENTE % ayuda,
                                              idle=True, color=self.COLOR_ERR)
            self.cb_actualizar_opciones([('conectar', True),
                                        ('desconectar', False),
                                        ('diagnostico', False)])
            self.cb_actualizacion_estado([("conexion", MSG_ST_CONEXION %
                                           ST_DESCONECTADO),
                                          ("ultima_conexion", '')])

    def __run_echo_loop(self):
        """
        Setea el loop dentro del cual se envia un ECHO al servidor.
        """
        if self._timeout_id is not None:
            gobject.source_remove(self._timeout_id)
        self._timeout_id = gobject.timeout_add_seconds(
            PING_EVERY,
            self.__echo)
        return False

    def __echo(self):
        self._ultima_conexion = datetime.now().strftime('%H:%M:%S')
        result = self._conexion.test_conexion()
        if result.status_ok():
            self.cb_actualizacion_estado([("conexion", MSG_ST_CONEXION %
                                           ST_CONECTADO),
                                          ("ultima_conexion",
                                           MSG_ST_ULTIMA_CONEXION %
                                           self._ultima_conexion)])
        else:
            self.logger.debug('Se perdió la conexión')
            self.cb_perdida_conexion()
            self.desconectar_red()
        return True

    def desconectar(self):
        self.logger.info("Desconectando")
        self.desconectar_red()
        self.desconectar_hw()

    def desconectar_red(self):
        """
        Borra la conexión, cambia el estado a desconectado y además limpia el
        loop de echo
        """
        self.logger.debug("Limpiando la conexión al servidor")
        self._conexion = None
        self.inicializar_variables()

        self.__set_estado_conexion(self.DESCONECTADO)
        self.cb_actualizar_opciones([('conectar', True),
                                    ('desconectar', False),
                                    ('diagnostico', False)])
        self.cb_actualizacion_estado([("conexion", MSG_ST_CONEXION %
                                       ST_DESCONECTADO),
                                      ("ultima_conexion", '')])
        self.cb_actualizacion_informacion(MSG_INICIO)

        if self._timeout_id is not None:
            gobject.source_remove(self._timeout_id)

    def desconectar_hw(self):
        """
        Desconecta el hardware del lector
        """
        self.logger.debug("Desconectando el hw del lector")
        self.__modulo_lector.desconectar_lector()

    def descargar_certificados(self, usuario, password):
        pass

    def preferencias(self):
        pass

    def preferencias(self, preferencias):
        pass

    def obtener_acta(self):
        pass

    #@mostrar_espera
    def confirmar_recuento(self, recuento):
        try:
            respuesta = self._conexion.confirmar_acta(recuento)
            if respuesta.status_ok():
                alerta = ''
                if 'alerta' in respuesta:
                    alerta = respuesta['alerta']
                self._reiniciar_estados_categorias(respuesta['id_ubicacion'])
                self.cb_actualizacion_informacion(MSG_BOLD %
                                                  respuesta['mensaje'],
                                                  idle=True,
                                                  color=self.COLOR_OK,
                                                  alerta=alerta)
                self._actualizar_estado_mesa(respuesta['id_ubicacion'],
                                             confirmada=True)
            else:
                self.cb_actualizacion_informacion(MSG_ERROR_BOLD %
                                                  respuesta['mensaje'],
                                                  idle=True,
                                                  color=self.COLOR_ERR)
        except Exception as e:
                self.logger.debug(str(e))
                self.cb_actualizacion_informacion(MSG_ERROR_COMUNICACION,
                                                  idle=True,
                                                  color=self.COLOR_ERR)

    @desbloqueante
    def __agregar_acta(self, recuento):
        pass

    #@mostrar_espera
    @desbloqueante
    def __enviar_recuento(self, recuento):
        """
        Envía el resultado al servidor web dentro de un thread en segundo
        plano.
        """
        try:
            respuesta = self._conexion.enviar_recuento(recuento)
            if respuesta.status_ok():
                alerta = ''
                if 'alerta' in respuesta:
                    alerta = respuesta['alerta']
                if 'cod_categoria' in respuesta:
                    self._actualizar_estado_categoria(
                        respuesta['id_ubicacion'], respuesta['cod_categoria'])
                if 'acta_borrador' in respuesta:
                    if self._recuento_anterior != recuento:
                        self.cb_reiniciar_vista_confirmacion()
                    self._reiniciar_estados_categorias(
                        respuesta['id_ubicacion'])
                    self.cb_actualizacion_informacion(MSG_BOLD %
                                                      respuesta['mensaje'],
                                                      idle=True,
                                                      color=self.COLOR_OK,
                                                      alerta=alerta)
                    self._actualizar_estado_mesa(respuesta['id_ubicacion'])
                    self.cb_mostrar_acta(respuesta['img_acta'],
                                         usar_pestana=self._acta_desglosada)
                elif 'confirma_definitiva' in respuesta:
                    self.cb_confirmacion(recuento)
                    self.cb_actualizacion_informacion(MSG_BOLD %
                                                      respuesta['mensaje'],
                                                      idle=True,
                                                      color=self.COLOR_OK,
                                                      alerta=alerta)
                    self.cb_mostrar_acta(respuesta['img_acta'],
                                         usar_pestana=self._acta_desglosada)
                    self._actualizar_estado_mesa(respuesta['id_ubicacion'],
                                                 borrador=True)
                else:
                    self.cb_actualizacion_informacion(MSG_BOLD %
                                                      respuesta['mensaje'],
                                                      idle=True,
                                                      color=self.COLOR_OK,
                                                      alerta=alerta)
                    self.cb_reiniciar_vista_confirmacion()
            else:
                self.cb_actualizacion_informacion(MSG_ERROR_BOLD %
                                                  respuesta['mensaje'],
                                                  idle=True,
                                                  color=self.COLOR_ERR)
                self.cb_reiniciar_vista_confirmacion()
        except Exception as e:
                self.logger.debug(str(e))
                self.cb_actualizacion_informacion(MSG_ERROR_COMUNICACION,
                                                  idle=True,
                                                  color=self.COLOR_ERR)
                self.cb_reiniciar_vista_confirmacion()

    def _actualizar_estado_mesa(self, ubicacion, borrador=False,
                                confirmada=False):
        if ubicacion in self._estados_mesas:
            estado_actual = self._estados_mesas[ubicacion]['estado']

            if estado_actual == ESTADO_ESPERA or borrador:
                self._estados_mesas[ubicacion]['estado'] = ESTADO_PRIMERA_CARGA
            elif estado_actual == ESTADO_PRIMERA_CARGA and confirmada:
                self._estados_mesas[ubicacion]['estado'] = ESTADO_OK
                self._estados_mesas[ubicacion]['cargos'] = {}
        self.cb_actualizacion_mesas()

    def _actualizar_estado_categoria(self, ubicacion, cod_categoria):
        if ubicacion in self._estados_mesas:
            if cod_categoria in self._estados_mesas[ubicacion]['cargos']:
                self._estados_mesas[ubicacion]['cargos'][cod_categoria] \
                    ['estado'] += 1
        self.cb_actualizacion_mesas(activa=ubicacion)

    def _reiniciar_estados_categorias(self, ubicacion):
        if ubicacion in self._estados_mesas:
            for dato in self._estados_mesas[ubicacion]['cargos'].values():
                dato['estado'] = 0

    def _validar_recuento(self, recuento):
        pass

    def _validar_datos(self):
        # @TODO: Verificar si los datos que posee el cliente son válidos
        # encontrar un método para verificar esto
        msg = ''
        destino = '/tmp/datos_actualizados'
        destino_tmp = '/tmp'
        version_datos = ConfiguracionSistema.one(codigo='db_version').valor
        self.logger.debug(
            'Verificando datos locales: {}'.format(version_datos))
        respuesta = self._conexion.obtener_datos_servidor(version_datos)
        self.logger.debug(
            'Verificando datos remotos: {}'.format(respuesta['version']))
        if len(respuesta['archivo']) > 0:
            actualizar_datos(respuesta['ubicacion'], respuesta['archivo'],
                             destino, destino_tmp)
            # Borro la cache del objeto configuracion
            cache_name = ConfiguracionSistema.get_cache_name()
            if cache_name is not None and hasattr(ConfiguracionSistema.cache,
                                                  cache_name):
                ConfiguracionSistema.cache.clear(cache_name)
            # Defino un nuevo origen de datos
            set_data_source(destino)
        else:
            msg = 'no '
        self.logger.debug("Funcion: obtener datos del servidor, "
                          "Los datos para la ubicación {} {} han sido "
                          "actualizados".format(respuesta['ubicacion'], msg))

    def _validar_certificados(self):
        pass

    #@mostrar_espera
    @desbloqueante
    def autenticar(self, datos):
        """
        Autentica el usuario contra el servidor web dentro de un thread en
        segundo plano
        """
        try:
            (usuario, clave) = datos.split(',')
        except ValueError:
            self.cb_actualizacion_informacion(MSG_TARJETA_INVALIDA, idle=True,
                                              color=self.COLOR_ERR)
        else:
            try:
                respuesta = self._conexion.autenticar(usuario, clave)
                if respuesta.status_ok():
                    self.__set_estado_conexion(self.AUTENTICADO)
                    self.cb_actualizacion_informacion('%s' %
                                                      respuesta['mensaje'],
                                                      idle=True,
                                                      color=self.COLOR_OK)
                    estados = respuesta['estado_mesas']
                    self._acta_desglosada, self._estados_mesas = \
                        estados_mesas_dict(estados)
                    self.cb_actualizacion_mesas()
                else:
                    self.cb_actualizacion_informacion(MSG_ERROR_GENERICO %
                                                      respuesta['mensaje'],
                                                      idle=True,
                                                      color=self.COLOR_ERR)
            except Exception as e:
                self.logger.debug(str(e))
                self.cb_actualizacion_informacion(MSG_ERROR_COMUNICACION,
                                                  idle=True,
                                                  color=self.COLOR_ERR)

    def certificados(self):
        pass

    def certificados(self, certificados):
        pass

    def mesas(self):
        return self._estados_mesas

    def __set_estado_conexion(self, estado_conexion):
        """
        """
        self.__estado_conexion = estado_conexion

    def __del__(self):
        self.logger.info("Desconectando")
        self.desconectar()

    #@mostrar_espera
    @bloqueante
    def _evento_tag(self, evento_tag, tag=None, datos_extra=None):
        """ Esta función es llamada cada vez que se detecta un cambio en el
        lector. """
        token = tag.get("token")
        if token is not None:
            token = token.upper()
        if (tag is not None and tag != {} and len(self.valid_tags) > 0 and
                token not in self.valid_tags):
            self.cb_actualizacion_informacion(MSG_CHIP_NO_AUTORIZADO)
        else:
            if evento_tag == NO_TAG:
                self.logger.debug(">>> " + evento_tag)
            elif evento_tag == TAG_ERROR:
                self.logger.debug(evento_tag)
                self.cb_actualizacion_informacion(MSG_ERROR_LEER_CHIP)
            elif evento_tag == TAG_VACIO:
                tipo = tag['tipo']
                if tipo == TAG_NO_ENTRA:
                    msg = MSG_CHIP_NO_ENTRA
                elif tipo:
                    msg = MSG_CHIP_DE_VACIO % tipo
                else:
                    msg = MSG_CHIP_VACIO
                self.cb_actualizacion_informacion(msg)
            elif evento_tag == TAG_DATOS or evento_tag == TAG_ADMIN:
                if (self.__estado_conexion == self.CONECTADO and
                        tag['tipo'] == TAG_USUARIO_MSA):
                    self.cb_actualizacion_informacion(MSG_AUTENTICANDO_USUARIO)
                    thread.start_new_thread(self.autenticar, (tag['datos'],))
                    # salgo para no desbloquear al final:
                    return
                elif (self.__estado_conexion == self.AUTENTICADO and
                        tag['clase'] == CLASE_ICODE2):
                    if tag['tipo'] == TAG_RECUENTO:
                        if tag['datos'] is None:
                            self.cb_actualizacion_informacion(
                                MSG_CONTENIDO_CHIP)
                        else:
                            if not self._acta_desglosada:
                                self.cb_actualizacion_informacion(
                                    MSG_ENVIANDO_DATOS)
                                thread.start_new_thread(self.__enviar_recuento,
                                                        (tag['datos'], ))
                            else:
                                self.cb_actualizacion_informacion(
                                    MSG_RESTO_ACTAS)
                                thread.start_new_thread(self.__enviar_recuento,
                                                        (tag['datos'], ))
                            # salgo para no desbloquear al final:
                            return
                    elif tag['tipo'] in (TAG_USUARIO_MSA, TAG_PRESIDENTE_MESA):
                        pass  # Debería informalo?
                    elif tag['tipo'] in (TAG_INICIO, TAG_ADDENDUM):
                        pass  # Espera a que le llegue el evento tag recuento
                    elif tag['tipo'] == TAG_NO_ENTRA:
                        self.cb_actualizacion_informacion(MSG_CHIP_NO_ENTRA)
                    else:
                        self.cb_actualizacion_informacion(
                            MSG_CHIP_NO_TIPO_RECUENTO)
                else:
                    if tag['clase'] == CLASE_ICODE2:
                        self.cb_actualizacion_informacion(
                            MSG_CHIP_NO_ICODE2 % tag['tipo'])
                    elif tag['clase'] == CLASE_MIFARE:
                        self.cb_actualizacion_informacion(MSG_CHIP_NO_RECUENTO)

        if self.lock:
            self.logger.debug("%s: libero lock manual!" % "_lector_callback")
            self.lock.release()

    def __verificar_estado_servidor_tx(self, url):
        _conexion = Conexion(url, DEBUG, self.config.TIMEOUT)
        _conexion.set_https_keys(self.config.KEY_FILE,
                                 self.config.CERT_FILE)
        _conexion.set_ca_certificate(self.config.CA_FILE)
        result = _conexion.test_conexion()
        estado = result["status"] if result else "Error de conexion"
        return estado

    def __verificar_estado(self, pruebas):
        for prueba in pruebas:
            verificador = prueba[2]
            estado = verificador(prueba[1])
            print "ESTADO:", estado
            self.logger.debug("Realizando prueba %d al sitio %s: %s",
                              prueba[0], prueba[1], estado)
            self.cb_fin_prueba_estados(prueba[:2] + (estado, ))

    def verificar_estado(self):
        pruebas = [
            (0, "Conexión a internet", "http://www.google.com.ar",
             status_for_url),
            (1, "Conexión al servidor de Transmisión", '{}://{}/'.format(
                 PROTOCOLO, self.config.HOST),
             self.__verificar_estado_servidor_tx),
            (2, "Conexión al sitio de Operaciones", '{}://{}'.format(
                PROTOCOLO_CERTS, self.config.HOST_CERTS),
             status_for_url)]

        paginas_pruebas = [(p[0], p[2], p[3]) for p in pruebas]
        lista_pruebas = [p[:-1] for p in pruebas]
        thread.start_new_thread(self.__verificar_estado, (paginas_pruebas, ))

        return lista_pruebas

    #@mostrar_espera
    def __diagnostico(self, ips, pruebas):
        resultados = {}

        for ip in ips:
            resultados[ip] = {}
            for prueba in pruebas:
                cmd = prueba[1] % ip
                proc = Popen(['bash', '-c', cmd], stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                proc.wait()

                resultados[ip][prueba[0]] = out

        respuesta = self._conexion.enviar_diagnostico(resultados)
        self.cb_actualizacion_informacion(respuesta['mensaje'])

    def diagnostico(self):
        if self._conexion is not None:
            ips = ['8.8.8.8']
            # Lista de pruebas compuesta por (clave, comando)
            pruebas = [
                ('alive', '(ping -c 1 %s >/dev/null && echo 0) || echo 1;'),
                ('ping', 'ping -i 0.2 -c 5 %s | tail -n 1 | cut -d " " -f 4'),
                ('mtr', 'mtr --report --no-dns %s'),
                ('dig', 'dig %s'),
                ('dig_other', 'dig %s @8.8.8.8')
            ]
            thread.start_new_thread(self.__diagnostico, (ips, pruebas, ))

    # ------------------------------------------------------------------------#
    #                 Metodos que deben implementarse en el UI                #
    # ------------------------------------------------------------------------#
    def esperando_evento(self, esperando, idle=False):
        """
        Muestra al usuario actividad indicando que se esta procesando algo.
        """
        raise NotImplemented

    def cb_actualizacion_mesas(self):
        """
        Callback para que la UI actualice la información de las mesas.
        """
        raise NotImplemented

    def cb_actualizacion_estado(self, status):
        """
        Callback de actualización de estados
        """
        raise NotImplemented

    def cb_actualizacion_informacion(self, text, idle=False, color=None,
                                     alerta=''):
        """
        Callback para el envio de información a mostrar al usuario.
        """
        raise NotImplemented

    def cb_confirmacion(self, datos_tag):
        """
        Callback de confirmación de recuentos
        """
        raise NotImplemented

    def cb_mostrar_acta(self, lista_imagenes, usar_pestana=False):
        """
        Callback para mostrar la/s imagen/es de las actas
        Recibe un listado de actas con la siguiente estructura
        [(cod_categoria, descripcion, idx_categoria, imagen)]
        """
        raise NotImplemented

    def cb_actualizar_opciones(self, lista_botones):
        """
        Callback para interactuar con las acciones disponibles.
        """
        raise NotImplemented

    def cb_perdida_conexion(self):
        """
        Callback llamado unicamente cuando el echo_loop detecta que no hay
        conectividad con el servidor
        """
        raise NotImplemented

    def cb_fin_prueba_estados(self, datos_prueba):
        """
        Callback llamado cuando se finaliza una prueba de la pantalla de estado
        """
        raise NotImplemented

    def cb_reiniciar_vista_confirmacion(self):
        """
        Callback llamado cuando se reinicia la vista de confirmación de acta
        """
        raise NotImplemented


class TransmisionClient(TransmisionCore):

    def cb_actualizacion_mesas(self):
        if not self.mesas():
            print "Sin información de mesas."
        else:
            mesas = self.mesas()
            for id_ubicacion in mesas:
                mesa = mesas[id_ubicacion]
                print "{}: Mesa: {} {:>10}".format(id_ubicacion,
                                                   mesa['numero'],
                                                   mesa['estado'])

    def esperando_evento(self, activo, idle=False):
        print "Esperando Evento %s" % activo

    def cb_actualizacion_informacion(self, text, idle=False, color=None,
                                     alerta=''):
        """
        """
        self.logger.info(text)
        self.cb_actualizacion_mesas()

    def cb_actualizacion_estado(self, status):
        print self.mesas()
        self.logger.info("{0}: {1}".format(*status))

    def cb_confirmacion(self, datos_tag):
        """
        Callback de confirmación de recuentos
        """
        print "Confirmación"

    def cb_mostrar_acta(self, lista_imagenes, usar_pestana=False):
        """
        Callback para mostrar la/s imagen/es de las actas
        Recibe un listado de actas con la siguiente estructura
        [(cod_categoria, descripcion, idx_categoria, imagen)]
        """
        pass

    def cb_actualizar_opciones(self, lista_botones):
        """
        Callback para interactuar con las acciones disponibles.
        """
        pass

    def cb_perdida_conexion(self):
        """
        Callback llamado unicamente cuando el echo_loop detecta que no hay
        conectividad con el servidor
        """
        print "Se ha perdido la conexión con el servidor"

    def cb_fin_prueba_estados(self, datos_prueba):
        """
        Callback llamado cuando se finaliza una prueba de la pantalla de estado
        """
        pass

    def cb_reiniciar_vista_confirmacion(self):
        """
        Callback llamado cuando se reinicia la vista de confirmación de acta
        """
        raise NotImplemented

if __name__ == '__main__':
    import gtk
    gtk.gdk.threads_init()
    app = TransmisionClient()
    app.conectar()
    gtk.main()
