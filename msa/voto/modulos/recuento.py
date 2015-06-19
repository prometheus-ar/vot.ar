# -*- coding: utf-8 -*-
"""Implementa clases para hacer el circuito del recuento de votos.
"""

import gobject
import time
from urllib2 import quote

from msa.constants import COD_TOTAL
from msa.core import get_config
from msa.core.clases import Recuento, Seleccion, Apertura
from msa.core.rfid.constants import TAG_VOTO, TAG_RECUENTO, TAG_VACIO
from msa.core.settings import DESPLAZAMIENTO_BOLETA, USA_ARMVE
from msa.voto.constants import MODULO_INICIO, \
    MODULO_RECUENTO, RECUENTO_OK, RECUENTO_ERROR, \
    RECUENTO_ERROR_REPETIDO, RECUENTO_NO_TAG, RECUENTO_GENERANDO, \
    E_INICIAL, E_SETUP, E_RECUENTO, E_RESULTADO, E_VERIFICACION, E_MESAYPIN, \
    E_INGRESO_ACTA, E_INGRESO_DATOS
from msa.voto.controllers.interaccion import ControllerInteraccion
from msa.voto.controllers.recuento import ControllerRecuento
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaRecuento
from msa.voto.print_manager import PrintManager
from msa.voto.sesion import get_sesion
from msa.voto.settings import MINIMO_BOLETAS_RECUENTO, USAR_CEF


sesion = get_sesion()
# Hilo Global del módulo para reproducir sonidos
_audio_player = None


