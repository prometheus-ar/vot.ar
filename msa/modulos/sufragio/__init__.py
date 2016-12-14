"""Modulo sufragio.
Permite almacenar e imprimir Boletas Únicas Electrónicas.
"""
from gi.repository.GObject import timeout_add
from msa.core.documentos.boletas import Seleccion
from msa.core.logging.settings import LOG_CAPTURE_STDOUT
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_CONSULTANDO, E_ESPERANDO,
                                   E_EXPULSANDO_BOLETA, E_REGISTRANDO,
                                   E_VOTANDO, MODULO_INICIO, MODULO_SUFRAGIO)
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.sufragio.constants import (PANTALLA_INSERCION_BOLETA,
                                            PANTALLA_MENSAJE_FINAL)
from msa.modulos.sufragio.controlador import Controlador
from msa.modulos.sufragio.rampa import Rampa
from msa.modulos.sufragio.registrador import Registrador


class Modulo(ModuloBase):

    """
        Modulo de votacion.

        Espera a que se aproxime un tag, si esta vacio permite votar, sino
        muestra el contenido del tag.

        Si durante cualquier momento del voto, se retira el tag, cancela
        la operacion y vuelve a la pantalla de inicio.
    """

    @requiere_mesa_abierta
    def __init__(self, nombre):
        """Constructor"""
        self.set_controller()
        self.web_template = "sufragio"
        ModuloBase.__init__(self, nombre)
        if LOG_CAPTURE_STDOUT:
            import sys
            from logging import INFO, ERROR
            from msa.core.logging import StreamToLogger
            sys.stdout = StreamToLogger(self.logger, INFO)
            sys.stderr = StreamToLogger(self.logger, ERROR)

        self.estado = None

        self.ret_code = MODULO_SUFRAGIO
        self.volvera = None
        self._metiendo_papel = False

        self.registrador = Registrador(self._fin_registro, self, self._error)
        self.tiempo_verificacion = 5000

        self.rampa = Rampa(self)

    def set_estado(self, estado):
        """Setea el estado."""
        self.estado = estado

    def set_controller(self):
        """Establece el controlador."""
        self.controlador = Controlador(self)

    def _comenzar(self):
        """Inicializo la seleccion."""
        if self.estado != E_VOTANDO:
            self.set_estado(E_VOTANDO)
            self.seleccion = Seleccion(self.sesion.mesa, self.sesion.interna)
            self.controlador.send_command("cargar_pantalla_inicial")

    def set_pantalla(self, pantalla, image_data=None):
        """Establece la pantalla deseada."""
        self.controlador.set_screen(pantalla, image_data=image_data)

    def get_pantalla_inicial_voto(self):
        """Muestra la pantalla inicial que ve el usuario al meter la boleta."""
        if self.config("seleccionar_idioma"):
            self.controlador.set_pantalla_idiomas()
        else:
            self.controlador.get_pantalla_modos()

    def expulsar_boleta(self):
        """Expulsa la boleta."""
        self.rampa.tiene_papel = False
        self.set_estado(E_EXPULSANDO_BOLETA)
        self.expulsar_boleta()

    def salir(self, ret_code=MODULO_INICIO):
        self.salir_a_modulo(ret_code)

    def _fin_registro(self):
        """Se llama cuando se termina de registrar un voto."""
        self.logger.info("Se muestra la pantalla de mensaje final")
        self.estado = E_ESPERANDO
        self.set_pantalla(PANTALLA_MENSAJE_FINAL)
        self.rampa.tiene_papel = False

        def _retornar():
            """Retorna a la pantalla de insercion de voto."""
            self.logger.info("Se llamó a la funcion retornar")
            if self.estado not in (E_CONSULTANDO, E_VOTANDO, E_REGISTRANDO):
                self.pantalla_insercion()

        # Se muestra el mensaje de agradecimiento durante 6 segundos
        timeout_add(6000, _retornar)

    def _guardar_voto(self):
        """Guarda el voto."""
        if self.rampa.tiene_papel:
            # Cambiamos el estado a "registrando"
            self.set_estado(E_REGISTRANDO)
            # Efectivamente registramos (grabamos el chip e imprimimos el papel)
            self.registrador._registrar_voto()
            # Borramos explicitamente los datos del tag.
            self.rampa.datos_tag = None
        else:
            self.pantalla_insercion()

    def pantalla_insercion(self):
        """Muestra la pantalla de insercion de la bolet."""
        self.seleccion = None
        self.set_estado(E_ESPERANDO)
        self.set_pantalla(PANTALLA_INSERCION_BOLETA)

    def hay_tag_vacio(self):
        """Arrancamos con la sesion de votacion."""
        self._comenzar()

    def _consultar(self, datos_tag, serial, force=False):
        """Cuando se apolla una boleta con datos. Mostramos el contenido."""
        # si no estamos ya consultando un voto o no forzamos la muestra.
        if self.estado != E_CONSULTANDO or force:
            # si ese tag tiene datos
            if datos_tag is not None and len(datos_tag) > 0:
                def _fin():
                    """Se llama en el final de la consulta."""
                    if self.estado == E_CONSULTANDO:
                        sigue = False
                        # Si el papel esta insertado se expulsa, sin embargo
                        # si está apoyada el acta hacemos que siga consultando
                        # nuevamente
                        if self.rampa.tiene_papel:
                            self.rampa.expulsar_boleta()
                        else:
                            tag = self.sesion.lector.get_tag()
                            if tag is not None:
                                # ok, vamos de nuevo por que la persona esta
                                # todavia chequeando. lo forzamos para que
                                # renueve
                                sigue = True
                                self._consultar(tag['datos'], tag['serial'],
                                                True)
                        if not sigue:
                            # reseteo el estado del tag por si no me llega el
                            # evento.
                            self.rampa.datos_tag = None
                            self.pantalla_insercion()

                seleccion_tag = None
                try:
                    seleccion_tag = Seleccion.desde_tag(datos_tag,
                                                        self.sesion.mesa)
                    if seleccion_tag is not None \
                            and not len(seleccion_tag.candidatos_elegidos()):
                        # Si el tag no esta vacio pero no tiene candidatos.
                        seleccion_tag = None
                    elif seleccion_tag is not None and \
                            seleccion_tag.serial != bytes(serial, "utf8"):
                        seleccion_tag = None
                except Exception as e:
                    # Esto maneja la instancia de que alguien quiera meter
                    # un voto que no cumple con las condiciones requeridas.
                    self.logger.error("La boleta no contiene datos validos")
                    self.logger.exception(e)
                    self.rampa.expulsar_boleta()
                    _fin()

                # Si el tag es validos arrancamos la consulta del voto.
                if seleccion_tag is not None:
                    self.set_estado(E_CONSULTANDO)
                    self.controlador.consulta(seleccion_tag)
                    timeout_add(self.tiempo_verificacion, _fin)
            else:
                # si la boleta que se ingresó no es un voto la expulsamos.
                self.rampa.expulsar_boleta()

    def document_ready(self):
        """Inicializamos cuando el browser tira el evento de document ready."""
        self.controlador.send_constants()
        self.rampa.maestro()

    def menu_salida(self):
        self.controlador.menu_salida()

    def hide_dialogo(self):
        """Oculta el dialogo."""
        self.controlador.hide_dialogo()

    def _error(self):
        """ Función de error, si el guardado de la boleta fue erróneo,
            se muestra un mensaje acorde.
        """
        self.rampa.tiene_papel = False
        self.pantalla_insercion()

        def aceptar_error():
            """Cuando el usuario hace click en aceptar expulsamos la boleta."""
            self.sesion.impresora.expulsar_boleta()

        self.controlador.cargar_dialogo("msg_error_grabar_boleta",
                                        aceptar=aceptar_error)
