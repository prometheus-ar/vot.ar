# -*- coding: utf-8 -*-
"""Implementa clases para Iniciar/Configurar la maquina de voto.
"""
import cPickle
import hashlib
import gobject
import os
try:
    import keybinder
except ImportError:
    print('Keybinder no encontrado')

from os import system
from subprocess import Popen

from msa.core.clases import Apertura
from msa.core.data import Ubicacion
from msa.core.settings import USA_ARMVE
from msa.settings import DEBUG
from msa.voto.constants import MODULO_ADMIN, MODULO_INICIO, RESTART, \
    MODULO_DEMO, MODULO_CALIBRADOR, E_INICIAL, E_EN_CONFIGURACION, \
    E_CONFIGURADA, E_MESAYPIN
from msa.voto.gui.basegui import MsgDialog
from msa.voto.controllers.inicio import ControllerInicio
from msa.voto.controllers.interaccion import ControllerInteraccion
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaInicio
from msa.voto.sesion import get_sesion
from msa.voto.settings import DUMP_FILE_REINICIO, USAR_CEF


sesion = get_sesion()


class ModuloReinicio:

    """ Modulo de Reinicio.
        Esta clase sólo se encarga de devolver retornar shutdown pero
        persistiendo en un pickle en /tmp la mesa actual, para que cuando
        inicio arranque autoconfigure dicha mesa.
        Además, reinicia los servicios de DBus por cualquier inconveniente que
        ocurra y el chip ARM en caso de correr en dicha plataforma.
    """
    def main(self):


        """ Persisto configuración para levantar luego """
        if sesion.apertura:
            dump_file = open(DUMP_FILE_REINICIO, 'w')
            cPickle.dump(sesion.apertura.a_tag(), dump_file)
            dump_file.close()
        """ Reinicio sesión para después salir y entrar a la app """
        sesion.restart()
        return RESTART


