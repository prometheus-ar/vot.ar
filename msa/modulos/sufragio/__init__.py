"""
Modulo sufragio.
Permite almacenar e imprimir Boletas Únicas Electrónicas.
"""
from gi.repository.GObject import timeout_add, source_remove
from msa.core.documentos.boletas import Seleccion
from msa.core.exceptions import MesaIncorrecta
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_CONSULTANDO, E_ESPERANDO,
                                   E_EXPULSANDO_BOLETA, E_REGISTRANDO,
                                   E_VOTANDO, MODULO_INICIO, MODULO_SUFRAGIO)
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.sufragio.constants import (PANTALLA_INSERCION_BOLETA,
                                            PANTALLA_MENSAJE_FINAL,
                                            TIEMPO_POST_IMPRESION,
                                            TIEMPO_VERIFICACION)
from msa.modulos.sufragio.controlador import Controlador
from msa.modulos.sufragio.rampa import Rampa
from msa.modulos.sufragio.registrador import Registrador


class Modulo(ModuloBase):

    """
        Modulo de votacion.

        Espera a que se aproxime un tag, si esta vacio permite votar, sino
        muestra el contenido del tag.

        Si durante cualquier momento de la votacion, se retira el tag, cancela
        la operacion y vuelve a la pantalla de espera.
    """

    @requiere_mesa_abierta
    def __init__(self, nombre):
        """Constructor"""
        self.set_controller()
        self.web_template = "sufragio"
        ModuloBase.__init__(self, nombre)

        self.estado = None

        self.ret_code = MODULO_SUFRAGIO
        self._timeout_consulta = None
        self._consultando_tag = None

        self.registrador = Registrador(self._fin_registro, self, self._error)

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
            # Borramos el timeout de revisión de voto por las dudas de que
            # alguien inserte la boleta en blanco inmediatamente después de
            # revisar el voto, para evitar que la expulse. Esto el día de la
            # elección no tiene mucho sentido, pero para la capacitación sí.
            if self._timeout_consulta is not None:
                source_remove(self._timeout_consulta)
                self._timeout_consulta = None

            self.set_estado(E_VOTANDO)
            # Inicializamos una seleccion vacía para esta mesa.
            self.seleccion = Seleccion(self.sesion.mesa)
            # carga la pantalla inicial de votación. La UI sabe decidir qué
            # pantalla es
            self.controlador.send_command("cargar_pantalla_inicial")

    def set_pantalla(self, pantalla, image_data=None):
        """Establece la pantalla deseada."""
        #TODO: esto deberíamos deprecarlo, es overkill y tiene que ver con la
        # arquitectura que usaba todo con GTK
        self.controlador.set_screen(pantalla, image_data=image_data)

    def expulsar_boleta(self, motivo="sufragio"):
        """Expulsa la boleta."""
        self.rampa.tiene_papel = False
        self.set_estado(E_EXPULSANDO_BOLETA)
        self.rampa.expulsar_boleta(motivo)

    def salir(self, ret_code=MODULO_INICIO):
        """Sale del modulo y carga el siguiente.

        Argumentos:
            ret_code -- el modulo al cual queremos salir.
        """
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
        timeout_add(TIEMPO_POST_IMPRESION, _retornar)

    def _guardar_voto(self):
        """Guarda el voto."""
        if self.rampa.tiene_papel:
            # Cambiamos el estado a "registrando"
            self.set_estado(E_REGISTRANDO)
            # Efectivamente registramos (grabamos el chip e imprimimos el papel)
            self.registrador.registrar_voto()
            # Borramos explicitamente los datos del tag.
            self.rampa.datos_tag = None
        else:
            self.pantalla_insercion()

    def pantalla_insercion(self, cambiar_estado=True):
        """Muestra la pantalla de insercion de la boleta."""
        self.seleccion = None
        if cambiar_estado:
            self.set_estado(E_ESPERANDO)
        self.set_pantalla(PANTALLA_INSERCION_BOLETA)

    def hay_tag_vacio(self):
        """Arrancamos con la sesion de votacion."""
        self._comenzar()

    def _mostrar_consulta(self, tag):
        """Muestra la consulta de la boleta en pantalla.

        Argumentos:
            tag -- un objeto de tipo SoporteDigital.
        """
        # lo primero que hacemos es traer la seleccion por que si estamos
        # apoyando un voto de una mesa de otro juego de datos raisea una
        # excepcion de tipo MesaIncorrecta
        seleccion = Seleccion.desde_tag(tag.datos, self.sesion.mesa)

        # mostramos la pantalla vacía de consulta.
        self.controlador.consulta()
        self.set_estado(E_CONSULTANDO)
        # Guardamos el tag que estamos consultando para poder manejar el cambio
        # de tag o la continuidad de la consulta de mejor manera.
        self._consultando_tag = tag
        # Mostramos los candidatos de la boleta en pantalla.
        self.controlador.candidatos_consulta(seleccion)

    def _consultar(self, tag):
        """Permite al elector consultar una boleta.

        Parametros:
            tag -- un objeto de clase SoporteDigital.
        """
        # Borramos el timeout de consulta por las dudas
        if self._timeout_consulta is not None:
            source_remove(self._timeout_consulta)
            self._timeout_consulta = None

        try:
            # En caso de que el tag sea distinto del consultado mostramos la
            # consulta. No refrescamos si es el mismo para que no "titile" la
            # pantalla, que quedaba feo en voto <= 3.6
            if tag != self._consultando_tag:
                self._mostrar_consulta(tag)
                tiempo_verificacion = TIEMPO_VERIFICACION
            else:
                # si el tag es el mismo quiere decir que estan verificando mas
                # tiempo, pero como no queremos que quede mucho tiempo en
                # pantalla seteamos el timeout en 1/3 del tiempo original
                tiempo_verificacion = TIEMPO_VERIFICACION / 3

            self._timeout_consulta = timeout_add(tiempo_verificacion,
                                                 self._fin_consulta)
        except MesaIncorrecta:
            self.logger.debug("El tag corresponde a una mesa de otro juego.")
            self.expulsar_boleta("juego_datos")
        except Exception as err:
            self.expulsar_boleta("excepcion")
            self.logger.error("ocurrió un error al parsear el tag.")
            self.logger.error(err)

    def _fin_consulta(self):
        """Fin de la rutina de consulta de boleta."""
        # borramos la referencia al timeout
        self._timeout_consulta = None
        # si en vez de apoyar la boleta metieron la boleta en la rampa la
        # expulsamos
        if self.rampa.tiene_papel:
            self._consultando_tag = None
            self.expulsar_boleta("fin_consulta")
        else:
            # vuelvo a leer explicitamente el tag por que puede nunca llegar el
            # evento de inventario vacio y nos tenemos que asegurar de que si
            # no hay tag desaparezca el mensaje.
            self.rampa.tag_leido = self.rampa.get_tag()
            if self.rampa.tag_leido is None:
                # si no hay mas tag apoyado salimos
                self._consultando_tag = None
                self.pantalla_insercion()
            else:
                # Si todavia estan verificando vamos a consultar de nuevo
                self._consultar(self._consultando_tag)

        return False

    def document_ready(self):
        """Inicializamos cuando el browser tira el evento de document ready."""
        # Mandamos las constantes que el modulo necesita para operar.
        self.controlador.send_constants()
        # llamamos al maestro de ceremonias de la rampa para que evalúe como
        # proceder
        self.rampa.maestro()

    def menu_salida(self):
        """Muestra el menú que nos permite salir o abrir asistida."""
        self.controlador.menu_salida()

    def hide_dialogo(self):
        """Oculta el dialogo."""
        self.controlador.hide_dialogo()

    def _error(self, cambiar_estado=True):
        """ Función de error, si el guardado de la boleta fue erróneo,
            se muestra un mensaje acorde.
        """
        self.logger.debug("Error tag no guardado o no impreso")
        # Hacemos un ruido para que el elector preste atención y que las
        # autoridades esten al tanto de un posible problema al emitir la boleta
        self.play_sonido_error()
        self.rampa.tiene_papel = False
        # Mostramos la pantalla de insercion para ocultar la selección de
        # candidatos que hizo el elector y así evitar que cualquier otra
        # persona pueda verlo
        self.pantalla_insercion(cambiar_estado)

        def aceptar_error():
            """Cuando el usuario hace click en aceptar expulsamos la boleta."""
            self.rampa.expulsar_boleta("acepta_error")
        # Mostramos el popup de error el la UI
        self.controlador.cargar_dialogo("msg_error_grabar_boleta",
                                        aceptar=aceptar_error)
