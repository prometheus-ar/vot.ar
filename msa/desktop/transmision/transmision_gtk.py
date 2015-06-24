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

from base64 import b64decode
from ojota import set_data_source
from os.path import join

from msa.constants import ESTADO_OK, ESTADO_PUBLICADA
#from msa.core.clases import Recuento
from msa.desktop.transmision.common import (
    AcercaDe, Autenticacion, ImportarClaves, Preferencias, BotonColor)
from msa.desktop.transmision.constants import (
    MSG_BIG_SI, MSG_BIG_NO, MSG_BIG_SPAN_COLOR,
    MSG_BIG_SPAN, MSG_BIG_SPAN_ALERT,
)
from msa.desktop.transmision.helpers import (
    bloqueante, desbloqueante, mostrar_espera, get_desktop_path,
    actualizar_datos)
from msa.desktop.transmision.settings import (
    PATH_NETWORK_CONF_APP, PROTOCOLO, DEBUG)

from msa.desktop.transmision.core import TransmisionCore


class TransmisionApp(TransmisionCore):

    def __init__(self, hw_init=True):
        TransmisionCore.__init__(self, hw_init)
        self.multi_test = False

        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndPrincipal = self._widget_tree.get_widget('wndPrincipal')
        self._lblMensajePantalla = self._widget_tree.get_widget(
            'lblMensajePantalla')
        self._vbox_acta = self._widget_tree.get_widget('vbox_acta')
        self._vbox_pendientes = self._widget_tree.get_widget('vbox_pendientes')
        self._widget_vport = self._widget_tree.get_widget('vp_acta')
        self._status = self._widget_tree.get_widget('status')
        self._lbl_mesas = self._widget_tree.get_widget('lbl_mesas')

        eventos = {
            "on_wndPrincipal_delete":
                self.gtk_cb_salir,
            "on_tlbSalir_clicked":
                self.gtk_cb_salir,
            "on_mnuArchivoSalir_activate":
                self.gtk_cb_salir,
            "on_mnuAyudaAcercaDe_activate":
                self.gtk_cb_mostrar_acerca_de,
            "on_mnuAccionesRed_activate":
                self.gtk_cb_configurar_red,
            "on_mnuAccionesImportar_activate":
                self.gtk_cb_mostrar_importar_claves,
            "on_tblPreferencias_clicked":
                self.gtk_cb_mostrar_preferencias,
            "on_tlbConectar_clicked":
                self.gtk_cb_conectar,
            "on_tblConfigurarRed_clicked":
                self.gtk_cb_configurar_red,
            "on_tblImportarCert_clicked":
                self.gtk_cb_mostrar_importar_claves,
            "on_tlbBajarCert_clicked":
                self.gtk_cb_mostrar_autenticacion,
        }
        self._widget_tree.signal_autoconnect(eventos)

    def gtk_cb_conectar(self, btn):
        self.conectar()

    def gtk_cb_mostrar_autenticacion(self, menuitem):
        autenticacion = Autenticacion(self.config, self)
        autenticacion.mostrar()

    def mostrar(self):
        if not DEBUG:
            self._wndPrincipal.maximize()
        self._wndPrincipal.show()

    def gtk_cb_mostrar_acerca_de(self, menuitem):
        acerca_de = AcercaDe(self.config)
        acerca_de.mostrar()

    def gtk_cb_mostrar_preferencias(self, menuitem):
        preferencias = Preferencias(self.config)
        preferencias.mostrar()

    def gtk_cb_mostrar_importar_claves(self, menuitem):
        wnd_importar_claves = ImportarClaves(self.config)
        wnd_importar_claves.mostrar()

    def gtk_cb_configurar_red(self, *args):
        try:
            subprocess.Popen(PATH_NETWORK_CONF_APP, shell=False)
        except OSError as e:
            self.logger.error(MSG_ERROR_CONF_APP % str(e.message))

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

    def cb_actualizacion_estado(self, status):
        pass

    def cb_actualizacion_informacion(self, text, idle=False, color=None,
                                     alerta=''):
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

        if self.multi_test:
            p = re.compile(r'<.*?>')
            self.logger.debug(">>> " + p.sub('', text))

    def get_mensaje(self):
        """ Obtiene el string de la pantalla, sin el pango markup """
        return self._lblMensajePantalla.get_text()

    def agregar_mensaje(self, text, idle=False):
        mensaje = self.get_mensaje() + '\n' + text
        if idle:
            gobject.idle_add(self._lblMensajePantalla.set_label, mensaje)
        else:
            self._lblMensajePantalla.set_label(mensaje)

    def _confirmar_transmision(self, w=None, ev=None, datos_tag=None):
        respuesta_conf = self._conexion.confirmar_acta(datos_tag)
        if respuesta_conf.status_ok() and 'acta_definitiva' in respuesta_conf:
            # Descargo y muestro el definitivo
            #self._descargar_y_guardar_acta(respuesta_conf)
            self.cb_actualizacion_informacion(MSG_BOLD % respuesta_conf['mensaje'],
                             idle=True, color=self.COLOR_OK)
            self._quitar_mesa(respuesta_conf['mesa'])
            self.cb_actualizacion_mesas()
            if datos_tag in self.borradores:
                self.borradores.remove(datos_tag)
        else:
            self.cb_actualizacion_informacion(MSG_ERROR_BOLD % respuesta_conf['mensaje'],
                             idle=True, color=self.COLOR_ERR)
        self._elimimar_vista_acta()

    def _cancelar_confirmacion(self, w=None, ev=None):
        self.cb_actualizacion_informacion(MSG_CONFIRMACION_CIERRE_CANCELADA, idle=True,
                         color=self.COLOR_OK)
        gobject.idle_add(self._elimimar_vista_acta)

    def _quitar_mesa(self, id_mesa):
        nuevos_estados = []

        for estado in self._estados_mesas:
            data_mesa = estado[0]
            if data_mesa[2].strip() != id_mesa[5:].strip():
                nuevos_estados.append([data_mesa] + estado[1:])

        self._estados_mesas = nuevos_estados

    def cb_actualizacion_mesas(self):
        """
        Callback para que la UI actualice la información de las mesas.
        """
        if not self.mesas():
            print "Sin información de mesas."
            # TODO: Achicar el panel de mesas.
        else:
            self._vbox_pendientes.set_visible(True)
            mesas = self.mesas()
            lbls_mesas = []
            for id_ubicacion in sorted(mesas.iterkeys()):
                mesa = mesas[id_ubicacion]
                if mesa['estado'] not in (ESTADO_OK, ESTADO_PUBLICADA):
                    actas = "".join([("<b>%s</b>" % cargo[1])
                                     for cargo in mesa['cargos']])
                    
                    lbl = "Mesa %s%s%s" % \
                        (mesa['numero'],
                         actas if len(actas) else "", mesa['estado'])
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
            self.cb_actualizacion_informacion(MSG_GENERANDO_IMG)

            imagen = recuento.a_imagen(svg=True, de_muestra=True,
                                       tipo=(CIERRE_TRANSMISION,
                                             recuento.cod_categoria))
            path_destino = join(get_desktop_path(),
                "%s_%s.svg" % (recuento.mesa.numero, recuento.cod_categoria))
            file_destino = open(path_destino, 'w')
            file_destino.write(imagen)
            file_destino.close()
            self._mostrar_acta(path_destino)
            self.cb_actualizacion_informacion(MSG_RESTO_ACTAS)

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

    def gtk_cb_salir(self, *args):
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
        self.desconectar()
        gtk.main_quit()


if __name__ == '__main__':
    gtk.gdk.threads_init()
    app = TransmisionApp()
    app.mostrar()
    gtk.main()
