"""Controlador del modulo sufragio."""
from base64 import encodestring
from io import BytesIO
from urllib.parse import quote

from msa.constants import COD_LISTA_BLANCO
from msa.core.data.candidaturas import (Agrupacion, Boleta, Candidatura,
                                        Categoria)
from msa.core.data.helpers import get_config
from msa.core.documentos.boletas import Seleccion
from msa.core.i18n import cambiar_locale
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.constants import (MODULO_ASISTIDA, MODULO_CAPACITACION,
                                   MODULO_SUFRAGIO)
from msa.modulos.sufragio.constants import NUMEROS_TEMPLATES, TEXTOS
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
        # No dejamos que nadie arranque el modulo con una boleta introducida en
        # la rampa
        self.modulo.rampa.expulsar_boleta("arranque")
        # Mostramos el mensaje de "cargando".
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
        # Solo guardamos el voto si hay papel puesto en la rampa. Sino
        # reseteamos todo.
        if self.modulo.rampa.tiene_papel:
            self.modulo._guardar_voto()
        else:
            self.reiniciar_seleccion()
            self.modulo.pantalla_insercion()

    def previsualizar_voto(self, data=None):
        """Previsualizacion del voto mientras se está imprimiendo.

        Este comportamiento se agregó para que la persona vea como tiene que
        salir impreso su voto y para bajar la ansiedad del usuario mientras
        espera que la boleta imprima.
        """
        # si tengo una seleccion para mostrar y tengo papel en la impresora
        if self.modulo.seleccion is not None and self.modulo.rampa.tiene_papel:
            image_data = None
            if self.nombre != MODULO_ASISTIDA:
                # genero la imagen
                muestra_svg = self.modulo.config("muestra_svg")
                mostrar = {"en_pantalla": True}
                imagen = self.modulo.seleccion.a_imagen(mostrar,
                                                        svg=muestra_svg)
                # despues de generar la imagen borro la seleccion por que ya no
                # la necesito.
                self.reiniciar_seleccion()

                # en caso de mostrar la imagen en PNG tenemos que pasarla en
                # base64
                if not muestra_svg:
                    buffer = BytesIO()
                    imagen.save(buffer, format="PNG")
                    img_data = encodestring(buffer.getvalue())
                    imagen = "data:image/png;base64,%s" % img_data.decode()

                # quoteamos y encodeamos antes de mandar
                image_data = quote(imagen.encode("utf-8"))

            self.send_command("mostrar_voto", image_data)
        else:
            # si no cumple con las condiciones para mostar la imagen vamos a
            # mostar la pantalla de insercion
            self.modulo.pantalla_insercion()

    @solo_votando
    def prepara_impresion(self, data=None):
        """Prepara la impresion del voto."""
        self.modulo.registrador._prepara_impresion(self.modulo.seleccion)

    @solo_votando
    def seleccionar_candidatos(self, seleccion):
        """Selecciona los candidatos."""
        for cod_categoria, cod_candidatos in list(seleccion.items()):
            # En caso de ser una eleccion donde pueden elegir mas de un
            # candidato en la misma categoría como Azuay o los presupuestos
            # participativos
            muchos_candidatos = len(cod_candidatos) > 1

            if muchos_candidatos:
                self.modulo.seleccion.borrar_categoria(cod_categoria)

            # seleccionamos los candidatos de cada categoría.
            for cod_candidato in cod_candidatos:
                cod_candidato = int(cod_candidato)
                candidato = Candidatura.one(cod_candidato)
                self.modulo.seleccion.elegir_candidato(candidato,
                                                       not muchos_candidatos)
        # las categorias para las cuales no llegaron candidatos las rellenamos
        # con "voto en blanco".
        self.modulo.seleccion.rellenar_de_blanco()

    @solo_votando
    def seleccionar_idioma(self, idioma):
        """Selecciona el idioma."""
        cambiar_locale(idioma)
        self.send_constants()
        self.get_pantalla_modos()

    def consulta(self):
        """Carga la pantalla de consulta (verificación) del voto en pantalla.
        """
        self.modulo.logger.info("Mostrando consulta")
        self.send_command("consulta")

    def candidatos_consulta(self, datos):
        """Carga los candidatos seleccionados en la pantalla de consulta."""
        self._datos_verificacion = datos
        candidatos = []
        # Recorremos todas las categorías y armamos una lista de todos los
        # candidatos selecionados
        for categoria in Categoria.all():
            candidato = datos.candidato_categoria(categoria.codigo)
            if candidato is not None:
                candidatos.extend(candidato)
        # mandamos solo los id_umv de los mismos
        cods_candidatos = [cand.id_umv for cand in candidatos]
        self.send_command("candidatos_consulta", cods_candidatos)

    def imagen_consulta(self):
        """Genera y envia la imagen de la consulta."""
        self.modulo.logger.info("Cargando imagen")
        muestra_svg = self.modulo.config("muestra_svg")

        mostrar = {"en_pantalla": True}
        imagen = self._datos_verificacion.a_imagen(mostrar, svg=muestra_svg)
        # si no mandamos el SVG armamos un png y lo base64 encodeamos.
        if not muestra_svg:
            buffer = BytesIO()
            imagen.save(buffer, format="PNG")
            img_data = encodestring(buffer.getvalue())
            imagen = "data:image/png;base64,%s" % img_data.decode()

        image_data = quote(imagen.encode("utf-8"))
        self.send_command("imagen_consulta", image_data)

        # Borramos los datos de la verificación, ya no los necesitamos más.
        self._datos_verificacion = None

    @solo_votando
    def get_pantalla_modos(self):
        """Muestra la pantalla de modos."""
        self.send_command("cargar_pantalla_inicial")

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
        """Envia los datos de las candidaturas a la UI."""
        datos = {}
        datos['categorias'] = self.dict_set_categorias()
        datos['candidaturas'] = self.dict_set_candidaturas()
        datos['agrupaciones'] = self.dict_set_agrupaciones()
        datos['boletas'] = self.dict_set_boletas()
        self.send_command("cargar_datos", datos)

    def dict_set_categorias(self):
        """Envia el diccionario con los datos de las categorias."""
        categorias = Categoria.all()
        return categorias.to_dict()

    def dict_set_boletas(self):
        """Envia el diccionario con los datos de las listas completas."""
        boletas = Boleta.all()
        return boletas.to_dict()

    def dict_set_candidaturas(self):
        """Envia el diccionario con los datos de las candidaturas."""
        candidatos = Candidatura.all()
        return candidatos.to_dict()

    def dict_set_agrupaciones(self):
        """Envia el diccionario con los datos de las agrupaciones."""
        candidatos = Agrupacion.all()
        return candidatos.to_dict()

    def get_encabezado(self):
        """Devuelve los datos para el encabezado."""
        encabezado = get_config('datos_eleccion')
        """
        if self.sesion.mesa is not None and \
                self.sesion.mesa.municipio is not None:
            encabezado = copy(encabezado)
            encabezado["fecha"] += " - {}".format(self.sesion.mesa.municipio)
        """
        return encabezado

    def get_constants(self):
        """Genera las constantes que se van a usar en la UI."""
        flavor = self.modulo.config("flavor")

        usar_asistida = self.modulo.config("usar_asistida")
        mostrar_indicador_capacitacion = \
            self.modulo.config("mostrar_indicador") and \
            (self.modulo.nombre == MODULO_CAPACITACION)

        local_constants = {
            "asistida": False,
            "cod_lista_blanco": COD_LISTA_BLANCO,
            "numeros_templates": NUMEROS_TEMPLATES[flavor],
            "shuffle": self.get_shuffle_configs(),
            "templates": self.get_templates_flavor(),
            "tiempo_feedback": 150,
            "ubicacion": getattr(self.sesion.mesa, "codigo", None),
            "usar_asistida": usar_asistida,
            "mostrar_indicador_capacitacion": mostrar_indicador_capacitacion,
        }

        constants_dict = self.base_constants_dict()
        constants_dict.update(local_constants)
        constants_dict.update(self.map_configs())

        return constants_dict

    def map_configs(self):
        """Devuelve todas configs para mandarle a la UI."""
        configs = [
            "agrupar_por_partido", "agrupar_cargo", "colapsar_listas",
            "colapsar_candidatos", "paso", "categoria_agrupa_por", "interna",
            "confirmacion_lateral", "mostrar_adheridas_confirmacion",
            "limitar_candidatos", "precachear_imagenes", "muestra_svg",
            "seleccionar_lista_unica", "seleccionar_candidato_unico",
            "mostrar_blanco_siempre", "botones_seleccion_modo",
            "mostrar_fotos_candididatos_boton_partido",
            "mostrar_barra_seleccion", "boton_modificar_en_lista_completa",
            "boton_modificar_en_categorias",
            "no_repetir_lista_partido_iguales",
            "boton_modificar_con_una_categroria", "templates_compiladas",
            "solapa_inteligente"
        ]

        config_map = {config: self.modulo.config(config) for config in configs}
        return config_map

    def get_shuffle_configs(self):
        shuffle_dict = {
            'por_sesion': self.modulo.config("mezclar_por_sesion"),
            'candidatos': self.modulo.config("mezclar_candidatos"),
            'listas': self.modulo.config("mezclar_listas"),
            'internas': self.modulo.config("mezclar_agrupaciones"),
            'consultas': self.modulo.config("mezclar_consulta")
        }
        return shuffle_dict

    def get_templates_flavor(self):
        """Devuelve las templates a precachear."""
        template_names = ("candidato", "categoria", "lista",
                          "partido", "candidato_hijo", "confirmacion",
                          "consulta_popular", "candidatos_adicionales",
                          "colores", "candidato_verificacion", "solapa")
        return template_names

    def get_templates_modulo(self):
        template_names = [
            "agradecimiento", "asistida", "candidatos", "confirmacion",
            "consulta_popular", "consulta_seleccion", "contenedor_listas",
            "context/alto_contraste", "context/barra_opciones",
            "context/btn_regresar", "context/candidatos_seleccionados",
            "context/confirmar_seleccion", "context/no_confirmar_voto",
            "context/si_confirmar_voto", "context/voto_blanco", "idioma",
            "idiomas", "insercion_boleta", "loading", "mensaje_final", "menu",
            "pantalla_modos", "context/btn_agrupaciones_municipales",
        ]
        return template_names
