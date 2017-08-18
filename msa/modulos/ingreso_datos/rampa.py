"""
    Rampas para el modulo ingreso de datos.
"""
from gi.repository.GObject import timeout_add

from msa.core.rfid.constants import TAG_ADMIN, TAG_COLISION
from msa.modulos.base.rampa import RampaBase, RampaActas, semaforo
from msa.modulos.constants import (E_RECUENTO, MODULO_INICIO)


class RampaInicio(RampaBase):

    """Rampa que controla el modulo inicio. """

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.tiene_papel:
            self.expulsar_boleta()

    def cambio_tag(self, tipo_lectura, tag):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_lectura -- el tipo de tag
            tag -- los datos del tag
        """
        if tipo_lectura == TAG_ADMIN:
            self.modulo.salir_a_modulo(MODULO_INICIO)
        elif self.tiene_papel:
            self.expulsar_boleta()


class RampaApertura(RampaActas):

    """
    Rampa que maneja las particularidades de deteccion de chip en el modulo
    de apertura.
    """

    def cambio_tag(self, tipo_lectura, tag):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_lectura -- el tipo de tag
            tag -- los datos del tag
        """
        if tag is not None:
            if tag.es_apertura():
                self.modulo.configurar_desde_apertura(tag)
            elif tipo_lectura == TAG_ADMIN:
                timeout_add(500, self.modulo.salir_a_modulo, MODULO_INICIO)
            elif tipo_lectura == TAG_COLISION:
                self.expulsar_boleta()
                self.tag_colision()

        if tag != self.tag_leido:
            self.tag_leido = tag
            self.maestro()

    def procesar_tag(self, tag):
        # Establecemos el "tiene papel" de nuevo porque hay una combinacion
        # rara de cosas que se puede dar en la que la rampa en este lugar puede
        # pensar que tiene papel cuando en realidad no lo tiene. Es una
        # combinacion medio rara pero merece ser contemplada.

        self.tiene_papel = self._servicio._estado_papel()
        self.modulo.procesar_tag_apertura(tag)


class RampaEscrutinio(RampaActas):

    """
    Rampa que maneja las particularidades del modulo de recuento que es el mas
    complejo en cuanto a estados.
    """

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
        """Callback que se corre cuando el sensor 2 se dispara.

        El evento que nos interesa es el que manda "0" en ambos sensores ya que
        nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['sensor_1']
        sensor_2 = data['sensor_2']

        if not sensor_2 and sensor_1:
            self.tiene_papel = True
            if self.modulo.estado == E_RECUENTO:
                self.expulsar_boleta()
            self.maestro()

    def cambio_tag(self, tipo_lectura, tag):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_lectura -- el tipo de tag
            tag -- los datos del tag
        """
        if tag is not None:
            if tag.es_apertura():
                self.modulo.cargar_apertura(tag)
            elif tipo_lectura == TAG_ADMIN:
                self.modulo.salir()
            elif tag.es_recuento():
                self.modulo.cargar_recuento_copias(tag)

    def procesar_tag(self, tag):
        pass
