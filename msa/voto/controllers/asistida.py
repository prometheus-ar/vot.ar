# -*- coding: utf-8 -*-
from os.path import join

from msa.constants import COD_LISTA_BLANCO
from msa.core.audioplayer import WavPlayer
from msa.core.data import Speech
from msa.core.data.candidaturas import Categoria
from msa.voto.controllers.voto import ControllerVoto, get_constants
from msa.voto.settings import BOTON_LISTA_COMPLETA, \
    BOTON_VOTAR_POR_CATEGORIAS, PATH_TONOS, VOLUMEN_GENERAL, \
    BOTONES_SELECCION_MODO


_audio_player = None


class Asistente(object):

    """
    Asistente generico de votacion asistida, cada Asistente hereda de este.
    """

    indice_inicio = 1

    def __init__(self, controller, data, data_key=None, repetir=True):
        """Inicializa el asistente y empieza a enumerar las opciones.

        Argumentos:
            controller -- el controller que esta usando esto. En general es una
                          referencia al controller de Asistida.
            data -- los datos que se mandan a la vista.
            data_key -- la key en la que estan los datos concretos en elegir
                        diccionario de datos
            repetir -- indica si se debe repetir "inifinitamente" la locución.
        """
        self.opciones = []
        self.controller = controller
        self.data = data
        self.data_key = data_key
        self.confirmando = None

        self.enumerar(repetir=repetir)

    def enumerar(self, error=None, repetir=True):
        """Enumera cada una de las opciones a elegir.
        Argumentos:
            error -- agrega un mensaje de error al inicio de la locución.
            repetir -- indica si se debe repetir "inifinitamente" la locución.
        """

        textos = []
        if error is not None:
            textos.extend(error)
        preludio = self.get_preludio()
        if preludio is not None:
            textos.extend(preludio)
        self.opciones = self._get_opciones()
        for opcion in self.opciones:
            textos.extend(self._audio_opcion(opcion))
        epilogo = self.get_epilogo()
        if epilogo is not None:
            textos.extend(epilogo)
        self._decir(textos, repetir)

    def _decir(self, mensaje, repetir=True, cambio_estado=False):
        u"""
            Envía el mensaje al locutor.

            Argumentos:
              mensaje -- el mensaje a emitir
              repetir -- hace que el locutor repita automáticamente el mensaje
              cambio_estado -- quien llama a este método pide que el timer de
                               repetición de locución se reinicie, ya que ha
                               habido un nuevo tipo de mensaje
        """
        if cambio_estado:
            self.controller.sesion.locutor.reset()

        self.controller.sesion.locutor.decir(mensaje, repetir)

    def _get_opciones(self):
        """Genera una lista con todas las opciones."""
        opciones = list(enumerate(self.procesar_data(), self.indice_inicio))
        return opciones

    def _(self, key):
        """
        Shortcut para no poner Speech.one(key) en todos lados.
        Argumentos:
            key -- la key del objeto Speech.
        """
        return Speech.one(key).texto

    def _audio_opcion(self, opcion):
        u"""Genera el contenido del texto del audio de la opción."""
        num_opcion, datos = opcion
        mensaje = [self._('para_votar'),
                   datos['texto_asistida'],
                   self._('presione'),
                   str(num_opcion)]
        return mensaje

    def procesar_data(self):
        """Procesa los datos del formato de voto y genera lo que necesito para
        asistida.
        """
        if self.data_key is not None:
            data = self.data[self.data_key]
        else:
            data = self.data

        blanco = None
        nueva_data = []
        for datum in data:
            if 'codigo' not in datum or \
                    not datum['codigo'].endswith(COD_LISTA_BLANCO):
                nueva_data.append(datum)
            else:
                blanco = datum

        if blanco is not None:
            nueva_data = [blanco] + nueva_data
            self.indice_inicio = 0

        return nueva_data

    def get_preludio(self):
        """Lo que dice antes de la lista de opciones."""
        pass

    def get_epilogo(self):
        """Lo que dice después de la lista de opciones."""
        pass

    def elegir(self, numero):
        u"""Elije la opcion que seleccionó el usuario.

        Argumentos:
            numero -- El numero de opcion seleccionado.
        """
        opciones = dict(self.opciones)
        try:
            opcion = opciones.get(int(numero))
        except ValueError:
            opcion = None

        if opcion is None and not self.confirmando:
            self.opcion_invalida()
        else:
            self.callback(opcion, numero)

    def opcion_invalida(self):
        """
        Genera el texto en caso de que la opción elegida sea invalida y lo
        dice.
        """
        error = [self._("la_opcion"),
                 self._("que_ingreso"),
                 self._("no_existe")]
        self.enumerar(error=error)

    def cancelar(self):
        self.confirmando = None
        self.controller.cambiar_monitor()
        self.enumerar()

    def get_monitor(self):
        """Devuelve el texto que se utilizara en el indicador de estado abajo
        a la derecha del teclado. Esto ayuda a que la persona que esta
        asistiendo al elector pueda saber en que etapa del voto se encuentra
        el mismo sin comprometer el sectreto al voto.
        """
        return ""


