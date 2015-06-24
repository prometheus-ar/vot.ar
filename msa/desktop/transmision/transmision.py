#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import re
import subprocess
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import image_viewer
import thread
import time

from base64 import b64decode
from ojota import set_data_source
from os.path import join

from msa import get_logger
from msa.constants import ESTADO_OK, ESTADO_PUBLICADA
from msa.core.clases import Recuento
from msa.core.constants import CIERRE_TRANSMISION
from msa.core.data import Configuracion as ConfiguracionSistema
from msa.core.rfid.constants import TAG_RECUENTO, CLASE_ICODE2, \
    TAG_USUARIO_MSA, TAG_PRESIDENTE_MESA, CLASE_MIFARE
from msa.desktop.transmision.common import AcercaDe, Autenticacion, \
    ImportarClaves, Preferencias, BotonColor
from msa.desktop.transmision.conexion import Conexion
from msa.desktop.transmision.config import Configuracion
from msa.desktop.transmision.constants import (
    MSG_ERROR_CONF_APP, MSG_CONECTADO, MSG_CONECTANDO, MSG_LECTOR_DESCONECTADO,
    MSG_CONECTANDO_ESPERE, MSG_AHORA_PASE_TARJETA, MSG_COMPRUEBE_CONEXION,
    MSG_VERIFIQUE_CERTIFICADOS, MSG_INTENTE_NUEVAMENTE, MSG_CHIP_NO_AUTORIZADO,
    NOMBRE_APLICACION, MSG_CHIP_DE_VACIO, MSG_CHIP_VACIO,
    MSG_AUTENTICANDO_USUARIO, MSG_CONTENIDO_CHIP, MSG_ENVIANDO_DATOS,
    MSG_CHIP_NO_TIPO_RECUENTO, MSG_CHIP_NO_ICODE2, MSG_CHIP_NO_RECUENTO,
    MSG_ERROR_COMUNICACION, MSG_CONFIRMACION_CIERRE_CANCELADA,
    MSG_TARJETA_INVALIDA, MSG_ERROR_BOLD, MSG_BOLD, MSG_ERROR_GENERICO,
    MSG_ATENCION_NO_CONFIRMADAS, MSG_ERROR_LEER_CHIP, MSG_MESA_NO_HABILITADA,
    MSG_BIG_SI, MSG_BIG_NO, MSG_BIG_SPAN_COLOR,
    MSG_BIG_SPAN, MSG_BIG_SPAN_ALERT,
    MSG_GENERANDO_IMG, MSG_RESTO_ACTAS,
    ST_CONECTADO, ST_DESCONECTADO, ST_NO_LECTOR)
from msa.desktop.transmision.helpers import (
    bloqueante, desbloqueante, mostrar_espera, get_desktop_path,
    actualizar_datos)
from msa.desktop.transmision.modulos import ModuloLector, NO_TAG, TAG_ERROR, \
    TAG_VACIO, TAG_DATOS, TAG_ADMIN
from msa.desktop.transmision.settings import PING_EVERY, \
    PATH_NETWORK_CONF_APP, PROTOCOLO, DEBUG
from msa.helpers import levantar_locales
from msa.core.settings import ACTA_DESGLOSADA


levantar_locales()
logger = get_logger(NOMBRE_APLICACION)
multi_test = False


