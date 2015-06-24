#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import subprocess
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import urllib

from argparse import ArgumentParser
from hashlib import sha256
from json import load
from os import system
from time import sleep
from zaguan import Zaguan, WebContainerController

from msa.constants import ESTADO_ESPERA, ESTADO_PRIMERA_CARGA
from msa.desktop.transmision.core import TransmisionCore
from msa.desktop.transmision.constants import (
    MSG_ERROR_CONF_APP, MSG_CONFIRMACION_CIERRE_CANCELADA,
    MSG_ATENCION_NO_CONFIRMADAS, MSG_INICIO, MSG_PANTALLA_ESTADOS,
    MSG_PANTALLA_DIAGNOSTICO)
from msa.desktop.transmision.settings import (
    PATH_NETWORK_CONF_APP, DEBUG, PATH_TEMPLATE_TRANSMISION, FULLSCREEN)
from msa.desktop.transmision.common import (
    AcercaDe, Autenticacion, ImportarClaves, Preferencias)


multi_test = False


class TransmisionApp(TransmisionCore, WebContainerController):

    def __init__(self, modo_local=False, hw_init=True):
        TransmisionCore.__init__(self, modo_local, hw_init)
        WebContainerController.__init__(self)
        self._widget_tree = gtk.glade.XML(self.config.GLADE_FILE)
        self._wndPrincipal = self._widget_tree.get_widget('wndPrincipal')
        self._mesa_activa = None
        self._datos_tag = None
    ##
    # Sobreescritura de métodos de TransmisionCore
    ##

    def esperando_evento(self, esperando, idle=False):
        """
        Muestra al usuario actividad indicando que se esta procesando algo.
        """
        self.web_cargando(esperando)

    def cb_actualizacion_mesas(self, activa=None):
        """
        Callback para que la UI actualice la información de las mesas.
        """
        lbls_mesas = []
        mesas = self.mesas()
        pendientes = 0
        if mesas is not None:

            def _sort_mesas(key):
                return int(key.split(".")[-1])

            for id_ubicacion in sorted(mesas.iterkeys(), key=_sort_mesas):
                mesa = mesas[id_ubicacion]

                if mesa['estado'] in (ESTADO_ESPERA, ESTADO_PRIMERA_CARGA):
                    pendientes += 1

                actas = [("Mesa&nbsp;%s" % mesa['numero'], mesa['estado'])]
                actas += [(cargo['descripcion'], cargo['estado'])
                          for cargo in
                          sorted(mesa['cargos'].values(),
                                 key=lambda x: x['nro_orden'])]

                lbls_mesas.append(actas)

                if id_ubicacion == activa:
                    self._mesa_activa = "Mesa&nbsp;%s" % mesa['numero']
        self.send_command("planillas_pendientes", (pendientes,
                          len(lbls_mesas) > 0))
        self.send_command("estado_mesas", lbls_mesas)

        if self._mesa_activa is not None:
            self.send_command("set_mesa_activa", self._mesa_activa)

    def cb_actualizacion_estado(self, status):
        """
        Callback de actualización de estados
        """
        self.web_set_status(status)

    def cb_actualizacion_informacion(self, text, idle=False, color=None,
                                     alerta=''):
        """
        Callback para el envio de información a mostrar al usuario.
        """
        self.set_mensaje(text)
        self.logger.info(text)
        self._eliminar_vista_acta()

    def cb_confirmacion(self, datos_tag):
        # Elimino la mesa activa para luego, cuando se ingrese la opción de
        # si/no confirmar el recuento, no se siga mostrando como activa
        self._mesa_activa = None
        self.web_mostrar_confirmacion_recuento(datos_tag)

    def cb_mostrar_acta(self, lista_imagenes, usar_pestana=False):
        # Como ahora es una lista, debo codificar cada imagen con urllib
        for datos_categ in lista_imagenes:
            datos_categ[3] = urllib.quote(datos_categ[3].encode('utf-8'))

        self.send_command("mostrar_acta", lista_imagenes)

    def cb_actualizar_opciones(self, lista):
        self.send_command("actualizar_botones", lista)

    def cb_perdida_conexion(self):
        self.web_limpiar_ui()

    def cb_fin_prueba_estados(self, datos_prueba):
        self.send_command("actualizar_estado_prueba", datos_prueba)

    def cb_reiniciar_vista_confirmacion(self):
        self._eliminar_vista_confirmacion()

    ##
    # Métodos de interacción pura con la UI
    ##

    def web_document_ready(self, menuitem):
        self.set_mensaje(MSG_INICIO)

    def web_conectar(self, toolbutton):
        self.conectar()

    def web_desconectar(self, toolbutton):
        self.desconectar_red()
        self.web_limpiar_ui()
        self.set_mensaje(MSG_INICIO)

    def web_set_status(self, status):
        self.send_command("set_status", status)

    def web_set_mesa_activa(self, mesa):
        self.send_command("set_mesa_activa", mesa)

    def set_mensaje(self, text, idle=False, color=None, alerta=''):
        if multi_test:
            p = re.compile(r'<.*?>')
            self.logger.debug(">>> " + p.sub('', text))
        self.send_command("set_message", [text.replace("\n", "<br>")])

    def web_mostrar_autenticacion(self, menuitem):
        autenticacion = Autenticacion(self.config, self)
        autenticacion.mostrar()

    def web_mostrar(self):
        if not DEBUG:
            self._wndPrincipal.maximize()
        self._wndPrincipal.show()

    def web_mostrar_acerca_de(self, menuitem):
        acerca_de = AcercaDe(self.config)
        acerca_de.mostrar()

    def web_mostrar_preferencias(self, menuitem):
        preferencias = Preferencias(self.config)
        preferencias.mostrar()

    def web_mostrar_importar_claves(self, menuitem):
        wnd_importar_claves = ImportarClaves(self.config)
        wnd_importar_claves.mostrar()

    def web_configurar_red(self, *args):
        try:
            subprocess.Popen(PATH_NETWORK_CONF_APP, shell=False)
        except OSError as e:
            self.logger.error(MSG_ERROR_CONF_APP % str(e.message))

    def web_mostrar_confirmacion_recuento(self, datos_tag):
        datos_hasheados = sha256(datos_tag).hexdigest()
        self._datos_tag = (datos_hasheados, datos_tag)
        self.send_command("mostrar_confirmacion", datos_hasheados)

    def web_salir(self, *args):
        borradores = [m['id_planilla'] for m in self._estados_mesas.values()
                      if m['estado'] == ESTADO_PRIMERA_CARGA]
        if len(borradores) > 0:
            msg = MSG_ATENCION_NO_CONFIRMADAS % len(borradores)
            dialog = gtk.MessageDialog(self._wndPrincipal, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_INFO, gtk.BUTTONS_OK_CANCEL,
                                       msg)
            dialog.connect('response', self._respuesta_salir)
            dialog.run()
            dialog.destroy()
        else:
            self._salir_definitivo()

    def _respuesta_salir(self, dialog, response, data=None):
        if response == gtk.RESPONSE_OK:
            self._salir_definitivo()

    def _salir_definitivo(self):
        self.desconectar()
        gtk.main_quit()

    def web_boton_si(self, data):
        datos_hasheados, datos_tag = self._datos_tag
        if datos_hasheados == data:
            self.confirmar_recuento(datos_tag)
            self._eliminar_vista_acta()
            self._datos_tag = None

    def web_boton_no(self, data):
        self._cancelar_confirmacion()

    def _eliminar_vista_acta(self):
        self.send_command("hide_vista_acta")

    def _eliminar_vista_estados(self):
        self.send_command("hide_vista_estados")

    def _eliminar_vista_confirmacion(self):
        self.send_command("ocultar_confirmacion")

    def web_limpiar_ui(self):
        self.send_command("limpiar_ui")

    def _cancelar_confirmacion(self, w=None, ev=None):
        self.set_mensaje(MSG_CONFIRMACION_CIERRE_CANCELADA, idle=True,
                         color=self.COLOR_OK)
        gobject.idle_add(self._eliminar_vista_acta)

    def web_pantalla_status(self, data):
        self.set_mensaje(MSG_PANTALLA_ESTADOS)
        pruebas = self.verificar_estado()
        self.send_command("cargar_pruebas", pruebas)

    def web_get_status(self, data):
        self.verificar_estado()

    def web_cargando(self, cargando=True):
        self.send_command("cargando", cargando)

    def web_salir_pantalla_status(self, data):
        self.cb_actualizacion_mesas()

    def web_pantalla_diagnostico(self, data):
        self.set_mensaje(MSG_PANTALLA_DIAGNOSTICO)
        self.diagnostico()

    def _get_aplicaciones(self):
        with open('aplicaciones.cfg', 'r') as file:
            return load(file)

    def web_pantalla_aplicaciones(self, data):
        aplicaciones = self._get_aplicaciones()
        self.send_command("pantalla_aplicaciones", aplicaciones)

    def web_run_app(self, app):
        self.logger.info('Iniciando aplicación: %s', app)
        system(app + ' &')


class Ventana(Zaguan):
    def run_gtk(self, settings=None, window=None, debug=False):
        gtk.gdk.threads_init()

        if window is None:
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window.set_size_request(1366, 700)
        else:
            self.window = window

        browser = self.controller.get_browser(self.uri, debug=debug,
                                              settings=settings)
        self.window.connect("delete-event", self.quit)
        self.window.set_border_width(0)
        self.window.add(browser)
        sleep(1)
        browser.show_all()
        self.window.show()
        self.window.show_all()
        if FULLSCREEN:
            self.window.fullscreen()
        gtk.main()

if __name__ == "__main__":
    parser = ArgumentParser(description="Aplicación de transmisión")
    parser.add_argument('--local', action='store_true', help='Utiliza una '
                        'conexión falsa para realizar la transmisión.')
    args = parser.parse_args()
    uri = 'file://' + urllib.pathname2url(PATH_TEMPLATE_TRANSMISION)
    controller = TransmisionApp(modo_local=args.local)
    controller.add_processor("transmision")
    app = Ventana(uri, controller)
    configs = [
        ['enable-universal-access-from-file-uris', True],
        ['enable-accelerated-compositing', False],
    ]
    app.run(configs, on_close=controller.web_salir, debug=DEBUG)