class AsistenteModos(Asistente):

    """El asistente para la pantalla de seleccion de modos."""

    def get_monitor(self):
        return _("seleccionando_modo")

    def get_preludio(self):
        mensaje = [self._('ingrese_nro_modo'),
                   self._("confirmando_con_e_opcion")]
        return mensaje

    def procesar_data(self):
        modos = []
        botones = self.data
        if BOTON_VOTAR_POR_CATEGORIAS in botones:
            modos.append({'codigo': BOTON_VOTAR_POR_CATEGORIAS,
                          'texto_asistida': self._('categorias')})
        if BOTON_LISTA_COMPLETA in botones:
            modos.append(
                {'codigo': BOTON_LISTA_COMPLETA,
                 'texto_asistida': self._('lista_completa')})

        return modos

    def _audio_opcion(self, opcion):
        num_opcion, datos = opcion
        mensaje = [self._('para_votar_por'),
                   datos['texto_asistida'],
                   self._('presione'),
                   str(num_opcion)]
        return mensaje

    def callback(self, opcion, numero):
        self.controller.seleccionar_modo(opcion['codigo'])


class AsistenteListaCompleta(Asistente):

    """Asistente para el modo de votacion por lista completa."""

    def get_monitor(self):
        return _("seleccionando_lista")

    def get_preludio(self):
        mensaje = [self._('ingrese_nro_lista'),
                   self._("confirmando_con_e_opcion")]
        return mensaje

    def callback(self, opcion, numero):
        self.controller.seleccionar_lista([opcion['codigo'], None, None, True])

    def procesar_data(self):
        if self.data_key is not None:
            data = self.data[self.data_key]
        else:
            data = self.data

        blanco = None
        nueva_data = []
        for datum in data:
            if 'codigo' not in datum or \
                    not datum['codigo'].endswith(COD_LISTA_BLANCO):
                nueva_data.append(datum)
            else:
                blanco = datum

        if blanco is not None:
            nueva_data = [blanco] + nueva_data
            self.indice_inicio = 0

        return nueva_data


