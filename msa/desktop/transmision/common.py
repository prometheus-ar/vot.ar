#!/usr/bin/env python
#-*- coding:utf-8 -*-
import gtk
import urllib
import urllib2
import os

from os.path import join
from json import loads

from msa.desktop.transmision.constants import MSG_ERROR_BAJAR_CERT, \
    MSG_ERROR_BAJAR_CERT_GRAVE, MSG_DESCARGANDO_CERTS, MSG_CLAVES_IMPORTADAS, \
    MSG_NO_HAY_CLAVES, MSG_WRONG_PASS, MSG_ERROR_COMUNICACION, \
    MSG_ARCHIVO_CLAVE, MSG_ARCHIVO_CERT, MSG_ARCHIVO_CA, MSG_DEBE_REINICIAR, \
    MSG_FALTAN_CERTIFICADOS, MSG_CERTIFICADOS_DANADOS
from msa.desktop.transmision.helpers import importar_claves, download
from msa.desktop.transmision.settings import PROTOCOLO_CERTS, \
    URL_LOGIN_CERTS, PATH_KEYS, PATH_CERTS, PATH_CA, PATTERN_PKEY, \
    PATTERN_CERT, PATTERN_TAR_GZ, PATTERN_GZ, PATTERN_TGZ


class AcercaDe(object):
    def __init__(self, config):
        self.config = config
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndAcercaDe = self._widget_tree.get_widget('wndAcercaDe')

    def mostrar(self):
        self._wndAcercaDe.run()
        self._wndAcercaDe.hide()


class Autenticacion(object):
    def __init__(self, config, app):
        self.config = config
        self.app = app
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndAtenticacion = self._widget_tree.get_widget('wndAutenticacion')
        eventos = {"on_btnEnviar_clicked": self.aceptar}
        self._widget_tree.signal_autoconnect(eventos)
        self._user = self._widget_tree.get_widget('txtUser')
        self._pass = self._widget_tree.get_widget('txtPass')
        self._widget_tree.get_widget('btnEnviar').grab_default()
        self._wndAtenticacion.activate_default()

    def mostrar(self):
        self._wndAtenticacion.run()
        self._wndAtenticacion.hide()

    def aceptar(self, widget):
        self._wndAtenticacion.hide()
        self.app.set_mensaje("Autenticando usuario")

        username = self._user.get_text()
        password = self._pass.get_text()

        values = {
            'username': username,
            'password': password
        }
        url_base = '%s://%s' % (PROTOCOLO_CERTS, self.config.HOST_CERTS)
        url_login = '%s%s' % (url_base, URL_LOGIN_CERTS)
        data = urllib.urlencode(values)

        req = urllib2.Request(url_login, data)
        try:
            response = urllib2.urlopen(req)
            data = response.read()
            # TODO: el json viene escapado. solucionar el doble load.
            response_data = loads(data)
            response_auth = response_data.get('authenticated')
            response_mesg = response_data.get('message')
            response_certs = response_data.get('certs')
            if response_auth == 1:
                if not response_mesg:
                    if len(response_certs):
                        self.app.set_mensaje(MSG_DESCARGANDO_CERTS)
                        #TODO or not TODO: si es tecnico en mas de una escuela
                        # toma el último según el orden en que se envia la
                        # lista.
                        try:
                            establecimiento, archivo = response_certs.pop()
                            destino = download(url_base, archivo, username,
                                               password)
                            faltan_archivos, archivos_danados = \
                                importar_claves(destino, self.config)

                            if faltan_archivos:
                                self.app.set_mensaje(MSG_FALTAN_CERTIFICADOS)
                            elif archivos_danados:
                                self.app.set_mensaje(MSG_CERTIFICADOS_DANADOS)
                            else:
                                self.app.set_mensaje(MSG_CLAVES_IMPORTADAS)
                        except urllib2.HTTPError:
                            self.app.set_mensaje(MSG_ERROR_BAJAR_CERT)
                        except Exception:
                            self.app.set_mensaje(MSG_ERROR_BAJAR_CERT_GRAVE)
                    else:
                        self.app.set_mensaje(MSG_NO_HAY_CLAVES)
                else:
                    self.app.set_mensaje(response_mesg)
            elif response_auth == 0:
                self.app.set_mensaje(MSG_WRONG_PASS)
            else:
                self.app.set_mensaje(response_mesg)
        except urllib2.HTTPError:
            self.app.set_mensaje(MSG_ERROR_COMUNICACION)


