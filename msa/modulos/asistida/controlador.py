"""Controlador para el modulo Asistida."""
from datetime import datetime
from os.path import join

from gi.repository import GObject

from msa.constants import COD_LISTA_BLANCO
from msa.core.audio.settings import VOLUMEN_GENERAL
from msa.core.data.candidaturas import Candidatura, Categoria, Lista, Partido
from msa.modulos.asistida.asistentes import (AsistenteAdhesion,
                                             AsistenteCandidatos,
                                             AsistenteCargoListas,
                                             AsistenteConfirmacion,
                                             AsistenteConsultaPopular,
                                             AsistenteListaCompleta,
                                             AsistenteModos, AsistentePartido,
                                             AsistentePartidosCat,
                                             AsistenteVerificacion)
from msa.modulos.asistida.constants import PATH_TONOS, TIEMPO_ITER_TIMEOUT
from msa.modulos.asistida.helpers import ultimo_beep
from msa.modulos.constants import MODULO_ASISTIDA
from msa.modulos.sufragio.controlador import Controlador as ControllerVoto

class Controlador(ControllerVoto):

    """Controller para la interaccion con la interfaz de Asistida."""

    def __init__(self, *args, **kwargs):
        """Constructor del controlador."""
        ControllerVoto.__init__(self, *args, **kwargs)
        self.nombre = MODULO_ASISTIDA
        self.modulo._start_audio()
        if self.modulo._player is not None:
            self.modulo._player.set_volume(VOLUMEN_GENERAL)

        self.ultima_tecla = None

        GObject.timeout_add_seconds(TIEMPO_ITER_TIMEOUT, ultimo_beep, self)

    def audios_pantalla_modos(self, data):
        """Carga los audios de la pantalla de modos."""
        self.audios("pantalla_modos", data)

    def audios_cargar_candidatos(self, data):
        """Carga los audios de los candidatos."""
        data_dict = {"cod_categoria": data[0]}
        candidatos = []
        for elem in data[1]:
            candidato = Candidatura.one(id_umv=elem).to_dict()
            candidatos.append(candidato)

        data_dict["candidatos"] = candidatos
        self.audios("cargar_candidatos", data_dict)

    def audios_cargar_consulta(self, data):
        """Carga los audios de la consulta popular."""
        data_dict = {"cod_categoria": data[0]}
        candidatos = []
        for elem in data[1]:
            candidato = Candidatura.one(id_umv=elem).to_dict()
            candidatos.append(candidato)
        data_dict["candidatos"] = candidatos
        self.audios("cargar_consulta_popular", data_dict)

    def audios_cargar_listas(self, data):
        """Carga los audios de las listas."""
        listas = []

        for datum in data:
            if datum != COD_LISTA_BLANCO:
                lista = Lista.one(id_candidatura=datum).to_dict()
            else:
                lista = Candidatura.first(clase="Blanco").to_dict()
            listas.append(lista)

        self.audios("cargar_listas", listas)

    def audios_cargo_listas(self, data):
        """Carga los audios de las lista de los cargos."""
        listas = []
        for datum in data:
            lista = Candidatura.one(id_umv=datum).to_dict()
            listas.append(lista)

        self.audios("cargar_cargo_listas", listas)

    def audios_mostrar_confirmacion(self, data):
        """Carga los audios de la confirmacion."""
        paneles = []
        for datum in data:
            categoria = Categoria.one(datum[0]).to_dict()
            candidato = Candidatura.one(datum[1]).to_dict()
            dict_panel = {"categoria": categoria,
                          "candidato": candidato}
            paneles.append(dict_panel)
        self.audios("mostrar_confirmacion", paneles)

    def audios_partidos_categoria(self, data):
        """Carga los audios de los partidos en la categoria."""
        partidos = []
        for datum in data[1]:
            partido = Partido.one(datum).to_dict()
            partido["cod_categoria"] = data[0]
            partidos.append(partido)
        self.audios("cargar_partidos_categoria", partidos)

    def audios_partidos_completa(self, data):
        """Carga los audios de los partidos en lista completa."""
        partidos = []
        for datum in data:
            partido = Partido.one(datum).to_dict()
            partidos.append(partido)
        self.audios("cargar_partidos_completa", partidos)

    def audios(self, command, data=None):
        """Llama al asistente de cada uno de las 'pantallas'."""
        interceptar = {
            "pantalla_modos": [AsistenteModos, None],
            "cargar_listas": [AsistenteListaCompleta, None],
            "cargar_adhesiones": [AsistenteAdhesion, 0],
            "cargar_consulta_popular": [AsistenteConsultaPopular,
                                        "candidatos"],
            "cargar_candidatos": [AsistenteCandidatos, "candidatos"],
            "mostrar_confirmacion": [AsistenteConfirmacion, None],
            "cargar_partidos_completa": [AsistentePartido, None],
            "cargar_partidos_categoria": [AsistentePartidosCat, None],
            "cargar_cargo_listas": [AsistenteCargoListas, None],
        }

        if command in list(interceptar.keys()):
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

    def change_screen_insercion_boleta(self, data):
        """Callback que se llama cuando se cambia a la pantalla de insercion."""
        self.sesion.locutor.shutup()

    def change_screen_mensaje_final(self):
        """Callback que se llama cuando se cambia a la pantalla de mensaje."""
        mensaje = [self.asistente._("fin_votacion"),
                   self.asistente._("puede_verificar")]
        self.asistente._decir(mensaje)

    def cambiar_monitor(self):
        """Cambia el texto del monitor al del asistente actual."""
        ControllerVoto.send_command(self, "cambiar_indicador_asistida",
                                    self.asistente.get_monitor())

    def imagen_consulta(self):
        """Pisamos el metodo imagen_consulta para escucharlo en vez de verlo."""
        self.modulo.seleccion = self._datos_verificacion
        categorias = Categoria.many(sorted="posicion")
        cat_list = []
        for categoria in categorias:
            cat_dict = {}
            cat_dict['categoria'] = categoria.to_dict()
            cands = self.modulo.seleccion.candidato_categoria(categoria.codigo)
            cat_dict['candidato'] = cands[0].to_dict()
            cat_list.append(cat_dict)
        self.modulo.seleccion = None
        self.asistente = AsistenteVerificacion(self, cat_list, repetir=False)
        self._imagen_verificacion = None
        self._datos_verificacion = None

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = self.get_constants()
        constants_dict['asistida'] = True
        constants_dict['titulo'] = _("titulo_votacion_asistida")
        constants_dict['subtitulo'] = _("coloque_el_acrilico")
        constants_dict['subtitulo_contraste'] = \
            _("coloque_el_acrilico_contraste")
        constants_dict['seleccionar_candidato_unico'] = False
        self.send_command("set_constants", constants_dict)

    def emitir_tono(self, tecla):
        """Emite un tono segun la tecla pulsada."""
        if tecla == "*":
            tecla = "s"
        elif tecla == "#":
            tecla = "p"
        tono = join(PATH_TONOS, "%s.wav" % tecla)
        self.sesion.locutor.shutup()
        self.modulo._player.play(tono)

        if tecla not in ("p", "s"):
            self.ultima_tecla = datetime.now()
        else:
            self.ultima_tecla = None
