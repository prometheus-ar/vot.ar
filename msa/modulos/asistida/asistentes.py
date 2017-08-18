"""
Los asistentes se encargan de manejar el audio y la navegacion de las
diferentes "pantallas" del modulo Asistida.
"""
from gi.repository.GObject import timeout_add

from msa.constants import COD_LISTA_BLANCO
from msa.core.data import Speech
from msa.core.data.candidaturas import Categoria, Candidatura, Lista
from msa.modulos.sufragio.constants import (BOTON_LISTA_COMPLETA,
                                            BOTON_VOTAR_POR_CATEGORIAS)


class Asistente(object):

    """
    Asistente generico de votacion asistida, cada Asistente hereda de este.
    """

    indice_inicio = 1
    es_interactivo = True           # muestra teclado en pantalla

    def __init__(self, controlador, data, data_key=None, repetir=True):
        """Inicializa el asistente y empieza a enumerar las opciones.

        Argumentos:
            controlador -- el controlador que esta usando esto. En general es una
                          referencia al controlador de Asistida.
            data -- los datos que se mandan a la vista.
            data_key -- la key en la que estan los datos concretos en elegir
                        diccionario de datos
            repetir -- indica si se debe repetir "inifinitamente" la locución.
        """
        self.opciones = []
        self.controlador = controlador
        self.controlador.ultima_tecla = None
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
        """
        Envía el mensaje al locutor.

        Argumentos:
            mensaje -- el mensaje a emitir
            repetir -- hace que el locutor repita automáticamente el mensaje
            cambio_estado -- quien llama a este método pide que el timer de
                repetición de locución se reinicie, ya que hubo un nuevo tipo
                de mensaje
        """
        if cambio_estado:
            self.controlador.sesion.locutor.reset()
        self.controlador.sesion.locutor.decir(mensaje, repetir)

    def registrar_callback_fin_cola(self, callback):
        locutor = self.controlador.sesion.locutor
        locutor._audio_player.registrar_callback_fin_cola(callback)

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
        """
        Genera el contenido del texto del audio de la opción.
        Argumentos:
            opcion -- la opcion a locutar.
        """
        num_opcion, datos = opcion
        mensaje = [self._('para_votar'),
                   datos['texto_asistida'] if datos["codigo"] != "0"
                        else self._('agrupaciones_municipales'),
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
            nueva_data = nueva_data + [blanco]
            #self.indice_inicio = 0

        return nueva_data

    def get_preludio(self):
        """Lo que dice antes de la lista de opciones."""
        pass

    def get_epilogo(self):
        """Lo que dice después de la lista de opciones."""
        pass

    def elegir(self, numero):
        """Elije la opcion que seleccionó el usuario.

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
        self.controlador.cambiar_monitor()
        self.enumerar()

    def get_monitor(self):
        """Devuelve el texto que se utilizara en el indicador de estado abajo
        a la derecha del teclado. Esto ayuda a que la persona que esta
        asistiendo al elector pueda saber en que etapa del voto se encuentra
        el mismo sin comprometer el sectreto al voto.
        """

        return ""

    def recordar(self):
        """Emite un recordatorio sonoro de interaccion al usuario."""
        mensaje = [self._('no_olvide_apretar_numeral')]
        self._decir(mensaje, repetir=True)


class AsistenteModos(Asistente):

    """El asistente para la pantalla de seleccion de modos."""

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        return _("seleccionando_modo")

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [
            self._('a_continuacion_usted'),
            self._('ingrese_nro_modo'),
            self._("confirmando_con_e_opcion"),
            self._("las_opciones_son")]
        return mensaje

    def procesar_data(self):
        """Procesa la data."""
        modos = []
        for boton in self.controlador.modulo.config("botones_seleccion_modo"):
            if boton == BOTON_VOTAR_POR_CATEGORIAS:
                modos.append({'codigo': BOTON_VOTAR_POR_CATEGORIAS,
                              'texto_asistida': self._('categorias')})
            if boton == BOTON_LISTA_COMPLETA:
                modos.append({'codigo': BOTON_LISTA_COMPLETA,
                              'texto_asistida': self._('lista_completa')})

        return modos

    def _audio_opcion(self, opcion):
        """
        Genera el audio de la opcion.
        Argumentos:
            opcion - la opcion a locutar.
        """
        num_opcion, datos = opcion
        mensaje = [self._('para_votar_por'),
                   datos['texto_asistida'],
                   self._('presione'),
                   str(num_opcion)]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        self.controlador.send_command("seleccionar_modo", opcion['codigo'])


class AsistenteListaCompleta(Asistente):

    """Asistente para el modo de votacion por lista completa."""

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        return _("seleccionando_lista")

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [
            self._('a_continuacion_usted'),
            self._('ingrese_nro_lista'),
            self._("confirmando_con_e_opcion"),
            self._("las_opciones_son")]
        return mensaje

    def _audio_opcion(self, opcion):
        """
        Genera el contenido del texto del audio de la opción.
        Argumentos:
            opcion -- la opcion a locutar.
        """
        num_opcion, datos = opcion

        mensaje = [self._('para_votar'),
                   datos['texto_asistida']]

        if self.controlador.modulo.config("completa_dice_candidato"):
            lista = Lista.one(datos["codigo"])
            if lista is not None:
                for candidato in lista.candidatos:
                    if len(lista.candidatos) > 1:
                        mensaje.append(candidato.categoria.texto_asistida)
                    mensaje.append(candidato.texto_asistida)
            elif datos["codigo"] == "0":
                # casos especiales:
                mensaje.append(self._('agrupaciones_municipales'))

        mensaje += [self._('presione'),
                    str(num_opcion)]
        return mensaje

    def callback(self, opcion, numero):
        """Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        self.controlador.send_command("seleccionar_lista", opcion['codigo'])

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
            nueva_data = nueva_data + [blanco]

        return nueva_data


class AsistenteCargoListas(Asistente):
    """
    Asistente para el modo de votacion por lista completa con listas
    sin gobernador u otros candidatos
    """
    def get_monitor(self):
        """Devuelve el texto del monitor."""
        return _("seleccionando_cargo_lista")

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [
            self._('a_continuacion_usted'),
            self._('ingrese_nro_cargo_lista'),
            self._("confirmando_con_e_opcion")]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """

        if "id_candidatura" in opcion:
            codigo = opcion['id_candidatura']
        elif opcion["codigo"] == "0":
            # casos especiales como "agrupaciones_municipales":
            codigo = None
        self.controlador.send_command("seleccionar_lista", codigo)

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
            nueva_data += [blanco]

        return nueva_data


class AsistenteAdhesion(Asistente):

    """
       Asiste para seleccion de candidatos cuando hay adhesion segmentada.
    """

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        ret = _("seleccionando_candidatos")
        return ret % self.categoria.nombre

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        self.categoria = Categoria.one(self.data[1])
        mensaje = [
            self._("a_continuacion_usted"),
            self._("su_candidato_para"),
            self.categoria.texto_asistida,
            self._("confirmando_con_e_opcion")]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            categoria = Categoria.one(opcion['cod_categoria'])
            mensaje = [self._("ud_eligio_opcion"),
                       numero,
                       self._("para"),
                       categoria.texto_asistida,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controlador.cambiar_monitor()
        else:
            opcion_ = self.confirmando[0]
            self.controlador.seleccionar_lista([opcion_['codigo'],
                                               opcion_['cod_categoria'], None,
                                               False])


class AsistenteCandidatos(Asistente):

    """Asistente para votacion por categorias."""

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        if self.confirmando:
            ret = _("confirmando_candidatos")
        else:
            ret = _("seleccionando_candidatos")

        return ret % self.categoria.nombre

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        self.categoria = Categoria.one(self.data["cod_categoria"])
        mensaje = [
            self._("a_continuacion_usted"),
            self._("su_candidato_para"),
            self.categoria.texto_asistida,
            self._("confirmando_con_e"),
            self._("las_opciones_son")]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            categoria = Categoria.one(opcion['cod_categoria'])
            mensaje = [self._("ud_eligio_opcion"),
                       numero,
                       self._("para"),
                       categoria.texto_asistida,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controlador.cambiar_monitor()
        else:
            self.controlador.send_command("seleccionar_candidatos_asistida",
                [self.confirmando[0]['cod_categoria'],
                 [self.confirmando[0]['id_umv']]])


class AsistenteConsultaPopular(Asistente):

    """Asitente para eleccion de consulta popular."""

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        if self.confirmando:
            ret = _("confirmando_candidatos")
        else:
            ret = _("seleccionando_candidatos")

        return ret % self.categoria.nombre

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        self.categoria = Categoria.one(self.data["cod_categoria"])
        mensaje = [
            self._("a_continuacion_usted"),
            self._("su_candidato_para"),
            self.categoria.texto_asistida,
            self._("confirmando_con_e_opcion"),
            self._("las_opciones_son")]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
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
            self.controlador.cambiar_monitor()
        else:
            self.controlador.send_command("seleccionar_candidatos_asistida",
                [self.confirmando[0]['cod_categoria'],
                 [self.confirmando[0]['id_umv']]])


class AsistentePartido(Asistente):

    """Asistente para seleccion de partido."""

    def __init__(self, controlador, data, data_key=None, repetir=True):
        blanco = Candidatura.first(clase="Blanco").to_dict()
        data.append(blanco)
        Asistente.__init__(self, controlador, data, data_key, repetir)

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        if self.confirmando:
            ret = _("confirmando_partido")
        else:
            ret = _("seleccionando_partido")

        return ret

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [
            self._("a_continuacion_usted"),
            self._("ingrese_nro_interna")]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            mensaje = [self._("ud_eligio_opcion"),
                       numero,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controlador.cambiar_monitor()
        else:
            if self.confirmando[0]['codigo'] == COD_LISTA_BLANCO:
                self.controlador.send_command("seleccionar_lista",
                                              self.confirmando[0]['codigo'])
            else:
                self.controlador.send_command("seleccionar_partido_asistida",
                                         [self.confirmando[0]['codigo'],
                                          None])


class AsistentePartidosCat(Asistente):

    """Asistente para seleccion de partido."""

    def __init__(self, controlador, data, data_key=None, repetir=True):
        categoria = data[0]['cod_categoria']
        blanco = Candidatura.one(clase="Blanco",
                                 cod_categoria=categoria).to_dict()
        data.append(blanco)
        Asistente.__init__(self, controlador, data, data_key, repetir)

    def procesar_data(self):
        """Procesa los datos del formato de voto y genera lo que necesito para
        asistida.
        """
        if self.data_key is not None:
            data = self.data[self.data_key]
        else:
            data = self.data

        return data

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        if self.confirmando:
            ret = _("confirmando_partido")
        else:
            ret = _("seleccionando_partido")

        return ret

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        self.categoria = Categoria.one(self.data[0]['cod_categoria'])
        mensaje = [
                self._('a_continuacion_usted'),
                self._("ingrese_nro_interna"),
                self._("para"),
                self.categoria.texto_asistida]
        return mensaje

    def callback(self, opcion, numero):
        """
        Callback que se ejecuta cuando se selecciona una opcion.
        Argumentos:
            opcion -- la opcion elegida.
            numero -- el numero de opcion que tiene la opcion elegida.
        """
        if self.confirmando is None:
            self.confirmando = [opcion, numero]
            mensaje = [self._("ud_eligio_opcion"),
                       numero,
                       opcion['texto_asistida'],
                       self._("acuerdo_cancelar")]
            self._decir(mensaje)
            self.controlador.cambiar_monitor()
        else:
            if self.confirmando[0]['codigo'] == COD_LISTA_BLANCO:
                self.controlador.send_command("seleccionar_candidatos_asistida",
                    [self.confirmando[0]['cod_categoria'],
                    [self.confirmando[0]['id_umv']]])
            else:
                self.controlador.send_command(
                    "seleccionar_partido_asistida",
                    [self.confirmando[0]['codigo'],
                    self.confirmando[0]['cod_categoria']])


class AsistenteConfirmacion(Asistente):

    """Asistente para confirmacion de voto."""

    def __init__(self, controlador, data, data_key=None, repetir=True):
        if len(data) == 1:
            self.controlador = controlador
            self.elegir(None)
            self.es_interactivo = False     # no mostrar teclado (controlador)
        else:
            Asistente.__init__(self, controlador, data, data_key, repetir)

    def get_monitor(self):
        """Devuelve el texto del monitor."""
        return _("confirmando")

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [self._("ud_confirmo")]

        return mensaje

    def get_epilogo(self):
        """Lo que dice después de la lista de opciones."""
        mensaje = [self._('confirmar_ud_confirmo_fin'),
                   self._('confirmar_ud_confirmo_fin2')]

        return mensaje

    def _audio_opcion(self, opcion):
        """Genera el audio de la opcion."""
        num_opcion, datos = opcion
        mensaje = [
            self._('el_candidato'),
            datos['candidato']['texto_asistida'],
            self._('para'),
            Categoria.one(datos['categoria']['codigo']).texto_asistida]
        return mensaje

    def elegir(self, data):
        """Confirma la elección, no utiliza número de opcion (data)"""
        # ocultar inmediatamente el teclado:
        self.controlador.send_command("ocultar_teclado")
        def _interfaz():
            self.controlador.send_command("agradecimiento")

        def _inner():
            self.controlador.prepara_impresion()
            self._decir([self._("imprimiendo")], False)
            self.controlador.confirmar_seleccion(data)

        timeout_add(1000, _interfaz)
        timeout_add(2000, _inner)

    def cancelar(self):
        """Cancela una opcion."""
        self.controlador.sesion.locutor.shutup()
        self.controlador.modulo.set_estado(None)
        self.controlador.modulo._comenzar()


class AsistenteVerificacion(AsistenteConfirmacion):

    """Asistente para verificacion de votos ya generados."""

    def __init__(self, controlador, data, data_key=None, repetir=True):
        Asistente.__init__(self, controlador, data, data_key, repetir)

    def get_epilogo(self):
        """Lo que dice después de la lista de opciones."""
        pass

    def get_preludio(self):
        """Devuelve el mensaje del preludio."""
        mensaje = [self._("ud_voto")]

        return mensaje

    def _decir(self, mensaje, repetir=True, cambio_estado=False):
        """
        Envía el mensaje al locutor.

        Argumentos:
            mensaje -- el mensaje a emitir
            repetir -- hace que el locutor repita automáticamente el mensaje
            cambio_estado -- quien llama a este método pide que el timer de
                repetición de locución se reinicie, ya que hubo un nuevo tipo
                de mensaje
        """
        def _inner():
            rampa = self.controlador.modulo.rampa
            self.controlador.modulo.pantalla_insercion()
            rampa.expulsar_boleta()

        self.registrar_callback_fin_cola(_inner)
        AsistenteConfirmacion._decir(self, mensaje, repetir, cambio_estado)
