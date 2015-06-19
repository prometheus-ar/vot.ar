# -*- coding: utf-8 -*-

import gobject

from base64 import b64decode
from json import loads

from msa.core.exceptions import MesaNoEncontrada
from msa.core.rfid.constants import TAG_COLISION, TAG_ADMIN, TAG_VACIO, \
    TAG_VOTO, TAG_USUARIO_MSA, TAG_APERTURA, NO_TAG, TAG_RECUENTO, TAG_DEMO, \
    TAG_DATOS
from msa.core.settings import USA_ARMVE
from msa.voto.constants import E_CARGA, E_INICIAL, E_VERIFICACION, \
    E_EN_CONFIGURACION, E_CONFIRMACION, E_SETUP, E_RECUENTO, \
    E_REGISTRANDO, E_CONSULTANDO, E_MESAYPIN, E_INGRESO_DATOS, E_ESPERANDO
from msa.voto.sesion import get_sesion


sesion = get_sesion()

corriendo = False


def semaforo(func):
    """Decorador que hace que no se puedan hacer 2 cosas al mismo tiempo.

    La idea es evitar las race conditions que teniamos con la rampa anterior.
    """
    def _inner(self, *args, **kwargs):
        global corriendo
        if not corriendo:
            corriendo = True
            func(self, *args, **kwargs)
            corriendo = False
    return _inner


