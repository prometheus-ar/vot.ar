"""Controlador del modulo sufragio."""
from copy import copy
from urllib.parse import quote

from gi.repository.GObject import timeout_add
from msa.constants import COD_LISTA_BLANCO
from msa.core.data.candidaturas import (Agrupacion, Boleta, Candidatura,
                                        Categoria)
from msa.core.data.helpers import get_config
from msa.core.documentos.boletas import Seleccion
from msa.core.i18n import cambiar_locale
from msa.core.settings import USAR_BUFFER_IMPRESION
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.constants import (MODULO_ASISTIDA, MODULO_SUFRAGIO,
                                   MODULO_CAPACITACION)
from msa.modulos.sufragio.constants import (IDIOMAS_DISPONIBLES,
                                            NUMEROS_TEMPLATES,
                                            PANTALLA_CONSULTA, TEXTOS)
from msa.modulos.sufragio.decorators import solo_votando


class Actions(BaseActionController):

    """Actions del controlador de voto."""

    def cargar_cache(self, data):
        """Cachea los dos de candidaturas y los manda a la UI."""
        self.controlador.cargar_datos()

    def inicializar_interfaz(self, data):
        """Inicializa la interfaz de votacion."""
        modulo = self.controlador.modulo
        modulo.pantalla_insercion()

    def get_pantalla_voto(self, data):
        """Devuelve la pantalla inicial de votacion."""
        self.controlador.modulo.get_pantalla_inicial_voto()

    def imagen_consulta(self, data):
        """Muestra la imagen de la consulta."""
        self.controlador.imagen_consulta()