class TransmisionApp(object):
    # Constantes de Estados
    DESCONECTADO = 0
    CONECTADO = 1
    AUTENTICADO = 2

    MARGEN_LECTURAS_CON_COLISION = 2
    MARGEN_LECTURAS_ERRONEAS = 2

    COLOR_OK = '#006600'
    COLOR_ERR = '#FF0000'
    COLOR_ALERTA = '#FF0000'

    def __init__(self, hw_init=True):
        self.config = Configuracion()
        if self.config.USAR_LOCK == 'true':
            self.lock = thread.allocate_lock()
        else:
            self.lock = None
        logger.debug("__init__: lock = " + str(self.lock))
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndPrincipal = self._widget_tree.get_widget('wndPrincipal')
        self._lblMensajePantalla = self._widget_tree.get_widget(
            'lblMensajePantalla')
        self._vbox_acta = self._widget_tree.get_widget('vbox_acta')
        self._widget_vport = self._widget_tree.get_widget('vp_acta')
        self._status = self._widget_tree.get_widget('status')
        self._lbl_mesas = self._widget_tree.get_widget('lbl_mesas')
        self.__set_estado_conexion(self.DESCONECTADO)
        self.__modulo_lector = ModuloLector(self._lector_callback, False)

        self._conexion = None
        self._timeout_id = None
        eventos = {
            "on_wndPrincipal_delete": self.salir,
            "on_tlbSalir_clicked": self.salir,
            "on_mnuArchivoSalir_activate": self.salir,
            "on_mnuAyudaAcercaDe_activate": self.mostrar_acerca_de,
            "on_mnuAccionesRed_activate": self.configurar_red,
            "on_mnuAccionesImportar_activate": self.mostrar_importar_claves,
            "on_tblPreferencias_clicked": self.mostrar_preferencias,
            "on_tlbConectar_clicked": self.conectar,
            "on_tblConfigurarRed_clicked": self.configurar_red,
            "on_tblImportarCert_clicked": self.mostrar_importar_claves,
            "on_tlbBajarCert_clicked": self.mostrar_autenticacion,
        }
        self._widget_tree.signal_autoconnect(eventos)

        self.borradores = []
        self.valid_tags = None
        self._actas = {}

    def mostrar_autenticacion(self, menuitem):
        autenticacion = Autenticacion(self.config, self)
        autenticacion.mostrar()

    def mostrar(self):
        if not DEBUG:
            self._wndPrincipal.maximize()
        self._wndPrincipal.show()

    def mostrar_acerca_de(self, menuitem):
        acerca_de = AcercaDe(self.config)
        acerca_de.mostrar()

    def mostrar_preferencias(self, menuitem):
        preferencias = Preferencias(self.config)
        preferencias.mostrar()

    def mostrar_importar_claves(self, menuitem):
        wnd_importar_claves = ImportarClaves(self.config)
        wnd_importar_claves.mostrar()

    def configurar_red(self, *args):
        try:
            subprocess.Popen(PATH_NETWORK_CONF_APP, shell=False)
        except OSError as e:
            logger.error(MSG_ERROR_CONF_APP % str(e.message))

    @bloqueante
    def conectar(self, toolbutton):
        if self.__estado_conexion != self.DESCONECTADO:
            self.set_mensaje(MSG_CONECTADO)
            self.set_status(("conexion", ST_CONECTADO))
        elif self._conexion is not None:
            self.set_mensaje(MSG_CONECTANDO)
        elif self.__modulo_lector is None:
            self.set_mensaje(MSG_LECTOR_DESCONECTADO %
                             self.config.PUERTO_LECTOR)
            self.set_status(("lector", ST_NO_LECTOR))
        else:
            self.set_mensaje(MSG_CONECTANDO_ESPERE)
            self._conexion = Conexion('%s://%s/' % (PROTOCOLO,
                                                    self.config.HOST),
                                      DEBUG, self.config.TIMEOUT)
            self._conexion.set_https_keys(self.config.KEY_FILE,
                                          self.config.CERT_FILE)
            self._conexion.set_ca_certificate(self.config.CA_FILE)
            thread.start_new_thread(self.__conectar, ())
            self.__conectar_lector()
            return

        if self.lock:
            logger.debug("_conectar: libero lock manual!")
            self.lock.release()

    @desbloqueante
    def __conectar_lector(self):
        self.set_mensaje(MSG_AHORA_PASE_TARJETA,
                         idle=True, color=self.COLOR_OK)

        self.__modulo_lector.conectar_lector()
        return

    @mostrar_espera
    @desbloqueante
    def __conectar(self):
        """Conectar al servidor web usando un thread en segundo plano"""
        logger.info("llamando a conectar")
        result = self._conexion.test_conexion()
        if result is not False and result.status_ok():
            if self.config.VERIFICAR_DATOS:
                self._verificar_datos()
            self.valid_tags = [b64decode(tag).upper() for tag
                               in result._dict['tags']]

            self.__set_estado_conexion(self.CONECTADO)
            self.set_status(("conexion", ST_CONECTADO))
            self.set_mensaje(MSG_AHORA_PASE_TARJETA,
                             idle=True, color=self.COLOR_OK)
            gobject.idle_add(self._set_timeout)

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
            self.set_mensaje(MSG_INTENTE_NUEVAMENTE % ayuda, idle=True,
                             color=self.COLOR_ERR)
            self._conexion = None
            self.set_status(("conexion", ST_DESCONECTADO))

    def _set_timeout(self):
        if self._timeout_id is not None:
            gobject.source_remove(self._timeout_id)
        self._timeout_id = gobject.timeout_add_seconds(PING_EVERY, self._conexion.test_conexion)
        return False

    @desbloqueante
    def __desconectar(self):
        """Cierra la conexión al servidor web usando un thread en segundo
        plano"""
        if self._timeout_id is not None:
            gobject.source_remove(self._timeout_id)
        logger.info("llamando a conectar")
        self._conexion.desconectar()
        self.set_status(("conexion", ST_DESCONECTADO))

    def _verificar_datos(self):
        # @TODO: Verificar si los datos que posee el cliente son válidos
        # encontrar un método para verificar esto
        msg = ''
        destino = '/tmp/datos_actualizados'
        destino_tmp = '/tmp'
        version_datos = ConfiguracionSistema.one(codigo='db_version').valor
        logger.debug('Verificando datos locales: {}'.format(version_datos))
        respuesta = self._conexion.obtener_datos_servidor(version_datos)
        logger.debug('Verificando datos remotos: {}'.format(
            respuesta['version']))
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
        logger.debug("Funcion: obtener datos del servidor, "
                     "Los datos para la ubicación {} {}han sido "
                     "actualizados".format(respuesta['ubicacion'], msg))

    def esperando_evento(self, ocupado, idle=True):
        """ Setea el puntero de la ventana principal en ocupado (True) o
        flecha estándar (False). Es idle por defecto porque se lo llama casi
        exclusivamente desde el segundo hilo.
        """
        if ocupado:
            cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        else:
            cursor = None
        if idle:
            gobject.idle_add(self._wndPrincipal.window.set_cursor, cursor)
        else:
            self._wndPrincipal.window.set_cursor(cursor)

    def set_status(self, status):
        pass

    def set_mensaje(self, text, idle=False, color=None, alerta=''):
        """ Modifica el string de la pantalla. Acepta pango markup, ser llamado
            cuando gtk está idle y un color.
            Ver http://www.pygtk.org/docs/pygtk/pango-markup-language.html
        """
        if color:
            text = MSG_BIG_SPAN_COLOR % (color, text)
        else:
            text = MSG_BIG_SPAN % text

        if alerta:
            text = MSG_BIG_SPAN_ALERT % (self.COLOR_ALERTA, alerta) + text

        if idle:
            gobject.idle_add(self._lblMensajePantalla.set_label, text)
        else:
            self._lblMensajePantalla.set_label(text)

        if multi_test:
            p = re.compile(r'<.*?>')
            logger.debug(">>> " + p.sub('', text))

    def get_mensaje(self):
        """ Obtiene el string de la pantalla, sin el pango markup """
        return self._lblMensajePantalla.get_text()

    def agregar_mensaje(self, text, idle=False):
        mensaje = self.get_mensaje() + '\n' + text
        if idle:
            gobject.idle_add(self._lblMensajePantalla.set_label, mensaje)
        else:
            self._lblMensajePantalla.set_label(mensaje)

    @mostrar_espera
    @bloqueante
    def _lector_callback(self, evento_tag, tag=None, datos_extra=None):
        """ Esta función es llamada cada vez que se detecta un cambio en el
        lector. """
        token = tag.get("token")
        if token is not None:
            token = token.upper()
        if (tag is not None and tag != {} and len(self.valid_tags) > 0 and
                token not in self.valid_tags):
            self.set_mensaje(MSG_CHIP_NO_AUTORIZADO)
        else:
            if evento_tag == NO_TAG:
                logger.debug(">>> " + evento_tag)
            elif evento_tag == TAG_ERROR:
                logger.debug(evento_tag)
                self.set_mensaje(MSG_ERROR_LEER_CHIP)
            elif evento_tag == TAG_VACIO:
                tipo = tag['tipo']
                if tipo:
                    msg = MSG_CHIP_DE_VACIO % tipo
                else:
                    msg = MSG_CHIP_VACIO
                self.set_mensaje(msg)
            elif evento_tag == TAG_DATOS or evento_tag == TAG_ADMIN:
                if (self.__estado_conexion == self.CONECTADO and
                        tag['tipo'] == TAG_USUARIO_MSA):
                    self.set_mensaje(MSG_AUTENTICANDO_USUARIO)
                    thread.start_new_thread(self.__autenticar, (tag['datos'],))
                    # salgo para no desbloquear al final:
                    return
                elif (self.__estado_conexion == self.AUTENTICADO and
                        tag['clase'] == CLASE_ICODE2):
                    if tag['tipo'] == TAG_RECUENTO:
                        if tag['datos'] is None:
                            self.set_mensaje(MSG_CONTENIDO_CHIP)
                        else:
                            self.set_mensaje(MSG_ENVIANDO_DATOS)
                            if multi_test:
                                # a veces esto se ejecutaba despues del
                                # thread de enviar
                                gobject.idle_add(self._elimimar_vista_acta)
                            if not ACTA_DESGLOSADA:
                                self.set_mensaje(MSG_ENVIANDO_DATOS)
                                thread.start_new_thread(self.__enviar_recuento,
                                                        (tag['datos'], ))
                            else:
                                self.set_mensaje(MSG_RESTO_ACTAS)
                                thread.start_new_thread(self.agregar_acta,
                                                        (tag['datos'], ))
                            # salgo para no desbloquear al final:
                            return
                    elif tag['tipo'] in (TAG_USUARIO_MSA, TAG_PRESIDENTE_MESA):
                        pass  # Debería informalo?
                    else:
                        self.set_mensaje(MSG_CHIP_NO_TIPO_RECUENTO)
                else:
                    if tag['clase'] == CLASE_ICODE2:
                        self.set_mensaje(MSG_CHIP_NO_ICODE2 % tag['tipo'])
                    elif tag['clase'] == CLASE_MIFARE:
                        self.set_mensaje(MSG_CHIP_NO_RECUENTO)

        if self.lock:
            logger.debug("%s: libero lock manual!" % "_lector_callback")
            self.lock.release()

    @desbloqueante
    def agregar_acta(self, data):
        recuento = Recuento.desde_tag(data)

        data_mesa = None
        for mesa in self._estados_mesas:
            if mesa[0][2] == recuento.mesa.numero and mesa[0][1] \
               not in (ESTADO_OK, ESTADO_PUBLICADA):

                data_mesa = mesa
                break

        if data_mesa is not None:
            dict_actas = self._actas.get(recuento.mesa.codigo)
            if dict_actas is None:
                self._actas[recuento.mesa.codigo] = {}
                dict_actas = self._actas.get(recuento.mesa.codigo)
            dict_actas[recuento.cod_categoria] = recuento
            recopiladas = []
            for categoria in data_mesa[1:]:
                if categoria[0] == recuento.cod_categoria:
                    categoria[3] = True
                    gobject.idle_add(self._update_estados_mesas)
                recopiladas.append(categoria[3])

            self._elimimar_vista_acta()
            self.set_mensaje(MSG_GENERANDO_IMG)

            imagen = recuento.a_imagen(svg=True, de_muestra=True,
                                       tipo=(CIERRE_TRANSMISION,
                                             recuento.cod_categoria))
            path_destino = join(get_desktop_path(),
                "%s_%s.svg" % (recuento.mesa.numero, recuento.cod_categoria))
            file_destino = open(path_destino, 'w')
            file_destino.write(imagen)
            file_destino.close()
            self._mostrar_acta(path_destino)
            self.set_mensaje(MSG_RESTO_ACTAS)

            if all(recopiladas):
                actas = dict_actas.values()
                recuento_ = Recuento(actas[0].mesa)
                campos_especiales = [
                    "votos_emitidos", "votos_impugnados", "votos_nulos",
                    "votos_recurridos", "votos_observados",
                    "cantidad_ciudadanos", "certificados_impresos"
                ]
                primer_acta = actas[0]
                for campo in campos_especiales:
                    if hasattr(primer_acta, campo):
                        setattr(recuento_, campo, getattr(primer_acta, campo))
                for acta in actas:
                    for key, value in acta._resultados.items():
                        if key[0] == acta.cod_categoria:
                            recuento_._resultados[key] = value
                datos_tag = recuento_.a_tag()
                thread.start_new_thread(self.__enviar_recuento, (datos_tag, ))
                if multi_test:
                    self._ultimo_recuento = datos_tag
                if len(self._vbox_acta.children()) == 1:
                    botsi = BotonColor(MSG_BIG_SI, "#00cc00", "#ffffff")
                    botno = BotonColor(MSG_BIG_NO, "#ff0000",
                                       "#000000")
                    botsi.set_size_request(80, 70)
                    botno.set_size_request(80, 70)
                    botsi.connect("button-release-event",
                                    self._confirmar_transmision, datos_tag)
                    botno.connect("button-release-event",
                                    self._cancelar_confirmacion)
                    _hbox = gtk.HBox(False)
                    _hbox.set_border_width(10)
                    _hbox.pack_start(botno, padding=100)
                    sep = gtk.VSeparator()
                    sep.set_size_request(80, -1)
                    _hbox.pack_start(sep, True, True)
                    _hbox.pack_start(botsi, padding=100)

                    self._vbox_acta.pack_end(_hbox, False, True)
                    # Descargo y muestro el borrador nuevamente
                    self._vbox_acta.show_all()
                    #self.set_mensaje(MSG_BOLD % respuesta['mensaje'],
                    #                    idle=True, color=self.COLOR_OK,
                    #                    alerta=alerta)
        else:
            # la mesa no esta para transm
            self.set_mensaje(MSG_MESA_NO_HABILITADA)

    @mostrar_espera
    @desbloqueante
    def __enviar_recuento(self, datos_tag):
        """Envía el resultado al servidor web dentro de un thread en segundo
        plano."""
        try:
            respuesta = self._conexion.enviar_recuento(datos_tag)
            if respuesta.status_ok():
                alerta = ''
                if 'alerta' in respuesta:
                    alerta = respuesta['alerta']
                if 'acta_borrador' in respuesta:
                    # Descargo y muestro el borrador
                    if not ACTA_DESGLOSADA:
                        #self._descargar_y_mostrar_acta(respuesta)
                        self._generar_y_mostrar_acta(datos_tag)
                        self.set_mensaje(MSG_BOLD % respuesta['mensaje'],
                                         idle=True, color=self.COLOR_OK,
                                         alerta=alerta)
                    self.borradores.append(datos_tag)
                    #if ACTA_DESGLOSADA:
                    #    self.__enviar_recuento(datos_tag)
                elif 'confirma_definitiva' in respuesta:
                    self._generar_y_mostrar_acta(datos_tag)
                    if len(self._vbox_acta.children()) < 2:
                        # Muestro la botonera de confirmacion
                        botsi = BotonColor(MSG_BIG_SI, "#00cc00", "#ffffff")
                        botno = BotonColor(MSG_BIG_NO, "#ff0000", "#000000")
                        botsi.set_size_request(80, 70)
                        botno.set_size_request(80, 70)
                        botsi.connect("button-release-event",
                                      self._confirmar_transmision, datos_tag)
                        botno.connect("button-release-event",
                                      self._cancelar_confirmacion)
                        _hbox = gtk.HBox(False)
                        _hbox.set_border_width(10)
                        _hbox.pack_start(botno, padding=100)
                        sep = gtk.VSeparator()
                        sep.set_size_request(80, -1)
                        _hbox.pack_start(sep, True, True)
                        _hbox.pack_start(botsi, padding=100)
                        self._vbox_acta.pack_end(_hbox, False, True)
                    # Descargo y muestro el borrador nuevamente
                    #self._descargar_y_mostrar_acta(respuesta)
                    self._vbox_acta.show_all()
                    self.set_mensaje(MSG_BOLD % respuesta['mensaje'],
                                     idle=True, color=self.COLOR_OK,
                                     alerta=alerta)
                else:
                    self.set_mensaje(MSG_BOLD % respuesta['mensaje'],
                                     idle=True, color=self.COLOR_OK,
                                     alerta=alerta)
            else:
                self.set_mensaje(MSG_ERROR_BOLD % respuesta['mensaje'],
                                 idle=True, color=self.COLOR_ERR)
        except Exception as e:
                logger.debug(str(e))
                self.set_mensaje(MSG_ERROR_COMUNICACION, idle=True,
                                 color=self.COLOR_ERR)

    def _confirmar_transmision(self, w=None, ev=None, datos_tag=None):
        respuesta_conf = self._conexion.confirmar_acta(datos_tag)
        if respuesta_conf.status_ok() and 'acta_definitiva' in respuesta_conf:
            # Descargo y muestro el definitivo
            #self._descargar_y_guardar_acta(respuesta_conf)
            self.set_mensaje(MSG_BOLD % respuesta_conf['mensaje'],
                             idle=True, color=self.COLOR_OK)
            self._quitar_mesa(respuesta_conf['mesa'])
            self._update_estados_mesas()
            if datos_tag in self.borradores:
                self.borradores.remove(datos_tag)
        else:
            self.set_mensaje(MSG_ERROR_BOLD % respuesta_conf['mensaje'],
                             idle=True, color=self.COLOR_ERR)
        self._elimimar_vista_acta()

    def _cancelar_confirmacion(self, w=None, ev=None):
        self.set_mensaje(MSG_CONFIRMACION_CIERRE_CANCELADA, idle=True,
                         color=self.COLOR_OK)
        gobject.idle_add(self._elimimar_vista_acta)

    @mostrar_espera
    @desbloqueante
    def __autenticar(self, datos):
        """
            Autentica el usuario contra el servidor web dentro de un thread en
            segundo plano
        """
        try:
            (usuario, clave) = datos.split(',')
        except ValueError:
            self.set_mensaje(MSG_TARJETA_INVALIDA, idle=True,
                             color=self.COLOR_ERR)
        else:
            try:
                respuesta = self._conexion.autenticar(usuario, clave)
                if respuesta.status_ok():
                    self.__set_estado_conexion(self.AUTENTICADO)
                    self.set_mensaje('%s' % respuesta['mensaje'], idle=True,
                                     color=self.COLOR_OK)
                    # @TODO: Modificar la lista de estados desde el servidor
                    # para capturar los estados de las mesas y mostrar en
                    # distintos colores como la web de consulta
                    estados = respuesta['estado_mesas']
                    for mesa in estados:
                        for categoria in mesa[1:]:
                            categoria.append(False)
                    self._estados_mesas = estados
                    self._update_estados_mesas()
                else:
                    self.set_mensaje(MSG_ERROR_GENERICO % respuesta['mensaje'],
                                     idle=True, color=self.COLOR_ERR)
            except Exception as e:
                logger.debug(str(e))
                self.set_mensaje(MSG_ERROR_COMUNICACION, idle=True,
                                 color=self.COLOR_ERR)

    def _quitar_mesa(self, id_mesa):
        nuevos_estados = []

        for estado in self._estados_mesas:
            data_mesa = estado[0]
            if data_mesa[2].strip() != id_mesa[5:].strip():
                nuevos_estados.append([data_mesa] + estado[1:])

        self._estados_mesas = nuevos_estados

    def _update_estados_mesas(self):
        lbls_mesas = []
        for mesa in self._estados_mesas:
            data_mesa = mesa[0]
            if data_mesa[1] not in (ESTADO_OK, ESTADO_PUBLICADA):
                actas = " ".join([("<b>%s</b>" % cargo[0]) if cargo[3]
                                  else cargo[0] for cargo in mesa[1:]])
                lbl = "Mesa %s%s%s%s" % \
                    (data_mesa[2],
                     (data_mesa[3] if data_mesa[3] is not None else "X"),
                      " - " if len(actas) else "", actas)
                lbls_mesas.append(lbl)

        lbl_pendientes = self._widget_tree.get_widget('label1')
        gobject.idle_add(lbl_pendientes.set_text,
                         "Pendientes(%s):" % len(lbls_mesas))

        gobject.idle_add(self._lbl_mesas.set_markup, "\n".join(lbls_mesas))

    def _elimimar_vista_acta(self):
        for child in self._vbox_acta.get_children():
            self._vbox_acta.remove(child)

    def _generar_y_mostrar_acta(self, datos_tag):
            self._elimimar_vista_acta()
            recuento = Recuento.desde_tag(datos_tag)
            self.set_mensaje(MSG_GENERANDO_IMG)

            imagen = recuento.a_imagen(svg=True, de_muestra=True,
                                       tipo=(CIERRE_TRANSMISION,
                                             recuento.cod_categoria))
            path_destino = join(get_desktop_path(),
                "%s_%s.svg" % (recuento.mesa.numero, recuento.cod_categoria))
            file_destino = open(path_destino, 'w')
            file_destino.write(imagen)
            file_destino.close()
            self._mostrar_acta(path_destino)
            self.set_mensaje(MSG_RESTO_ACTAS)

    def _descargar_y_mostrar_acta(self, respuesta):
        """ Descarga el acta del servidor y lo muestra al usuario """
        if not ACTA_DESGLOSADA:
            path_destino = join(get_desktop_path(),
                                respuesta['file_name'])
            url_acta = '%s://%s/%s' % (PROTOCOLO, self.config.HOST,
                                       respuesta['url'])
            self._conexion.descargar(url_acta, path_destino)
            self._mostrar_acta(path_destino)

    def _mostrar_acta(self, path_destino):
        imgviewer = image_viewer.SimpleImageViewer(path_destino)
        self._vbox_acta.pack_start(imgviewer, True, True)
        self._vbox_acta.show_all()
        self._vbox_acta.show()

    def _descargar_y_guardar_acta(self, respuesta):
        """ Descarga el acta del servidor y lo guarda al usuario """
        path_destino = join(os.getenv('HOME'), respuesta['file_name'])
        self._conexion.descargar('%s://%s/%s' % (PROTOCOLO, self.config.HOST,
                                                 respuesta['url']),
                                 path_destino)
        self._elimimar_vista_acta()

    def __set_estado_conexion(self, estado_conexion):
        """
        """
        self.__estado_conexion = estado_conexion
        self.__tiempo_conexion = time.time()

    def salir(self, *args):
        if self.borradores:
            msg = MSG_ATENCION_NO_CONFIRMADAS % len(self.borradores)
            dialog = gtk.MessageDialog(self._wndPrincipal, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,
                                       msg)
            dialog.connect('response', self._respuesta_salir)
            dialog.run()
            dialog.destroy()
        else:
            self.salir_definitivo()

    def _respuesta_salir(self, dialog, response, data=None):
        if response == gtk.RESPONSE_OK:
            self.salir_definitivo()

    def salir_definitivo(self):
        if self.__modulo_lector:
            self.__modulo_lector.desconectar_lector()
        gtk.main_quit()


if __name__ == '__main__':
    gtk.gdk.threads_init()
    app = TransmisionApp()
    app.mostrar()
    gtk.main()