class Rampa(object):

    """Rampa generica de la que heredan el resto de las rampas.

    Esta clase se encarga de manejar los estados de papel en la impresora y el
    estado de los chips.
    """

    def __init__(self, modulo):
        """Constructor de la clase de manejo de rampa.

        Argumentos:
            modulo -- referencia al modulo que maneja la rampa.
        """
        self.modulo = modulo
        self.desregistrar_eventos()
        self.registrar_eventos()
        # ojo que esto no verifica correctamente que tenga papel, no puedo
        # saber si está viendo el sensor solamente o ademas el papel estar
        # tomado pero este conocimiento es mejor que nada.
        if sesion.impresora is not None:
            self.tiene_papel = sesion.impresora.tiene_papel
        else:
            self.tiene_papel = False

        if sesion.lector is not None:
            self.datos_tag = sesion.lector.get_tag()
        else:
            self.datos_tag = None

    def cambio_sensor_1(self, data):
        """Callback que se corre cuando el sensor 1 se dispara.

        El evento que nos interesa es el que manda False en el sensor_1
        ya que nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['paper_out_1']

        if not sensor_1:
            self.tiene_papel = False
            self.maestro()
        elif not USA_ARMVE:  # malata fix
            sesion.impresora.tomar_tarjeta()
            self.tiene_papel = True
            self.maestro()

            def _expulsar():
                self.datos_tag = sesion.lector.get_tag()
                if self.tiene_papel and self.datos_tag is None:
                    self.expulsar_boleta()
                else:
                    self.maestro()
            gobject.timeout_add(1000, _expulsar)

    def cambio_sensor_2(self, data):
        """
        Callback que se corre cuando el sensor 2 se dispara.

        El evento que nos interesa es el que manda "0" ya que nos dice
        que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['paper_out_1']
        sensor_2 = data['paper_out_2']

        if not sensor_2 and sensor_1:
            self.tiene_papel = True
            self.maestro()

    def _cambio_tag(self, tipo_tag, tag_data=None):
        """
        Esto es un filtro que formatea el tag para que sea un diccionario y
        hace el base 64 decoding.

        Argumentos:
            tipo_tag -- el tipo de tag.
            tag_dict -- los datos crudos del tag.
        """
        tag_dict = None

        if tag_data is not None:
            datos = None
            tag_dict = loads(tag_data)

            if tag_dict is not None:
                if "datos" in tag_dict:
                    datos = b64decode(tag_dict['datos'])
                    tag_dict['datos'] = datos
        return self.cambio_tag(tipo_tag, tag_dict)

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- un diccionario con los datos del tag
        """
        if tipo_tag == TAG_COLISION:
            self.modulo.pantalla_insercion()
            self.tag_colision()
        elif tipo_tag == TAG_ADMIN:
            self.tag_admin()
        else:
            if tag_dict != self.datos_tag:
                self.datos_tag = tag_dict
                self.maestro()

    def tag_colision(self):
        """Metodo que se llama cuando se detecta colision."""
        self.expulsar_boleta()

    def expulsar_boleta(self):
        """Metodo de expulsion de boleta."""
        if False:
            from traceback import print_stack
            print_stack()
        sesion.logger.debug("EXPULSION dese modulo rampa")
        self.tiene_papel = False
        self.datos_tag = None
        sesion.impresora.expulsar_boleta()

    def tag_admin(self):
        """Metodo que se llama cuando se apoya un tag de admin."""
        self.desregistrar_eventos()
        if self.tiene_papel:
            self.expulsar_boleta()
        self.modulo.salir()

    def registrar_eventos(self):
        """Registra los eventos por default de la rampa."""
        imp = sesion.impresora
        lector = sesion.lector
        self._ev_lector = lector.consultar_lector(self._cambio_tag)
        self._ev_sensor_1 = imp.registrar_insertando_papel(
            self.cambio_sensor_1)
        self.registrar_nuevo_papel(self.cambio_sensor_2)

    def registrar_nuevo_papel(self, callback):
        imp = sesion.impresora
        self.remover_nuevo_papel()
        if USA_ARMVE:
            self._ev_sensor_2 = imp.registrar_autofeed_end(callback)
        else:
            self._ev_sensor_2 = imp.consultar_tarjeta(callback)

    def remover_nuevo_papel(self):
        imp = sesion.impresora
        if USA_ARMVE:
            imp.remover_autofeed_end()
        else:
            imp.remover_consultar_tarjeta()

    def desregistrar_eventos(self):
        """Desregistra los eventos por default de la rampa."""
        if sesion.lector is not None:
            sesion.lector.remover_consultar_lector()
        if sesion.impresora is not None:
            sesion.impresora.remover_insertando_papel()
            self.remover_nuevo_papel()


class RampaVoto(Rampa):

    """La Rampa especializada para el modulo de votacion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None:
            if self.datos_tag['tipo'] == TAG_VOTO:
                self.modulo._consultar(self.datos_tag['datos'])
            elif self.tiene_papel and self.datos_tag['tipo'] == TAG_VACIO:
                self.modulo.hay_tag_vacio()
            elif self.datos_tag['tipo'] in (TAG_APERTURA, TAG_RECUENTO):
                self.expulsar_boleta()
            elif self.modulo.estado != E_ESPERANDO:
                self.modulo.pantalla_insercion()
        elif self.tiene_papel:
            def _expulsar():
                self.datos_tag = sesion.lector.get_tag()
                if self.tiene_papel and self.datos_tag is None:
                    self.modulo.pantalla_insercion()
                    self.expulsar_boleta()
            if USA_ARMVE:
                gobject.timeout_add(300, _expulsar)

        elif self.modulo.estado not in (E_REGISTRANDO, E_CONSULTANDO,
                                        E_ESPERANDO):
            self.modulo.pantalla_insercion()


