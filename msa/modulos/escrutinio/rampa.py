"""Rampa del modulo escrutinio."""
from msa.core.rfid.constants import TAG_COLISION, TAG_PRESIDENTE_MESA, TAG_VOTO
from msa.modulos.base.rampa import RampaBase
from msa.modulos.constants import E_IMPRIMIENDO


class Rampa(RampaBase):

    """
    Rampa que maneja las particularidades del modulo de recuento que es el mas
    complejo en cuanto a estados.
    """

    def maestro(self):
        if self.modulo.estado != E_IMPRIMIENDO:
            self.expulsar_boleta()

    def cambio_tag(self, tipo, tag_dict):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag

        """
        # solo proceso si es un evento de cambio de tag
        if tag_dict is not None:
            serial = tag_dict.get('serial')
            tipo_tag = tag_dict.get('tipo')
            datos = tag_dict.get('datos')

            if None not in (serial, tipo_tag, datos):
                if tipo_tag == TAG_VOTO:
                    self.modulo.procesar_voto(bytes(serial, "utf8"), tipo_tag,
                                              datos)
                elif tipo_tag == TAG_PRESIDENTE_MESA:
                    self.modulo.preguntar_salida()
                else:
                    # no es un voto
                    self.modulo.error_lectura()
            elif tipo == TAG_COLISION:
                self.modulo.error_lectura()