class Controlador(ControladorBase):

    """Controller para la interfaz web de voto."""

    def __init__(self, modulo):
        """Constructor del controlador de votacion."""
        super(Controlador, self).__init__(modulo)
        self.set_actions(Actions(self))
        self.textos = TEXTOS
        self.nombre = MODULO_SUFRAGIO

    def document_ready(self, data):
        """Callback que se llama cuando el browser lanza document.ready()."""
        self.modulo.rampa.expulsar_boleta()
        self.mostrar_loader()

    def mostrar_loader(self):
        """Muestra la ventana del loader."""
        self.send_constants()
        self.send_command("mostrar_loader")

    def ocultar_loader(self):
        """Oculta la ventana del loader."""
        self.send_command("ocultar_loader")

    @solo_votando
    def confirmar_seleccion(self, data):
        """Confirma la seleccion. Manda a imprimir."""
        def _inner():
            if self.modulo.rampa.tiene_papel:
                self.modulo._guardar_voto()
                self.reiniciar_seleccion()
            else:
                self.reiniciar_seleccion()
                self.modulo.pantalla_insercion()

        # Lo tiramos asincronico con un timeout por que si queda en el mismo
        # thread no actualiza la UI hasta que termina de cargar el buffer de
        # impresion, y si se extiende mucho puede tirar un segfault.
        timeout_add(50, _inner)

    def previsualizar_voto(self, data):
        """Previsualizacion del voto mientras se está imprimiendo."""
        if self.modulo.seleccion is not None and self.modulo.rampa.tiene_papel:
            imagen = self.modulo.seleccion.a_imagen(verificador=True,
                                                    solo_mostrar=True,
                                                    svg=True)
            image_data = quote(imagen.encode("utf-8"))
            self.send_command("mostrar_voto", image_data)
        else:
            self.reiniciar_seleccion()
            self.modulo.pantalla_insercion()

    @solo_votando
    def prepara_impresion(self, data=None):
        """Prepara la impresion del voto."""
        self.modulo.registrador._prepara_impresion(self.modulo.seleccion)

    @solo_votando
    def seleccionar_candidatos(self, seleccion):
        """Selecciona los candidatos."""
        for cod_categoria, cod_candidatos in list(seleccion.items()):
            muchos_candidatos = len(cod_candidatos) > 1

            if muchos_candidatos:
                self.modulo.seleccion.borrar_categoria(cod_categoria)

            for cod_candidato in cod_candidatos:
                cod_candidato = int(cod_candidato)
                candidato = Candidatura.one(cod_candidato)
                self.modulo.seleccion.elegir_candidato(candidato,
                                                       not muchos_candidatos)

    @solo_votando
    def seleccionar_idioma(self, idioma):
        """Selecciona el idioma."""
        cambiar_locale(idioma)
        self.send_constants()
        self.get_pantalla_modos()

    def consulta(self, seleccion_tag):
        """Muesta la consulta del voto en la pantalla."""
        try:
            self._datos_verificacion = seleccion_tag
            imagen = self._datos_verificacion.a_imagen(verificador=True,
                                                       solo_mostrar=True,
                                                       svg=True)
            self._imagen_verificacion = imagen
            self.set_screen(PANTALLA_CONSULTA)
        except AttributeError:
            self.modulo.rampa.expulsar_boleta()

    def imagen_consulta(self):
        """Genera y envia la imagen de la consulta."""
        # Sr. desarrollador, resista la tentacion de mandar una imagen
        # base64 encoded SVG es mas rapido
        image_data = quote(self._imagen_verificacion.encode("utf-8"))

        datos = self._datos_verificacion
        candidatos = []
        for categoria in Categoria.all():
            candidato = datos.candidato_categoria(categoria.codigo)
            if candidato is not None:
                candidatos.extend(candidato)
        cods_candidatos = [cand.id_umv for cand in candidatos]
        self.send_command("imagen_consulta", [image_data, cods_candidatos])

        self._imagen_verificacion = None
        self._datos_verificacion = None

    @solo_votando
    def get_pantalla_modos(self):
        """Muestra la pantalla de modos."""
        self.send_command("cargar_pantalla_inicial")

    @solo_votando
    def set_pantalla_idiomas(self):
        """Establece la pantalla de idiomas."""
        self.send_command("pantalla_idiomas", IDIOMAS_DISPONIBLES)

    def reiniciar_seleccion(self, data=None):
        """Resetea la seleccion. Elimina lo que el usuario eligió."""
        self.modulo.seleccion = Seleccion(self.sesion.mesa)

    def menu_salida(self):
        self.send_command("mostrar_menu_salida")

    def salir_a_modulo(self, nombre_modulo):
        if nombre_modulo == MODULO_ASISTIDA:
            if self.modulo.nombre == MODULO_ASISTIDA:
                nombre_modulo = MODULO_SUFRAGIO
            else:
                nombre_modulo = MODULO_ASISTIDA
        self.modulo.salir(nombre_modulo)

    def cargar_datos(self):
        datos = {}
        datos['categorias'] = self.dict_set_categorias()
        datos['candidaturas'] = self.dict_set_candidaturas()
        datos['agrupaciones'] = self.dict_set_agrupaciones()
        datos['boletas'] = self.dict_set_boletas()
        self.send_command("cargar_datos", datos)

    def dict_set_categorias(self):
        """Envia el diccionario con los datos de las categorias."""
        categorias = Categoria.all().to_dict()
        return categorias

    def dict_set_boletas(self):
        """Envia el diccionario con los datos de las categorias."""
        categorias = Boleta.all().to_dict()
        return categorias

    def dict_set_candidaturas(self):
        """Envia el diccionario con los datos de las categorias."""
        candidatos = Candidatura.all().to_dict()
        return candidatos

    def dict_set_agrupaciones(self):
        """Envia el diccionario con los datos de las categorias."""
        candidatos = Agrupacion.all().to_dict()
        return candidatos

    def get_encabezado(self):
        encabezado = get_config('datos_eleccion')
        if self.sesion.mesa is not None and \
                self.sesion.mesa.municipio is not None:
            encabezado = copy(encabezado)
            encabezado["fecha"] += " - {}".format(self.sesion.mesa.municipio)
        return encabezado

    def get_constants(self):
        """Genera las constantes que se van a usar en la UI."""
        flavor = self.modulo.config("flavor")

        shuffle_dict = {
            'por_sesion': self.modulo.config("mezclar_por_sesion"),
            'candidatos': self.modulo.config("mezclar_candidatos"),
            'listas': self.modulo.config("mezclar_listas"),
            'internas': self.modulo.config("mezclar_agrupaciones"),
            'consultas': self.modulo.config("mezclar_consulta")
        }

        usar_asistida = self.modulo.config("usar_asistida")
        mostrar_indicador_capacitacion = \
                self.modulo.config("mostrar_indicador") and \
                (self.modulo.nombre == MODULO_CAPACITACION)

        local_constants = {
            "agrupar_por_partido": self.modulo.config("agrupar_por_partido"),
            "asistida": False,
            "BARRA_SELECCION": self.modulo.config("mostrar_barra_seleccion"),
            "BOTONES_SELECCION_MODO":
            self.modulo.config("botones_seleccion_modo"),
            "cod_lista_blanco": COD_LISTA_BLANCO,
            "modificar_en_completa": self.modulo.config("boton_modificar_en_lista_completa"),
            "modificar_en_categorias": self.modulo.config("boton_modificar_en_categorias"),
            "modificar_con_una_categroria": self.modulo.config("boton_modificar_con_una_categoria"),
            "numeros_templates": NUMEROS_TEMPLATES[flavor],
            "shuffle": shuffle_dict,
            "templates": self.get_templates(),
            "tiempo_feedback": 150,
            "agrupar_cargo": self.modulo.config("agrupar_cargo"),
            "colapsar_listas": self.modulo.config("colapsar_listas"),
            "colapsar_candidatos": self.modulo.config("colapsar_candidatos"),
            "paso": self.modulo.config("paso"),
            "categoria_agrupa_por": self.modulo.config("categoria_agrupa_por"),
            "interna": self.modulo.config("interna"),
            "ubicacion": getattr(self.sesion.mesa, "codigo", None),
            "USAR_BUFFER_IMPRESION": USAR_BUFFER_IMPRESION,
            "USAR_ASISTIDA": usar_asistida,
            "mostrar_indicador_capacitacion": mostrar_indicador_capacitacion,
            "confirmacion_lateral": self.modulo.config("confirmacion_lateral"),
            "mostrar_adheridas_confirmacion":
            self.modulo.config("mostrar_adheridas_confirmacion"),
            "limitar_candidatos": self.modulo.config("limitar_candidatos"),
            "precachear_imagenes": self.modulo.config("precachear_imagenes"),
            "seleccionar_lista_unica":
                self.modulo.config("seleccionar_lista_unica"),
            "seleccionar_candidato_unico":
                self.modulo.config("seleccionar_candidato_unico"),
            "mostrar_blanco_siempre":
                self.modulo.config("mostrar_blanco_siempre"),
        }

        constants_dict = self.base_constants_dict()
        constants_dict.update(local_constants)

        return constants_dict

    def get_templates(self):
        """Devuelve las templates a precachear."""
        template_names = ("candidato", "confirmacion", "categoria", "lista",
                          "partido", "candidato_hijo", "confirmacion",
                          "consulta_popular", "candidatos_adicionales",
                          "colores")
        return template_names
