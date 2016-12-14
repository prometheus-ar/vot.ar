"""
Modulo base de las rampas.

maneja la interaccion entre la impresora y el lector y el usuario.
"""
from base64 import b64decode
from json import loads

from gi.repository import GObject

from msa.core.exceptions import MesaNoEncontrada
from msa.core.rfid.constants import (TAG_ADMIN, TAG_APERTURA, TAG_COLISION,
                                     TAG_PRESIDENTE_MESA, TAG_RECUENTO,
                                     TAG_VACIO, TAG_VOTO)
from msa.modulos import get_sesion
from msa.modulos.base.decorators import semaforo
from msa.modulos.constants import (E_CARGA, E_CONFIRMACION, E_INICIAL,
                                   E_REGISTRANDO, E_SETUP,
                                   SUBMODULO_DATOS_ESCRUTINIO)


class RampaBase(object):

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
        self.sesion = get_sesion()
        self.desregistrar_eventos()
        self.registrar_eventos()
        # ojo que esto no verifica correctamente que tenga papel, no puedo
        # saber si está viendo el sensor solamente o ademas el papel estar
        # tomado pero este conocimiento es mejor que nada.
        if self.sesion.impresora is not None:
            self.tiene_papel = self.sesion.impresora.tiene_papel
        else:
            self.tiene_papel = False

        if self.sesion.lector is not None:
            self.datos_tag = self.sesion.lector.get_tag()
        else:
            self.datos_tag = None

    def maestro(self):
        pass

    def cambio_sensor_1(self, data):
        """Callback que se corre cuando el sensor 1 se dispara.

        El evento que nos interesa es el que manda False en el sensor_1
        ya que nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['sensor_1']

        if not sensor_1:
            self.tiene_papel = False
            self.maestro()

    def cambio_sensor_2(self, data):
        """
        Callback que se corre cuando el sensor 2 se dispara.

        El evento que nos interesa es el que manda "0" ya que nos dice
        que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['sensor_1']
        sensor_2 = data['sensor_2']

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
                    datos = b64decode(bytes(tag_dict['datos'], "utf8"))
                    tag_dict['datos'] = datos
                    if tag_dict['tipo'] == TAG_PRESIDENTE_MESA:
                        salt_y_key = tag_dict['datos']
                        salt = salt_y_key[:40]
                        self.sesion.salt = salt
                        self.sesion.key_credencial = salt_y_key[24:]

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
            self.tag_admin(tag_dict)
        else:
            if tag_dict != self.datos_tag:
                self.datos_tag = tag_dict
                self.maestro()

    def tag_colision(self):
        """Metodo que se llama cuando se detecta colision."""
        self.expulsar_boleta()

    def expulsar_boleta(self):
        """Metodo de expulsion de boleta."""
        self.sesion.logger.debug("EXPULSION dese modulo rampa")
        self.tiene_papel = False
        self.datos_tag = None
        if self.sesion.impresora is not None:
            self.sesion.impresora.expulsar_boleta()

    def tag_admin(self, datos_tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        self.desregistrar_eventos()
        if self.tiene_papel:
            self.expulsar_boleta()
        self.modulo.salir()

    def registrar_eventos(self):
        """Registra los eventos por default de la rampa."""
        imp = self.sesion.impresora
        lector = self.sesion.lector
        if lector is not None:
            self._ev_lector = lector.consultar_lector(self._cambio_tag)
            self._ev_sensor_1 = imp.registrar_insertando_papel(
                self.cambio_sensor_1)
            self.registrar_nuevo_papel(self.cambio_sensor_2)

    def registrar_nuevo_papel(self, callback):
        """Registra el evento de nuevo papel."""
        imp = self.sesion.impresora
        self.remover_nuevo_papel()
        self._ev_sensor_2 = imp.registrar_autofeed_end(callback)

    def remover_nuevo_papel(self):
        """Remueve el evento de nuevo papel."""
        imp = self.sesion.impresora
        imp.remover_autofeed_end()

    def desregistrar_eventos(self):
        """Desregistra los eventos por default de la rampa."""
        if self.sesion.lector is not None:
            self.sesion.lector.remover_consultar_lector()
        if self.sesion.impresora is not None:
            self.sesion.impresora.remover_insertando_papel()
            self.remover_nuevo_papel()

    def registrar_boleta_expulsada(self, callback):
        self.sesion.impresora.registrar_boleta_expulsada(callback)

    def remover_boleta_expulsada(self):
        self.sesion.impresora.remover_boleta_expulsada()


class RampaActas(RampaBase):

    """
    Rampa generica para el modulo de apertura y el cierre ya que ambos usan el
    controlador de interacion y manejan de una manera similar la toma de papel.
    """

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None \
                and (self.datos_tag['tipo'] in (TAG_RECUENTO, [0, 0],
                                                TAG_VOTO, TAG_VACIO,
                                                TAG_APERTURA)):
            try:
                self.procesar_tag(self.datos_tag)
            except MesaNoEncontrada:
                self.expulsar_boleta()
        elif self.modulo.estado in (E_CARGA, E_CONFIRMACION, E_SETUP):
            if self.modulo.nombre != SUBMODULO_DATOS_ESCRUTINIO:
                self.modulo.reiniciar_modulo()
            else:
                self.expulsar_boleta()
        elif self.modulo.estado == E_INICIAL and self.tiene_papel and \
                self.datos_tag is None:
            def _expulsar():
                if self.tiene_papel and self.datos_tag is None:
                    self.expulsar_boleta()
            GObject.timeout_add(1000, _expulsar)
        elif self.modulo.estado != E_REGISTRANDO:
            self.modulo.mensaje_inicial()