class RampaDemo(Rampa):

    """La Rampa especializada para el modulo de demo."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None and self.datos_tag['tipo'] == TAG_VOTO:
            self.modulo._consultar(self.datos_tag['datos'])
        elif self.tiene_papel:
            self.modulo.hay_tag_vacio()
        elif self.modulo.estado not in (E_CONSULTANDO, E_ESPERANDO):
            self.modulo.pantalla_insercion()


class RampaAdmin(Rampa):

    """La Rampa especializada para el modulo de administracion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.tiene_papel and not self.modulo.modo_mantenimiento:
            self.expulsar_boleta()

    def registrar_eventos(self):
        """Registra los eventos por default de la rampa."""
        imp = sesion.impresora
        lector = sesion.lector

        self._ev_lector = lector.consultar_lector(self._cambio_tag)
        self._ev_sensor_1 = imp.registrar_insertando_papel(
            self.cambio_sensor_1)
        if USA_ARMVE:
            self._ev_sensor_2 = imp.registrar_autofeed_end(self.cambio_sensor_2)
        else:
            self._ev_sensor_2 = imp.consultar_tarjeta(self.cambio_sensor_2)

        if USA_ARMVE:
            pwr_mgr = sesion.powermanager
            pir = sesion.pir

            self.signal_ac = pwr_mgr.check_ac(self.modulo._recheck_batteries)
            self.signal_batt_discharging = pwr_mgr.check_battery_discharging(
                self.modulo._recheck_batteries)
            self.signal_batt_plugged = pwr_mgr.check_battery_plugged(
                self.modulo._recheck_batteries)
            self.signal_batt_unplugged = pwr_mgr.check_battery_unplugged(
                self.modulo._recheck_batteries)
            self.signal_pir_detected = pir.check_detected(
                self.modulo._recheck_pir_detected)
            self.signal_pir_not_detected = pir.check_not_detected(
                self.modulo._recheck_pir_not_detected)

    def desregistrar_eventos(self):
        """desegistra los eventos por default de la rampa."""
        if sesion.lector is not None:
            sesion.lector.remover_consultar_lector()
        if sesion.impresora is not None:
            sesion.impresora.remover_insertando_papel()
            self.remover_nuevo_papel()
        if USA_ARMVE:
            if hasattr(self, "signal_ac") and self.signal_ac is not None:
                self.signal_ac.remove()
            if hasattr(self, "signal_batt_discharging") and \
                    self.signal_batt_discharging is not None:
                self.signal_batt_discharging.remove()
            if hasattr(self, "signal_batt_plugged") and \
                    self.signal_batt_plugged is not None:
                self.signal_batt_plugged.remove()
            if hasattr(self, "signal_batt_unplugged") and \
                    self.signal_batt_unplugged is not None:
                self.signal_batt_unplugged.remove()
            if hasattr(self, "signal_pir_detected") and \
                    self.signal_pir_detected is not None:
                self.signal_pir_detected.remove()
            if hasattr(self, "signal_pir_not_detected") and \
                    self.signal_pir_not_detected is not None:
                self.signal_pir_not_detected.remove()

            pwr_mgr = sesion.powermanager
            pwr_mgr.uncheck_ac()
            pwr_mgr.uncheck_battery_discharging()
            pwr_mgr.uncheck_battery_plugged()
            pwr_mgr.uncheck_battery_unplugged()
            sesion.pir.uncheck_detected()
            sesion.pir.uncheck_not_detected()

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.
        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        modo_mantenimiento = self.modulo.modo_mantenimiento
        boton_mantenimiento = self.modulo.boton_mantenimiento

        if not modo_mantenimiento:
            if tipo_tag == TAG_ADMIN and tag_dict['tipo'] == TAG_USUARIO_MSA:
                if boton_mantenimiento:
                    self.modulo._calibrar_pantalla()
                else:
                    self.modulo._show_maintenance_button()
            elif not self.modulo.mesa_abierta and tipo_tag == TAG_DATOS and \
                    tag_dict['tipo'] == TAG_APERTURA:
                datos_tag = tag_dict['datos']
                self.modulo._configurar_mesa(datos_tag)
            else:
                if self.tiene_papel:
                    self.expulsar_boleta()
        else:
            self.modulo.rfid_check(tag_dict)


class RampaActas(Rampa):

    """
    Rampa generica para el modulo de apertura y el cierre ya que ambos usan el
    controller de interacion y manejan de una manera similar la toma de papel.
    """

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None \
                and (self.tiene_papel or
                     self.datos_tag['tipo'] in (TAG_RECUENTO, [0, 0])):
            try:
                self.modulo.procesar_tag(self.datos_tag)
            except MesaNoEncontrada:
                sesion.impresora.expulsar_boleta()
        elif self.modulo.estado in (E_CARGA, E_CONFIRMACION, E_SETUP):
            self.modulo.reiniciar_modulo()
        elif self.modulo.estado == E_INICIAL and self.tiene_papel and \
                self.datos_tag is None:
            def _expulsar():
                if self.tiene_papel and self.datos_tag is None:
                    self.expulsar_boleta()
            gobject.timeout_add(1000, _expulsar)
        elif self.modulo.estado != E_REGISTRANDO:
            self.modulo.mensaje_inicial()