class ModuloInicio(Modulo):

    """ Modulo de Inicio.

        Hereda de: ModuloLector

        Este módulo muestra la pantalla de bienvenida y realiza el proceso de
        configuracion de una mesa.
        El usuario debe pasar el tag de presidente o de MSA para habilitar el
        comienzo de la configuración.
        Luego se le pedirá un PIN y el modulo configurará la mesa para la
        ubicación solicitada.
    """

    def __init__(self):
        """Constructor"""
        # Importante antes de inicializar el modulo, limpiar la configuracion
        self._limpiar_configuracion()
        self.mute_armve_ver_1()
        self.controller = ControllerInicio(self)
        self.es_modulo_web = True
        self.web_template = "inicio"

        Modulo.__init__(self)

        self.ret_code = MODULO_INICIO
        self.loop_lector = True
        self._vaciar_impresora()
        self.estado = E_INICIAL
        self.dialogo = None
        self._bind_term()
        self.manejar_desconexion()

        self.rampa = RampaInicio(self)

        gobject.idle_add(self._dump_check)

    def mute_armve_ver_1(self):
        if USA_ARMVE:
            machine_number = sesion.agent.get_machine_type()
            if machine_number == 1:
                system('/usr/bin/amixer -c 0 sset "Auto-Mute Mode" Disabled')

    def _cargar_ui_inicio(self):
        Modulo._cargar_ui_web(self)
        self._inicio()
        self.controller.set_pantalla()
        self.ventana.show_all()

    def _bind_term(self):
        try:
            keybinder.bind('<Control><Alt>X', self.abrir_terminal)
        except (KeyError, NameError):
            pass

    def set_pantalla(self, pantalla):
        self.controller.set_screen(pantalla)

    def show_dialogo(self, mensaje=None, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=False,
                     btn_aceptar=False):
        self.controller.show_dialogo(mensaje, callback_cancelar,
                                     callback_aceptar, btn_cancelar,
                                     btn_aceptar)

    def hide_dialogo(self):
        self.controller.hide_dialogo()

    def _inicio(self):
        """ Funcion llamada desde el controller"""
        self.controller.send_constants()

    def manejar_desconexion(self):
        def mostrar_dialogo(estado):
            if not estado and self.dialogo is None:
                if USA_ARMVE:
                    self.dialogo = MsgDialog(_("arm_no_responde"),
                                             MsgDialog.WARNING, MsgDialog.OK,
                                             self.apagar)
                else:
                    self.dialogo = MsgDialog(_("impresora_desconectada"),
                                             MsgDialog.WARNING, MsgDialog.NONE)
                self.dialogo.show()
            elif estado and self.dialogo is not None:
                self.dialogo.hide()
                self.dialogo = None

        if sesion.impresora is None or not sesion.impresora.estado():
            mostrar_dialogo(False)

        if sesion.impresora is not None:
            sesion.impresora.connection(mostrar_dialogo)

    def _vaciar_impresora(self):
        impresora = sesion.impresora
        if impresora is not None and impresora.estado() and \
                impresora.tarjeta_ingresada():
            impresora.expulsar_boleta()

    def _pantalla_principal(self):
        self.controller.set_screen("pantalla_inicio")

    def a_demo(self):
        self.ret_code = MODULO_DEMO
        self.quit()

    def configurar(self):
        # Inicio la configuración de la mesa.
        if not USAR_CEF:
            self._descargar_ui_web()
        self.controller = ControllerInteraccion(self, E_MESAYPIN)
        self._cargar_ui_inicio()
        self.estado = E_EN_CONFIGURACION

    def abrir_mesa(self, datos_tag):
        apertura = Apertura.desde_tag(datos_tag)
        self._validar_configuracion(mesa=apertura.mesa.numero, pin=None,
                                    con_acta_apertura=True,
                                    datos_tag=datos_tag)

    def _validar_configuracion(self, mesa=None, pin=None,
                               con_acta_apertura=False, datos_tag=''):
        """ Recibe el numero de mesa y el pin de la pantalla de configuración y
            verifica que sea correcto.
            Si es *con_acta_apertura* se carga la mesa automaticamente y con
            datos tag carga los datos del presidente
            Si es correcto configura la mesa para dejarla operativa y pasa al
            menú de administración, en otro caso presenta la pantalla
            principal.
        """
        mesa_obj = Ubicacion.one(numero=mesa)

        if mesa_obj is not None and \
                (pin is not None and
                 hashlib.sha1(pin).hexdigest() == mesa_obj.pin or
                 con_acta_apertura):
            self._mesa = mesa_obj
            # Le seteo el atributo abierta si la configuracion de la mesa fue
            # con el acta de apertura
            self._configurar_mesa()
            if con_acta_apertura:
                apertura = Apertura.desde_tag(datos_tag)
                sesion.apertura = apertura
            self.estado = E_CONFIGURADA
            self.ret_code = MODULO_ADMIN
            if self.rampa.tiene_papel:
                self.rampa.expulsar_boleta()
            gobject.idle_add(self.quit)
        else:
            if sesion.lector is None:
                msg = _("error_conectar_lector")
            else:
                msg = _("mesa_pin_incorrectos")
            mensaje = {"aclaracion": msg}

            self.estado = E_INICIAL
            self.ventana.remove(self.ventana.children()[0])
            self._cargar_ui_web()
            self.ventana.show_all()
            self._pantalla_principal()
            self.show_dialogo(mensaje, btn_aceptar=True)

    def _configurar_mesa(self):
        # Configura la ubicacion actual del modulo.
        sesion.mesa = self._mesa

    def _limpiar_configuracion(self):
        # Reinicio todos los valores
        sesion.mesa = None
        sesion.apertura = None
        sesion.recuento = None

    def calibrar_pantalla(self):
        """ Sale del módulo de inicio y envia la orden de calibrar pantalla """
        self.ret_code = MODULO_CALIBRADOR
        self.quit()

    def _dump_check(self):
        """ Chequeo que el sistema no haya reiniciado previamente """
        if os.path.exists(DUMP_FILE_REINICIO):
            try:
                dump_file = open(DUMP_FILE_REINICIO, 'r')
                dump_data = cPickle.load(dump_file)
            except:
                pass
            else:
                apertura = Apertura.desde_tag(dump_data)
                if apertura.mesa is not None:
                    self._validar_configuracion(mesa=apertura.mesa.numero,
                                                pin=None,
                                                con_acta_apertura=True,
                                                datos_tag=dump_data)
            finally:
                dump_file.close()
                os.remove(DUMP_FILE_REINICIO)
        return False  # Se ejecuta una vez

    def apagar(self):
        """ Sale del módulo de inicio y envia la orden de apagado """
        self.ret_code = 'shutdown'
        gobject.idle_add(self.quit)

    def abrir_terminal(self):
        if DEBUG:
            sesion.logger.debug('abrir terminal')
            pop = Popen('xterm')

    def _btn_apagar_clicked(self, w=None):
        """ Llamo al callback para apagar la maquina en su totalidad.
        """
        mensaje = {"pregunta": _("esta_seguro_apagar")}
        self.show_dialogo(mensaje,
                          btn_aceptar=True,
                          btn_cancelar=True,
                          callback_aceptar=self.apagar,
                          callback_cancelar=None)