class ModuloRecuento(Modulo):
    """ Modulo de Recuento de votos.

        Este módulo permite hacer el recuento de votos de una mesa.
        El usuario debe pasar el tag a ser utilizado para el recuento de la
        mesa, y a continuacion debe pasar todas las boletas por el lector.
        El sistema va a totalizarlas y una vez que el usuario confirme el
        cierre de la mesa, emite un listado con la cantidad de copias
        indicadas.

    E_INICIAL = 0
    E_SETUP = 1
    E_RECUENTO = 2
    E_RESULTADO = 3
    E_VERIFICACION = 4
    """
    controller_recuento = ControllerRecuento

    def __init__(self):
        """Constructor"""
        self.send_function = None
        # El primer controller es ControllerInteraccion porque es el que maneja
        # el ingreso de datos de mesa y pin y autoridades
        self.web_template = "recuento"
        self._cargar_controller_interaccion()
        self.es_modulo_web = True
        Modulo.__init__(self)
        self.ret_code = MODULO_RECUENTO
        self.estado = E_INICIAL
        self._intento = 0
        self._ui_web_activa = True  # Flag que indica si esta activa la ui web
        self.apertura = None
        """
        if USA_ARMVE:
            power_source = sesion.powermanager.get_power_source()
            if power_source is not None and not power_source['byte']:
                sesion.fancoolers.set_fan_auto_mode(False)
                sesion.fancoolers.set_fan_speed(100)
        """
        self.rampa = RampaRecuento(self)

    def _cargar_controller_interaccion(self):
        self.controller = ControllerInteraccion(self)

    def _cargar_ui_web(self):
        Modulo._cargar_ui_web(self)

    def _cargar_ui_recuento(self):
        Modulo._cargar_ui_web(self)
        self.ventana.show_all()

    def reiniciar_modulo(self):
        if self.rampa.tiene_papel and self.estado == E_SETUP:
            pass
        else:
            self.estado = E_INICIAL
            self.controller.estado = E_INGRESO_ACTA
            self.controller._inicializa_pantalla()

    def _inicio(self):
        """ Funcion llamada desde el controller una vez que se encuentra lista
            la interfaz web
        """
        self.controller.set_panel_estado(RECUENTO_NO_TAG)

        if self.estado == E_RECUENTO:
            #self.controller.set_pantalla_recuento()
            pass
        elif self.estado == E_VERIFICACION:
            self.print_manager.callback = self.print_manager.reset_copias
            sesion.recuento.autoridades = None
            #self.controller.set_pantalla_revision()

    def procesar_tag(self, tag_dict):
        """ Evento. Procesa el tag recibido por parametro. Cumple la funcion
            del procesar_tag() de PantallaRecuento de recuento Gtk.

            Argumentos:
            tag   -- El objeto TAG recibido.
            datos -- Los datos almacenados en el tag recibido.

            Si el tag no es ICODE se descarta el evento.
            Si su tipo no es voto, o está vacío, se devuelve error.
            Se intenta sumar los datos al recuento, si devuelve False
            es porque el tag ya fue sumado, sino está ok.
        """
        if self.estado == E_RECUENTO:
            serial = tag_dict.get('serial')
            tipo_tag = tag_dict.get('tipo')
            datos = tag_dict.get('datos')
            if None in (serial, tipo_tag, datos) or tipo_tag != TAG_VOTO:
                self.controller.set_panel_estado(RECUENTO_ERROR)
            else:
                self.controller.hide_dialogo()
                try:
                    seleccion = Seleccion.desde_tag(datos,
                                                    sesion.mesa)
                    if not sesion.recuento.serial_sumado(serial):
                        sesion.recuento.sumar_seleccion(seleccion, serial)
                        sesion.recuento.hora_fin = time.time()
                        sesion.ultima_seleccion = seleccion

                        # Dibujo boleta
                        imagen = seleccion.a_imagen(verificador=False,
                                                    solo_mostrar=True,
                                                    svg=True)
                        image_data = quote(imagen.encode("utf-8"))

                        cant_leidas = sesion.recuento.boletas_contadas()
                        self.controller.actualizar_resultados(
                            sesion.ultima_seleccion, cant_leidas, image_data)
                        gobject.timeout_add(200,
                                            self.controller.set_panel_estado,
                                            RECUENTO_OK)
                    else:
                        self.controller.set_panel_estado(
                            RECUENTO_ERROR_REPETIDO)
                except Exception as e:
                    print(e)
                    self.controller.set_panel_estado(RECUENTO_ERROR)
        elif self.controller.__class__.__name__ == "ControllerInteraccion":
            read_only = tag_dict.get("read_only")
            if self.rampa.tiene_papel and not read_only and self.estado not in \
                    (E_SETUP, E_VERIFICACION) and tag_dict['tipo'] in \
                    (TAG_VACIO, [0, 0]):
                self.estado = E_SETUP
                self.controller.estado = E_MESAYPIN
                self.controller.set_pantalla()
                self.posicion_recuento()
            elif self.estado in E_INICIAL and tag_dict['tipo'] == TAG_RECUENTO:
                sesion.recuento = Recuento.desde_tag(tag_dict['datos'])
                sesion.mesa = sesion.recuento.mesa

                def _inner():
                    if hasattr(self.controller, "set_mensaje"):
                        self.controller.set_mensaje(_("cargando_recuento"))
                    gobject.timeout_add(4000, self.revision_recuento)
                    if self.rampa.tiene_papel:
                        self.rampa.expulsar_boleta()
                gobject.timeout_add(1000, _inner)

            else:
                def _expulsar():
                    if self.rampa.tiene_papel and self.rampa.datos_tag and self.estado != E_SETUP:
                        self.controller.set_mensaje(_("acta_contiene_informacion"))
                        self.rampa.expulsar_boleta()
                gobject.timeout_add(300, _expulsar)

    def _show_pantalla_inicial(self):
        self.controller._inicializa_pantalla()

    def set_print_manager(self, callback):
        self.print_manager = PrintManager(self, callback)

    def revision_recuento(self):
        self.estado = E_VERIFICACION
        if not USAR_CEF:
            self._descargar_ui_web()
        self.controller = self.controller_recuento(self)
        self.set_print_manager(self.controller
                               .set_pantalla_impresion_certificados)
        self.print_manager.callback = self.print_manager.reset_copias
        self._cargar_ui_recuento()
        #self.controller.set_pantalla_impresion_certificados()
        #self.habilitar_impresion_certificados()
        self.copiar_certificados()
        sesion.impresora.remover_consultar_tarjeta()
        if USA_ARMVE:
            self.rampa.registrar_nuevo_papel(
                self._impresion_copias_certificados)
        else:
            self.rampa.remover_nuevo_papel()
            sesion.impresora.registrar_insertando_papel(
                self._impresion_copias_certificados)

    def ingreso_papel(self):
        self.estado = E_SETUP

    def posicion_recuento(self):
        if USA_ARMVE:
            sesion.impresora.linefeed(DESPLAZAMIENTO_BOLETA * 4)
        else:
            sesion.impresora.backfeed(DESPLAZAMIENTO_BOLETA)

    def guardar_datos_del_presidente(self, autoridades, hora):
        """
        Recibe un instancia de Presidente de Mesa, con los datos que cargo el
        usuario.
        """
        #sesion.impresora.remover_consultar_tarjeta()
        sesion.recuento = Recuento(sesion.mesa, autoridades, hora)
        sesion.mesa = sesion.recuento.mesa
        self.estado = E_RECUENTO
        if not USAR_CEF:
            self._descargar_ui_web()
        self.controller = self.controller_recuento(self)
        self.set_print_manager(self.controller.set_pantalla_asistente_cierre)
        # Cargamos la interfaz web, lo que inicia la pantalla recuento.
        self._cargar_ui_recuento()

    def ver_acta_de_cierre(self):
        """  Callback de salida del estado de recuento, es cuando el usuario
        presiona 'Terminar escrutinio'."""
        self.estado = E_RESULTADO
        self.controller.set_pantalla_confirmacion()

    def _finalizar(self):
        """ Funcion llamada desde el controller cuando se desea finalizar el
        recuento"""
        if sesion.recuento.boletas_contadas() < MINIMO_BOLETAS_RECUENTO:
            mensaje = {
                "alerta": _("pocas_boletas_alerta") % MINIMO_BOLETAS_RECUENTO,
                "pregunta": _("pocas_boletas_pregunta"),
                "aclaracion": _("pocas_boletas_aclaracion")}
            self.show_dialogo(mensaje=mensaje,
                              btn_cancelar=True,
                              btn_aceptar=True,
                              callback_aceptar=self.ver_acta_de_cierre,
                              callback_cancelar=None)
        else:
            self.ver_acta_de_cierre()

    def _imprimir(self):
        """ Pide confirmación del usuario para guardar e imprimir los
        resultados mostrados """

        mensaje = {"pregunta": _("esta_seguro_acta_cierre")}
        self.show_dialogo(mensaje=mensaje,
                          btn_cancelar=True,
                          btn_aceptar=True,
                          callback_aceptar=self._iniciar_impresion,
                          callback_cancelar=self.controller.cancelar_impresion)

    def _iniciar_impresion(self):
        """ Realiza las ultimas operaciones sobre el recuento antes de comenzar
            la impresion
        """

        def pre_impresion(tipo_acta):
            self.controller.mostrar_imprimiendo(tipo_acta)
            self.controller.hide_dialogo()

        def esperando_papel(tipo_acta):
            self.controller.pedir_acta(tipo_acta[0])

        self.rampa.expulsar_boleta()
        self.print_manager.imprimir_secuencia(
            False, pre_impresion, waiting_paper_callback=esperando_papel)

    def _lee_tag(self):
        """ Función para obtener un tag y devolver sus datos o vacío """
        if USA_ARMVE:
            tag = self.rampa.datos_tag
        else:
            tag = sesion.lector.get_tag()
        try:
            datos = tag['datos']
        except:
            datos = ''
        return datos

    def set_campos_extra(self, campos_recuento):
        for lista in get_config("listas_especiales"):
            sesion.recuento.actualizar_lista_especial(lista,
                                                      campos_recuento[lista])

    def get_campos_extra(self):
        campos_extra = []
        campos_extra.append({"codigo": "",
                             "titulo": _("boletas_procesadas"),
                             "editable": False,
                             "valor": sesion.recuento.boletas_contadas()})

        for lista in get_config("listas_especiales"):
            campos_extra.append(
                {"codigo": lista,
                 "titulo": _("titulo_votos_%s" % lista[-3:]),
                 "editable": True,
                 "valor": sesion.recuento.listas_especiales[lista]})

        total = 0
        for campo in campos_extra:
            total += campo.get('valor', 0)
        campos_extra.append({"codigo": COD_TOTAL,
                             "titulo": _("total_general"),
                             "editable": False,
                             "valor": total})
        return campos_extra

    def copiar_certificados(self):
        """  Callback de salida del estado de recuento, es cuando el usuario
        comienza la copia de certificados."""
        self.estado = E_RESULTADO
        self.print_manager.callback = self.print_manager.reset_copias
        self.controller.set_pantalla_impresion_certificados()
        self.habilitar_impresion_certificados()

    def habilitar_impresion_certificados(self):
        if USA_ARMVE:
            self.rampa.registrar_nuevo_papel(
                self._impresion_copias_certificados)
        else:
            sesion.impresora.registrar_insertando_papel(
                self._impresion_copias_certificados)

    def _impresion_copias_certificados(self, datos_sensores):
        self.controller.deshabilitar_botones()
        self.controller.set_panel_estado(RECUENTO_GENERANDO)

        def _inner():
            tag = self.rampa.datos_tag
            if not tag:
                if self.estado == E_RESULTADO:
                    # Si estoy imprimiendo certificados extra despues de un
                    # recuento completo seteo los callback para dar
                    # feedback

                    def pre_impresion(tipo_acta):
                        pass

                    def post_impresion(tipo_acta):
                        pass

                    def esperando_papel(tipo_acta):
                        pass

                    self.print_manager.imprimir_secuencia(True,
                                                          pre_impresion,
                                                          post_impresion,
                                                          esperando_papel)
                else:
                    # En otro caso (levanto un recuento ya grabado) solo
                    # mando a imprimir la secuencia.
                    self.print_manager.imprimir_secuencia(True)
            else:
                self.rampa.expulsar_boleta()
                self.controller.habilitar_botones()
                self.controller.limpiar_panel_estado()
                mensaje = {"alerta": _("certificado_no_impreso_alerta"),
                            "aclaracion": _(
                                "certificado_no_impreso_aclaracion")}
                self.show_dialogo(mensaje=mensaje, btn_aceptar=True)

        gobject.timeout_add(200, _inner)

    def cargar_apertura(self, tag_dict):
        apertura = Apertura.desde_tag(tag_dict['datos'])
        if (self.controller.estado == E_INGRESO_DATOS and
                sesion.mesa.numero == apertura.mesa.numero) or \
                self.controller.estado != E_INGRESO_DATOS:
            self.apertura = apertura
            self.controller.set_pantalla({"mesa": apertura.mesa.numero})

    def salir(self):
        """ Sale del módulo de recuento, vuelve al comienzo con la maquina
        desconfigurada."""
        mensaje = {"pregunta": _("seguro_salir_recuento")}
        self.show_dialogo(mensaje=mensaje,
                          btn_aceptar=True,
                          btn_cancelar=True,
                          callback_aceptar=self.quit,
                          callback_cancelar=None,
                          error=False)

    def quit(self, w=None):
        #self._stop_audio()
        self.ret_code = MODULO_INICIO
        #self._descargar_ui_web()
        Modulo.quit(self)

    def mensaje_inicial(self):
        if hasattr(self.controller, "mensaje_inicial"):
            self.controller.mensaje_inicial()

    def volver(self, admin=False, tag=None, datos_tag=None):
        """ Callback para volver del estado de resultado al de recuento y
        seguir recontando votos."""
        if admin is True or self.estado == E_RECUENTO:
            self.administrador()
        else:
            self.estado = E_RECUENTO
            self.controller.set_pantalla_recuento()
            if tag is not None and datos_tag is not None:
                self._tag_disponible(self.TAG_DATOS, tag, datos_tag)

    def administrador(self, callback_ok=None, callback_cancel=None):
        mensaje = {"pregunta": _("seguro_salir_recuento")}
        self.show_dialogo(mensaje=mensaje,
                          btn_aceptar=True,
                          btn_cancelar=True,
                          callback_aceptar=self.salir_a_administrador,
                          callback_cancelar=None)

    def salir_a_administrador(self):
        if self._ui_web_activa:
            self._descargar_ui_web()
            #self._cargar_ui()
        self.rampa.desregistrar_eventos()
        sesion.recuento = None
        self.rampa.expulsar_boleta()
        self._stop_audio()
        self.admin()

    def _stop_audio(self):
        global _audio_player
        if _audio_player is not None:
            _audio_player.stop()

    def show_dialogo(self, mensaje=None, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=None,
                     btn_aceptar=None, error=True):
        self.controller.show_dialogo(mensaje, callback_cancelar,
                                     callback_aceptar, btn_cancelar,
                                     btn_aceptar, error=error)
