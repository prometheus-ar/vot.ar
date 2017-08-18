"""Rampa del modulo capacitacion."""
from time import sleep

from msa.modulos.base.rampa import RampaBase, semaforo
from msa.modulos.constants import (E_CONSULTANDO, E_EN_CONFIGURACION,
                                   E_ESPERANDO, MODULO_CAPACITACION,
                                   E_REGISTRANDO)


class RampaCapacitacion(RampaBase):

    """La Rampa especializada para el modulo de capacitacion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        # si apoyan un voto
        if self.tag_leido is not None and self.tag_leido.es_voto():
            # si no estamos en el menu
            if self.modulo.web_template != "capacitacion":
                self.modulo._consultar(self.tag_leido)
            else:
                self.expulsar_boleta()
        # si hay papel puesto
        elif self.tiene_papel:
            controlador = self.modulo.controlador
            # Si el controlador es el de capacitacion y no el de sufagio
            if controlador.nombre == MODULO_CAPACITACION:
                # para cuando queremos imprimir un tag desde el menu
                if controlador.estado == E_EN_CONFIGURACION:
                    if(self.tag_leido is not None and
                       self.tag_leido.es_tag_vacio()):
                        sleep(1)
                        controlador.hide_dialogo()
                        self.modulo.imprimir_boleta()
                    else:
                        controlador.hide_dialogo()
                        controlador.cargar_dialogo(
                            "error_impresion_boleta",
                            aceptar=self.modulo.cancelar_impresion)
                        self.expulsar_boleta()
                else:
                    self.expulsar_boleta()
            # si meto un tag vacio en el con el controlador de sufagio y estoy
            # haciendo tiempo como si estuviera imprimiendo el voto
            elif self.modulo.estado != E_REGISTRANDO:
                self.modulo.hay_tag_vacio()
        # si no estamos en ningun estaddo de votacion vamos a mostar la
        # pantalla de insercion
        elif self.modulo.estado not in (E_CONSULTANDO, E_ESPERANDO):
            self.modulo.pantalla_insercion()

    def tag_admin(self, tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        if tag is not None and (tag.es_capacitacion() or tag.es_autoridad()):
            self.modulo.salir()

    def registrar_voto(self, seleccion, solo_impimir, aes_key, callback):
        respuesta = self._servicio.registrar_voto(seleccion, solo_impimir,
                                                  aes_key, callback)
        return respuesta
