"""Rampa para el modulo Inicio."""
from msa.core.rfid.constants import TAG_ADMIN
from msa.modulos.base.rampa import RampaBase, semaforo


class Rampa(RampaBase):

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
            # si es capacitacion validamos que haya capacitacion, si hay
            # capacitacion entramos al modulo, sino no hacemos nada
            if tag.es_capacitacion():
                if (self.modulo.config("usar_capacitacion") and
                        self.sesion.modo_demo):
                    self.modulo.a_capacitacion()
                # si es un tag de capacitacion pero no esta habilitada la
                # capacitacion o estamos en el disco de la eleccion no hacemos
                # nada
            else:
                # Si es un tag admin que no es capacitacion vamos a configurar
                # la mesa
                self.modulo.configurar(tag)
        else:
            # si es otra cosa por las dudas expulsamos, por si metieron una
            # boleta o acta
            self.expulsar_boleta()
