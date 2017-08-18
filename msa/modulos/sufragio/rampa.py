"""Rampa del modulo sufragio."""
from gi.repository.GObject import timeout_add
from msa.modulos.base.rampa import RampaBase, semaforo
from msa.modulos.constants import E_CONSULTANDO, E_ESPERANDO, E_REGISTRANDO


class Rampa(RampaBase):

    """La Rampa especializada para el modulo de votacion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        tag_leido = self.tag_leido
        # si tengo tag me fijo que tipo de tag es.
        if tag_leido is not None:
            if tag_leido.es_voto() and self.modulo.estado != E_REGISTRANDO:
                # si es un voto vamos a mostrarlo.
                self.modulo._consultar(tag_leido)
            elif self.tiene_papel and tag_leido.es_tag_vacio():
                # tengo papel y hay un tag_vacio, queremos votar.
                self.modulo.hay_tag_vacio()
                # refrescar y comprobar que el tag sea efectivamente el mismo:
                if self.tiene_conexion:
                    def _verificar_tag_leido(nuevo_tag):
                        """Callback en segundo plano para chequear el tag"""
                        if tag_leido != nuevo_tag:
                            self.sesion.logger.warning("No coincide TAG leido")
                            self.desregistrar_eventos()
                            self.tag_leido = None
                            self.reset_rfid()
                            self.registrar_eventos()
                            self.modulo.pantalla_insercion()
                            # expulsar para volver a comenzar correctamente:
                            timeout_add(2000, self.expulsar_boleta, "verif")
                        else:
                            self.sesion.logger.debug("TAG leido Verificado")
                    # esperar una fracción de segundo para actualizar UI:
                    _cb_read = lambda: self.get_tag_async(_verificar_tag_leido)
                    timeout_add(300, _cb_read)
            elif tag_leido.es_apertura() or tag_leido.es_recuento():
                self.expulsar_boleta("es apertura/recuento")
            elif self.modulo.estado != E_ESPERANDO:
                self.modulo.pantalla_insercion()
        elif self.tiene_papel:
            # reiniciar el RFID e Impresora preventivo
            self.sesion.logger.warning("Hay papel sin tag leido...")
            if self.modulo.estado != E_REGISTRANDO:
                self.reset_rfid()
            def _reevaluar():
                # si sigo teniendo papel puesto
                if self.tiene_papel:
                    # Le pido al service el contenido del tag
                    self.tag_leido = self.get_tag()
                    if self.tag_leido is None:
                        # si el tag no tiene datos muestro la pantalla de
                        # impresion y expulso la boleta
                        self.modulo.pantalla_insercion()
                        timeout_add(1000, self.expulsar_boleta, "reevaluar")
                    else:
                        # en caso contrario llamo de nuevo a la logica que
                        # evalúa que hacer con la boleta que estan metiendo
                        self.maestro()

            # espero cierto tiempo para volver a evaluar, ya que quizas el
            # papel está aun entrando.
            timeout_add(200, _reevaluar)
        elif self.modulo.estado not in (E_REGISTRANDO, E_CONSULTANDO,
                                        E_ESPERANDO):
            self.modulo.pantalla_insercion()

    def tag_admin(self, tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        if tag is not None and tag.es_autoridad():
            self.modulo.play_sonido_warning()
            self.modulo.menu_salida()

    def registrar_voto(self, seleccion, solo_impimir, aes_key, callback):
        # registra un voto en una BUE
        respuesta = self._servicio.registrar_voto(seleccion, solo_impimir,
                                                  aes_key, callback)
        return respuesta
