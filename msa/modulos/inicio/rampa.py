"""Rampa para el modulo Inicio."""
from msa.core.rfid.constants import TAG_ADMIN, TAG_CAPACITACION
from msa.modulos.base.rampa import RampaBase, semaforo


class Rampa(RampaBase):

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
        if tipo_tag == TAG_ADMIN:
            if tag_dict['tipo'] == TAG_CAPACITACION:
                usar_capacitacion = self.modulo.config("usar_capacitacion")
                if usar_capacitacion:
                    self.modulo.a_capacitacion()
            else:
                self.modulo.configurar()
        else:
            self.expulsar_boleta()