class RampaApertura(RampaActas):

    """
       Rampa que maneja las particularidades de deteccion de chip en el modulo
       de apertura.
    """

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.
        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        if tag_dict is not None:
            if tag_dict['tipo'] == TAG_APERTURA:
                datos_tag = tag_dict['datos']
                self.modulo._configurar_mesa(datos_tag)
            elif tipo_tag == TAG_ADMIN:
                self.tag_admin()
            elif tipo_tag == TAG_COLISION:
                self.expulsar_boleta()
                self.tag_colision()

        if tag_dict != self.datos_tag:
            self.datos_tag = tag_dict
            self.maestro()


class RampaRecuento(RampaActas):
    """Rampa que maneja las particularidades del modulo de recuento que es el
       mas complejo en cuanto a estados.
    """
    def cambio_sensor_1(self, data):
        """Callback que se corre cuando el sensor 1 se dispara.

        El evento que nos interesa es el que manda False en el sensor_1
        ya que nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['paper_out_1']

        if not sensor_1:
            self.tiene_papel = False
            self.maestro()
        elif not USA_ARMVE:  # malata fix
            sesion.impresora.tomar_tarjeta()
            self.tiene_papel = True
            if self.modulo.estado == E_RECUENTO:
                self.modulo.posicion_recuento()

    def cambio_sensor_2(self, data):
        """Callback que se corre cuando el sensor 2 se dispara.
        El evento que nos interesa es el que manda "0" en ambos sensores ya que
        nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['paper_out_1']
        sensor_2 = data['paper_out_2']

        if not sensor_2 and sensor_1:
            self.tiene_papel = True
            if USA_ARMVE and self.modulo.estado == E_RECUENTO:
                self.modulo.posicion_recuento()
            self.maestro()

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.
        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        if hasattr(self.modulo.controller, "estado"):
            estado_controller = self.modulo.controller.estado
        else:
            estado_controller = None

        if estado_controller == E_INICIAL:
            if tag_dict is not None and tag_dict['tipo'] == TAG_APERTURA:
                self.expulsar_boleta()
            elif tag_dict is not None and tag_dict['tipo'] == TAG_RECUENTO:
                self.modulo.estado = E_VERIFICACION
                self.modulo.procesar_tag(tag_dict)
            elif tipo_tag == NO_TAG:
                self._show_pantalla_inicial()
        elif tipo_tag == TAG_ADMIN:
            self.tag_admin()
        elif tipo_tag == TAG_COLISION and sorted(tag_dict['tipo']) == [0, 4]:
            self.expulsar_boleta()
        elif tipo_tag == TAG_COLISION and tag_dict['tipo'] \
                not in ([0, 0], [1, 1], [1], [0], []):
            self.tag_admin()
        elif estado_controller in (E_MESAYPIN, E_INGRESO_DATOS):
            if tag_dict is not None and tag_dict['tipo'] == TAG_APERTURA:
                self.modulo.cargar_apertura(tag_dict)

        if tag_dict != self.datos_tag:
            self.datos_tag = tag_dict
            self.maestro()

    def tag_admin(self):
        """Metodo que se llama cuando se apoya un tag de admin."""
        self.modulo.salir()


class RampaInicio(Rampa):

    """Rampa que controla el modulo inicio. """

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.tiene_papel:
            self.expulsar_boleta()

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.
        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        if self.modulo.estado == E_INICIAL:
            if tipo_tag == TAG_ADMIN:
                if tag_dict['tipo'] == TAG_DEMO:
                    self.modulo.a_demo()
                else:
                    self.modulo.configurar()
            elif tag_dict is not None and tag_dict['tipo'] == TAG_APERTURA:
                self.modulo.abrir_mesa(tag_dict['datos'])
            else:
                self.expulsar_boleta()
        elif self.modulo.estado == E_EN_CONFIGURACION:
            if tipo_tag == TAG_ADMIN:
                self.modulo.quit()
            elif tag_dict is not None and tag_dict['tipo'] == TAG_APERTURA:
                self.modulo.abrir_mesa(tag_dict['datos'])

        elif self.tiene_papel:
            self.expulsar_boleta()
