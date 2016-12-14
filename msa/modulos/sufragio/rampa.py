"""Rampa del modulo sufragio."""
from gi.repository.GObject import timeout_add
from msa.core.rfid.constants import (TAG_APERTURA, TAG_PRESIDENTE_MESA,
                                     TAG_RECUENTO, TAG_VACIO, TAG_VOTO)
from msa.modulos.base.rampa import RampaBase, semaforo
from msa.modulos.constants import E_CONSULTANDO, E_ESPERANDO, E_REGISTRANDO


class Rampa(RampaBase):

    """La Rampa especializada para el modulo de votacion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None:
            if self.datos_tag['tipo'] == TAG_VOTO:
                self.modulo._consultar(self.datos_tag['datos'],
                                       self.datos_tag['serial'])
            elif self.tiene_papel and self.datos_tag['tipo'] == TAG_VACIO:
                self.modulo.hay_tag_vacio()
            elif self.datos_tag['tipo'] in (TAG_APERTURA, TAG_RECUENTO):
                self.expulsar_boleta()
            elif self.modulo.estado != E_ESPERANDO:
                self.modulo.pantalla_insercion()
        elif self.tiene_papel:
            def _expulsar():
                self.datos_tag = self.sesion.lector.get_tag()
                if self.tiene_papel and self.datos_tag is None:
                    self.modulo.pantalla_insercion()
                    self.expulsar_boleta()
            timeout_add(300, _expulsar)

        elif self.modulo.estado not in (E_REGISTRANDO, E_CONSULTANDO,
                                        E_ESPERANDO):
            self.modulo.pantalla_insercion()

    def tag_admin(self, datos_tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        if datos_tag is not None and datos_tag['tipo'] == TAG_PRESIDENTE_MESA:
            self.modulo.play_sonido_warning()
            self.modulo.menu_salida()
