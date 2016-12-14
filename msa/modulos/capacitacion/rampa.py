"""Rampa del modulo capacitacion."""
from time import sleep

from msa.core.rfid.constants import (TAG_CAPACITACION, TAG_PRESIDENTE_MESA,
                                     TAG_VOTO)
from msa.modulos.base.rampa import RampaBase, semaforo
from msa.modulos.constants import (E_CONSULTANDO, E_EN_CONFIGURACION,
                                   E_ESPERANDO, MODULO_CAPACITACION)


class RampaCapacitacion(RampaBase):

    """La Rampa especializada para el modulo de capacitacion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.datos_tag is not None and self.datos_tag['tipo'] == TAG_VOTO:
            if self.modulo.web_template != "capacitacion":
                self.modulo._consultar(self.datos_tag['datos'],
                                       self.datos_tag['serial'])
        elif self.tiene_papel:
            controlador = self.modulo.controlador
            if controlador.nombre == MODULO_CAPACITACION:
                if controlador.estado == E_EN_CONFIGURACION:
                    if self.datos_tag is not None:
                        sleep(1)
                        controlador.hide_dialogo()
                        self.modulo.imprimir_boleta()
                    else:
                        controlador.hide_dialogo()
                        controlador.cargar_dialogo("error_impresion_boleta")
                        self.expulsar_boleta()
                else:
                    self.expulsar_boleta()
            else:
                self.modulo.hay_tag_vacio()
        elif self.modulo.estado not in (E_CONSULTANDO, E_ESPERANDO):
            self.modulo.pantalla_insercion()

    def tag_admin(self, datos_tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        if datos_tag is not None and datos_tag['tipo'] in (
                TAG_CAPACITACION, TAG_PRESIDENTE_MESA):
            self.modulo.salir()