class Preferencias(object):
    def __init__(self, config):
        self.config = config
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndPreferencias = self._widget_tree.get_widget('wndPreferencias')
        self._txtHostServidor = self._widget_tree.get_widget('txtHostServidor')
        self._txtHostServidor.set_text(self.config.HOST)
        self._txtHostDescargaCerts = self._widget_tree.get_widget('txtHostDescargaCerts')
        self._txtHostDescargaCerts.set_text(self.config.HOST_CERTS)
        self._txtTimeout = self._widget_tree.get_widget('txtTimeout')
        self._txtTimeout.set_text(self.config.TIMEOUT)

        # Configuro los selectores de archivos Keys y Certs
        self._flcKey = self._widget_tree.get_widget('flcKey')
        self._flcKey.select_filename(self.config.KEY_FILE)
        self._flcKey.set_current_folder(join(os.getcwd(), PATH_KEYS))
        self._flcKey.set_title(MSG_ARCHIVO_CLAVE)
        pkey_filter = gtk.FileFilter()
        pkey_filter.add_pattern(PATTERN_PKEY)
        self._flcKey.set_filter(pkey_filter)

        self._flcSigned = self._widget_tree.get_widget('flcSigned')
        self._flcSigned.select_filename(self.config.CERT_FILE)
        self._flcSigned.set_current_folder(os.path.join(os.getcwd(),
                                                        PATH_CERTS))
        self._flcSigned.set_title(MSG_ARCHIVO_CERT)
        cert_filter = gtk.FileFilter()
        cert_filter.add_pattern(PATTERN_CERT)
        self._flcSigned.set_filter(cert_filter)

        self._flcCA = self._widget_tree.get_widget('flcCA')
        self._flcCA.select_filename(self.config.CA_FILE)
        self._flcCA.set_current_folder(os.path.join(os.getcwd(), PATH_CA))
        self._flcCA.set_title(MSG_ARCHIVO_CA)
        cert_filter = gtk.FileFilter()
        cert_filter.add_pattern(PATTERN_CERT)
        self._flcSigned.set_filter(cert_filter)
        # Configuro los eventos a los que voy a responder
        eventos = {"on_btnAceptar_clicked": self.aceptar}
        self._widget_tree.signal_autoconnect(eventos)

    def aceptar(self, widget):
        self.config.set_option('host', self._txtHostServidor.get_text())
        self.config.set_option('host_certs', self._txtHostDescargaCerts.get_text())
        self.config.set_option('timeout', self._txtTimeout.get_text())
        key_file = self._flcKey.get_filename()
        cert_file = self._flcSigned.get_filename()
        ca_file = self._flcCA.get_filename()
        if key_file:
            self.config.set_option('key_file', key_file)
        if cert_file:
            self.config.set_option('cert_file', cert_file)
        if ca_file:
            self.config.set_option('ca_file', ca_file)
        self.config.write_options()

        dialog = gtk.MessageDialog(self._wndPreferencias, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE,
                                   MSG_DEBE_REINICIAR)
        dialog.run()
        dialog.destroy()

    def mostrar(self):
        self._wndPreferencias.run()
        self._wndPreferencias.hide()


class ImportarClaves(object):
    def __init__(self, config):
        self.config = config
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndImportarClaves = self._widget_tree.get_widget(
            'wndImportarClaves')

        self._wndImportarClaves.set_default_response(gtk.RESPONSE_OK)

        _filter = gtk.FileFilter()
        _filter.set_name("Archivos Comprimidos")
        _filter.add_mime_type("application/x-gzip")
        _filter.add_pattern(PATTERN_TAR_GZ)
        _filter.add_pattern(PATTERN_TGZ)
        _filter.add_pattern(PATTERN_GZ)
        self._wndImportarClaves.add_filter(_filter)
        # Configuro los eventos a los que voy a responder
        eventos = {"on_btnAceptar_clicked": self.aceptar}
        self._widget_tree.signal_autoconnect(eventos)

    def aceptar(self, widget):
        tar_filename = self._wndImportarClaves.get_filename()
        faltan_archivos, archivos_danados = importar_claves(tar_filename,
                                                            self.config)

        self._wndImportarClaves.hide()
        if faltan_archivos:
            msg = MSG_FALTAN_CERTIFICADOS
            tipo_msg = gtk.MESSAGE_ERROR
        elif archivos_danados:
            msg = MSG_CERTIFICADOS_DANADOS
            tipo_msg = gtk.MESSAGE_ERROR
        else:
            msg = MSG_CLAVES_IMPORTADAS
            tipo_msg = gtk.MESSAGE_INFO
        dialog = gtk.MessageDialog(self._wndImportarClaves, gtk.DIALOG_MODAL,
                                   tipo_msg, gtk.BUTTONS_CLOSE, msg)
        dialog.run()
        dialog.destroy()

    def mostrar(self):
        self._wndImportarClaves.run()
        self._wndImportarClaves.hide()


class BotonColor(gtk.EventBox):
    """ Clase que compone un gtk.Button pero facilita configurarle color de
    frente y de fondo """

    def __init__(self, titulo='Botón', color_fondo='#0000ff',
                 color_frente='#000000'):
        """ Constructor.
            Argumentos:
            texto -- El texto a mostrar en el botón (default 'Botón')
            color_fondo -- El color de fondo del botón (default '#0000ff')
            color_frente -- El color de la fuente del botón (default '#ffffff')
        """
        gtk.EventBox.__init__(self)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color_fondo))
        self.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(color_frente))

        if titulo is None:
            gtk.EventBox.add(self, self.fondo)
        else:
            lbl_titulo = gtk.Label()
            lbl_titulo.set_markup(titulo)
            lbl_titulo.modify_fg(gtk.STATE_NORMAL,
                                 gtk.gdk.color_parse('#000000'))

            self._boton = gtk.Button()
            self._boton.set_border_width(4)
            self._boton.add(lbl_titulo)
            self.add(self._boton)

    def connect(self, evento, controlador, *data):
        self._boton.connect(evento, controlador, *data)