class AsistenteAdhesion(Asistente):

    """
       Asiste para seleccion de candidatos cuando hay adhesion segmentada.
    """

    def get_monitor(self):
        ret = _("seleccionando_candidatos")
        return ret % self.categoria.nombre

    def get_preludio(self):
        self.categoria = Categoria.one(self.data[1])
        mensaje = [self.categoria.texto_asistida_ingrese_nro,
                   self._("confirmando_con_e_opcion")]
        return mensaje

    def callback(self, opcion, numero):
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            categoria = Categoria.one(opcion['cod_categoria'])
            mensaje = [self._("ud_eligio_candidato"),
                       numero,
                       self._("para"),
                       categoria.texto_asistida,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controller.cambiar_monitor()
        else:
            opcion_ = self.confirmando[0]
            self.controller.seleccionar_lista([opcion_['codigo'],
                                               opcion_['cod_categoria'], None,
                                               False])


class AsistenteCandidatos(Asistente):

    """Asistente para votacion por categorias."""

    def get_monitor(self):
        if self.confirmando:
            ret = _("confirmando_candidatos")
        else:
            ret = _("seleccionando_candidatos")

        return ret % self.categoria.nombre

    def get_preludio(self):
        self.categoria = Categoria.one(self.data["cod_categoria"])
        mensaje = [self.categoria.texto_asistida_ingrese_nro,
                   self._("confirmando_con_e")]
        return mensaje

    def callback(self, opcion, numero):
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            categoria = Categoria.one(opcion['cod_categoria'])
            mensaje = [self._("ud_eligio_candidato"),
                       numero,
                       self._("para"),
                       categoria.texto_asistida,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controller.cambiar_monitor()
        else:
            self.controller.seleccionar_candidatos(
                [self.confirmando[0]['cod_categoria'],
                 [self.confirmando[0]['codigo']]])


class AsistenteConsultaPopular(Asistente):

    """Asitente para eleccion de consulta popular."""

    def get_monitor(self):
        if self.confirmando:
            ret = _("confirmando_candidatos")
        else:
            ret = _("seleccionando_candidatos")

        return ret % self.categoria.nombre

    def get_preludio(self):
        self.categoria = Categoria.one(self.data[1])
        mensaje = [self.categoria.texto_asistida_ingrese_nro,
                   self._("confirmando_con_e_opcion")]
        return mensaje

    def callback(self, opcion, numero):
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            categoria = Categoria.one(opcion['cod_categoria'])
            mensaje = [self._("ud_eligio"),
                       numero,
                       self._("para"),
                       categoria.texto_asistida,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controller.cambiar_monitor()
        else:
            self.controller.seleccionar_candidatos(
                [self.confirmando[0]['cod_categoria'],
                 [self.confirmando[0]['codigo']]])


class AsistentePartido(Asistente):

    """Asistente para seleccion de partido."""

    def get_monitor(self):
        if self.confirmando:
            ret = _("confirmando_partido")
        else:
            ret = _("seleccionando_partido")

        return ret

    def get_preludio(self):
        mensaje = [self._("ingrese_nro_interna")]
        return mensaje

    def callback(self, opcion, numero):
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            mensaje = [self._("ud_eligio_candidato"),
                       numero,
                       self._("para"),
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controller.cambiar_monitor()
        else:
            self.controller.seleccionar_partido([self.confirmando[0]['codigo'],
                                                 None])


class AsistenteConfirmacion(Asistente):

    """Asistente para confirmacion de voto."""

    def get_monitor(self):
        return _("confirmando")

    def get_preludio(self):
        mensaje = [self._("ud_confirmo")]

        return mensaje

    def get_epilogo(self):
        mensaje = [self._('confirmar_ud_confirmo_fin'),
                   self._('confirmar_ud_confirmo_fin2')]

        return mensaje

    def _audio_opcion(self, opcion):
        num_opcion, datos = opcion
        mensaje = [
            self._('el_candidato'),
            datos['candidato']['texto_asistida'],
            self._('para'),
            Categoria.one(datos['categoria']['codigo']).texto_asistida]
        return mensaje

    def elegir(self, data):
        self._decir([self._("imprimiendo")], False)
        self.controller.prepara_impresion()
        self.controller.previsualizar_voto(data)

    def cancelar(self):
        self.controller.sesion.locutor.shutup()

        self.controller.send_command("pantalla_modos", BOTONES_SELECCION_MODO)
        #self.controller.send_command("mostrar_teclado")


class AsistenteVerificacion(AsistenteConfirmacion):

    """Asistente para verificacion de votos ya generados."""

    def get_epilogo(self):
        pass

    def get_preludio(self):
        mensaje = [self._("ud_voto")]

        return mensaje


class ControllerAsistida(ControllerVoto):

    """Controller para la interaccion con la interfaz de Asistida."""

    def __init__(self, *args, **kwargs):
        ControllerVoto.__init__(self, *args, **kwargs)
        global _audio_player
        if _audio_player is None or not _audio_player.is_alive():
            _audio_player = WavPlayer()
            _audio_player.start()
            _audio_player.set_volume(VOLUMEN_GENERAL)

    def send_command(self, command, data=None):
        """Intercepta los comandos que se envian a la interfaz.

        Hace un override del metodo send_command de Zaguan para poder inyectar
        las cosas de asistidas del medio, tiene una lista de comandos para
        interceptar y una white_list de que comandos tiene que dejar pasar. El
        resto de los comandos no se envia nunca al front end.

        Argumentos:
            command -- El comando enviado originalmente al front end.
            data -- los datos que se mandaron como parametro al comando.
        """
        white_list = ["set_constants", "cargar_categorias",
                      "limpiar_data_categorias", "change_screen",
                      "insertando_boleta", "mostrar_voto",
                      "hide_barra_opciones", "imagen_consulta",
                      "mostrar_teclado", "cargar_adhesiones",
                      "cargar_consulta_popular", "mostrar_loader",
                      "ocultar_loader"]
        interceptar = {
            "pantalla_modos": [AsistenteModos, None],
            "cargar_listas": [AsistenteListaCompleta, None],
            "cargar_listas_params": [AsistenteListaCompleta, 0],
            "cargar_adhesiones": [AsistenteAdhesion, 0],
            "cargar_consulta_popular": [AsistenteConsultaPopular, 0],
            "cargar_candidatos": [AsistenteCandidatos, "candidatos"],
            "mostrar_confirmacion": [AsistenteConfirmacion, None],
            "seleccion_partido": [AsistentePartido, None],
        }

        if command in white_list:
            if command == "change_screen":
                attr = "change_screen_%s" % data[0]
                if hasattr(self, attr):
                    getattr(self, attr)()
            ControllerVoto.send_command(self, command, data)

        if command in interceptar.keys():
            clase, key = interceptar[command]
            self.asistente = clase(self, data, key)
            self.cambiar_monitor()
            self.send_command("mostrar_teclado")

    def numeral(self, numero):
        """Callback cuando se apreta en numeral.

        Argumentos:
            numero -- el numero (de n cifras) que se escribió antes del
            numeral.
        """
        if numero.isalnum():
            numero = str(int(numero))
        self.asistente.elegir(numero)

    def asterisco(self, data):
        """Callback cuando se apreta en asterisco.

        Argumentos:
            numero -- el numero (de n cifras) que se escribió antes del
            asterisco.
        """
        self.asistente.cancelar()

    def change_screen_insercion_boleta(self):
        """Callback que se llama cuando se cambia a la pantalla de insercion."""
        self.sesion.locutor.shutup()

    def change_screen_mensaje_final(self):
        """Callback que se llama cuando se cambia a la pantalla de mensaje."""
        self.send_command("hide_barra_opciones")
        mensaje = [self.asistente._("fin_votacion"),
                   self.asistente._("puede_verificar")]
        self.asistente._decir(mensaje)

    def cambiar_monitor(self):
        """Cambia el texto del monitor al del asistente actual."""
        ControllerVoto.send_command(self, "cambiar_indicador_asistida",
                                    self.asistente.get_monitor())

    def imagen_consulta(self):
        """Pisamos el metodo imagen_consulta para escucharlo en vez de verlo."""
        self.parent.seleccion = self._datos_verificacion
        consultas = self.get_data_categorias(consulta_popular=True)
        cat_list = self.get_data_categorias(todas=True)
        cat_list += consultas
        self.parent.seleccion = None
        self.asistente = AsistenteVerificacion(self, cat_list, repetir=False)
        self._imagen_verificacion = None
        self._datos_verificacion = None

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants(self.sesion.mesa.codigo)
        constants_dict['asistida'] = True
        constants_dict['titulo'] = _("titulo_votacion_asistida")
        constants_dict['subtitulo'] = _("coloque_el_acrilico")
        self.send_command("set_constants", constants_dict)

    def emitir_tono(self, tecla):
        """Emite un tono segun la tecla pulsada. """
        if tecla == "*":
            tecla = "s"
        elif tecla == "#":
            tecla = "p"
        tono = join(PATH_TONOS, "%s.wav" % tecla)
        self.sesion.locutor.shutup()
        _audio_player.play(tono)
