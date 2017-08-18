"""Modulo para hacer Escrutinio y Cierre de Mesa."""
from datetime import datetime

from msa.core.audio.settings import VOLUMEN_ESCRUTINIO_P2, VOLUMEN_GENERAL
from msa.core.config_manager.constants import COMMON_SETTINGS
from msa.core.documentos.actas import Recuento
from msa.core.documentos.boletas import Seleccion
from msa.core.documentos.constants import CIERRE_COPIA_FIEL
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_IMPRIMIENDO, E_RECUENTO, MODULO_INICIO,
                                   MODULO_RECUENTO, SHUTDOWN)
from msa.modulos.decorators import requiere_mesa_abierta
from msa.modulos.escrutinio.constants import (ACT_BOLETA_NUEVA,
                                              ACT_BOLETA_REPETIDA, ACT_ERROR,
                                              ACT_VERIFICAR_ACTA,
                                              SECUENCIA_CERTIFICADOS)
from msa.modulos.escrutinio.controlador import Controlador
from msa.modulos.escrutinio.rampa import Rampa
from msa.modulos.escrutinio.registrador import SecuenciaActas


class Modulo(ModuloBase):
    """ Modulo de Recuento de votos.

        Este módulo permite hacer el recuento de votos de una mesa.
        El usuario debe pasar el tag a ser utilizado para el recuento de la
        mesa, y a continuacion debe pasar todas las boletas por el lector.
        El sistema va a totalizarlas y una vez que el usuario confirme el
        cierre de la mesa, emite un listado con la cantidad de copias
        indicadas.
    """

    @requiere_mesa_abierta
    def __init__(self, nombre):
        """Constructor"""
        self.web_template = "escrutinio"
        self.get_controller()
        ModuloBase.__init__(self, nombre)
        self._start_audio()
        self.apertura = self.sesion.apertura
        self.ret_code = MODULO_RECUENTO
        self.get_rampa()
        self.set_volume()
        if self.sesion.recuento is None:
            self.sesion.recuento = Recuento(self.sesion.mesa)
        self.estado = E_RECUENTO
        self.get_orden_certs()
        self.config_files = [COMMON_SETTINGS, nombre, "imaging"]
        self._load_config()

        self._ultimo_tag_leido = None
        self._hora_ultimo_tag = datetime.now()

    def set_volume(self):
        volumen = VOLUMEN_GENERAL
        if self.rampa.tiene_conexion:
            version = self.rampa.get_arm_version()
            if version == 1:
                volumen = VOLUMEN_ESCRUTINIO_P2
        self._player.set_volume(volumen)

    def get_orden_certs(self):
        self.orden_actas = SECUENCIA_CERTIFICADOS

    def get_controller(self):
        self.controlador = Controlador(self)

    def get_rampa(self):
        self.rampa = Rampa(self)

    def _inicio(self):
        """ Funcion llamada desde el controlador una vez que se encuentra lista
            la interfaz web
        """
        pass

    def beep(self, tipo_actualizacion):
        if tipo_actualizacion == ACT_BOLETA_NUEVA:
            self.play_sonido_ok()
        elif tipo_actualizacion == ACT_BOLETA_REPETIDA:
            self.play_sonido_warning()
        elif tipo_actualizacion == ACT_ERROR:
            self.play_sonido_error()

    def procesar_voto(self, tag):
        """Procesa un voto que se apoya. Actua en consecuencia.

        Argumentos:
            tag -- un objeto SoporteDigital
        """
        tipo_actualizacion = ACT_ERROR
        seleccion = None
        if self.estado == E_RECUENTO:
            try:
                # usamos el serial como unicidad, esto podría cambiar
                unicidad = tag.serial
                # Parseamos la seleccion
                seleccion = Seleccion.desde_tag(tag.datos, self.sesion.mesa)
                # A veces puede llegar mas de un evento de tag nuevo al mismo
                # tiempo, como es un factor humano dificil de manejar lo que
                # hacemos es no tirar dos eventos seguidos del mismo tag por
                # que las autoridades de mesa "se asustan" si ven un "boleta
                # repetida" inmediatamente despues de que apoyaron el tag de
                # una boleta nueva. Para evitar confusiones no procesamos la
                # boleta que se acaba de procesar y la pantalla no se refresca
                # si la ultima lectura de la misma boleta fue hace menos de un
                # segundo.
                delta = datetime.now() - self._hora_ultimo_tag
                if tag.serial != self._ultimo_tag_leido or delta.seconds > 0:
                        # Si el voto no fue ya contado se suma.
                    if not self.sesion.recuento.serial_sumado(unicidad):
                        self._sumar_voto(seleccion, unicidad)
                        tipo_actualizacion = ACT_BOLETA_NUEVA
                    else:
                        # En caso de estar ya somado se avisa y no se cuenta.
                        tipo_actualizacion = ACT_BOLETA_REPETIDA
                else:
                    tipo_actualizacion = None
            except Exception as e:
                # cualquier circunstancia extraña se translada en un error.
                print(e)
                seleccion = None

            if tipo_actualizacion is not None:
                self._ultimo_tag_leido = unicidad
                self._hora_ultimo_tag = datetime.now()
                self.controlador.actualizar(tipo_actualizacion, seleccion)

    def _sumar_voto(self, seleccion, unicidad):
        """Suma un voto al recuento."""
        # Suma la seleccion al recuento.
        self.sesion.recuento.sumar_seleccion(seleccion, unicidad)

    def preguntar_salida(self):
        self.controlador.preguntar_salida()

    def error_lectura(self):
        self.controlador.actualizar(ACT_ERROR)

    def imprimir_documentos(self):
        """ Realiza las ultimas operaciones sobre el recuento antes de comenzar
            la impresion
        """
        self.estado = E_IMPRIMIENDO
        self._iniciar_secuencia()
        self.secuencia.ejecutar()

    def habilitar_copia_certificados(self):
        def _imprimiendo(tipo_acta, final=False):
            """Muestra que esta imprimiendo el recuento en el panel."""
            self.controlador.hide_dialogo()
            self.controlador.mostrar_imprimiendo()

        def _fin():
            """Limpia el panel de estado cuando dejó de imprimir."""
            self.controlador.mostrar_pantalla_copias()
        self.estado = E_IMPRIMIENDO
        self._iniciar_secuencia()
        # piso los callbacks de la secuencia para evitar que sea un caso super
        # especial como era antes.
        self.secuencia.callback_fin_secuencia = _fin
        self.secuencia.callback_post_fin_secuencia = _fin
        self.secuencia.callback_imprimiendo = _imprimiendo
        self.secuencia.actas_a_imprimir = []
        # usar el mismo grupo categoria para todas las copias:
        grupo_cat = self.sesion.recuento.grupo_cat
        self.secuencia.acta_actual = [CIERRE_COPIA_FIEL, grupo_cat]
        self.secuencia._pedir_acta()

    def _iniciar_secuencia(self):
        """Inicia la secuencia de impresion de las actas."""
        def callback_imprimiendo(tipo_acta, final=False):
            """Se llama a este callback cuando se empieza a imprimir."""
            self.controlador.hide_dialogo()
            self.controlador.mostrar_imprimiendo()

        def callback_espera(tipo_acta):
            """Callback que se llama para setear la pantalla de espera de
            insercion de actas."""
            self.controlador.pedir_acta(tipo_acta[0])

        def callback_error_registro(tipo_acta, final=False):
            """El callback al cual se llama cuando se genera un error de
            registro del acta."""
            self.rampa.expulsar_boleta()
            self.controlador.cargar_dialogo(
                "mensaje_popup_{}".format(tipo_acta[0]))

        def callback_post_fin_secuencia():
            self.controlador.set_pantalla_anterior_asistente()

        def callback_fin_secuencia():
            """Se llama cuando se terminó toda la secuencia de impresion."""
            if self.config("mostrar_asistente_cierre"):
                self.controlador.set_pantalla_asistente_cierre()
            else:
                self.controlador.mostrar_pantalla_copias()

        self.secuencia = SecuenciaActas(self, callback_espera,
                                        callback_error_registro,
                                        callback_imprimiendo,
                                        callback_fin_secuencia,
                                        callback_post_fin_secuencia)

    def salir(self):
        self.salir_a_modulo(MODULO_INICIO)

    def apagar(self):
        self.salir_a_modulo(SHUTDOWN)
