"""Controlador del modulo escrutinio."""
from base64 import encodestring
from io import BytesIO
from os.path import join
from urllib.parse import quote

from msa.constants import COD_LISTA_BLANCO
from msa.core.constants import PATH_TEMPLATES_VARS
from msa.core.data.candidaturas import Agrupacion, Candidatura, Categoria
from msa.core.documentos.constants import (CIERRE_CERTIFICADO,
                                           CIERRE_COPIA_FIEL,
                                           CIERRE_ESCRUTINIO, CIERRE_RECUENTO,
                                           CIERRE_TRANSMISION)
from msa.core.imaging.constants import (CONFIG_BOLETA_CIERRE,
                                        CONFIG_BOLETA_ESCRUTINIO,
                                        CONFIG_BOLETA_TRANSMISION)
from msa.core.imaging.reverso import ImagenReversoBoleta
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.constants import E_CLASIFICACION, E_RECUENTO, MODULO_INICIO
from msa.modulos.escrutinio.constants import (ACT_BOLETA_NUEVA,
                                              ACT_BOLETA_REPETIDA, ACT_ERROR,
                                              ACT_ESPECIALES, ACT_INICIAL,
                                              ACT_VERIFICAR_ACTA,
                                              MINIMO_BOLETAS_RECUENTO, TEXTOS)


class Actions(BaseActionController):

    def document_ready(self, data):
        self.controlador.send_constants()

    def cargar_cache(self, data):
        """Cachea los dos de candidaturas y los manda a la UI."""
        self.controlador.cargar_datos()

    def inicializar_interfaz(self, data):
        recuento = self.controlador.sesion.recuento
        reimpresion = hasattr(recuento, "reimpresion") and recuento.reimpresion
        if reimpresion:
            self.controlador.modulo.habilitar_copia_certificados()
        self.controlador.actualizar(ACT_INICIAL, reimpresion=reimpresion)


class Controlador(ControladorBase):

    """Controller para la interfaz web de recuento."""

    def __init__(self, modulo):
        super(Controlador, self).__init__(modulo)
        self.set_actions(Actions(self))
        self.textos = TEXTOS

    def cargar_datos(self):
        datos = {}
        datos['categorias'] = self.dict_set_categorias()
        datos['candidaturas'] = self.dict_set_candidaturas()
        datos['agrupaciones'] = self.dict_set_agrupaciones()
        self.send_command("cargar_datos", datos)

    def dict_set_categorias(self):
        """Envia el diccionario con los datos de las categorias."""
        categorias = Categoria.all().to_dict()
        return categorias

    def dict_set_candidaturas(self):
        """Envia el diccionario con los datos de las categorias."""
        candidatos = Candidatura.all().to_dict()
        return candidatos

    def dict_set_agrupaciones(self):
        """Envia el diccionario con los datos de las categorias."""
        candidatos = Agrupacion.all().to_dict()
        return candidatos

    def _datos_tabla(self):
        ret = {}
        resultados = self.sesion.recuento.get_resultados()

        for key, value in resultados.items():
            ret[key] = value
        return ret

    def actualizar(self, tipo_actualizacion, seleccion=None,
                   reimpresion=False):
        if (self.modulo.estado == E_RECUENTO or reimpresion
                or tipo_actualizacion == ACT_ESPECIALES):

            self.modulo.beep(tipo_actualizacion)

            recuento = self.sesion.recuento
            procesadas = recuento.boletas_contadas()

            upd_data = {
                "boletas_procesadas": procesadas,
                "datos_tabla": None,
                "imagen": None,
                "listas_especiales": None,
                "reimpresion": reimpresion,
                "seleccion": seleccion,
                "tipo": tipo_actualizacion,
                "total_general": None,
                "grupo_cat": recuento.grupo_cat,
            }

            if tipo_actualizacion in (ACT_BOLETA_NUEVA, ACT_BOLETA_REPETIDA):
                muestra_svg = self.modulo.config("muestra_svg")
                mostrar = {"en_pantalla": True}
                imagen = seleccion.a_imagen(mostrar, svg=muestra_svg)
                if not muestra_svg:
                    buffer = BytesIO()
                    imagen.save(buffer, format="PNG")
                    img_data = encodestring(buffer.getvalue())
                    imagen = "data:image/png;base64,%s" % img_data.decode()

                upd_data['imagen'] = quote(imagen.encode("utf-8"))
                if tipo_actualizacion == ACT_BOLETA_REPETIDA:
                    upd_data['seleccion'] = None

            if tipo_actualizacion == ACT_BOLETA_NUEVA:
                upd_data['seleccion'] = self.get_datos_seleccion(seleccion)

            if tipo_actualizacion in (ACT_INICIAL, ACT_BOLETA_NUEVA,
                                      ACT_ESPECIALES):
                upd_data['datos_tabla'] = self._datos_tabla()

            if tipo_actualizacion == ACT_ESPECIALES or reimpresion:
                upd_data["orden_especiales"] = recuento.mesa.listas_especiales
                upd_data["listas_especiales"] = recuento.listas_especiales
                upd_data["total_general"] = recuento.total_boletas()

            self.send_command("actualizar", upd_data)

    def get_datos_seleccion(self, seleccion):
        """Devuelve los candidatos de Una seleccion ordenados por categoria."""
        cand_seleccion = []
        for categoria in Categoria.many(sorted="posicion"):
            candidatos = seleccion.candidato_categoria(categoria.codigo)
            for candidato in candidatos:
                cand_seleccion.append(candidato.id_umv)

        return cand_seleccion

    def cargar_clasificacion_de_votos(self, data):
        self.modulo.estado = E_CLASIFICACION
        boletas_procesadas = self.sesion.recuento.boletas_contadas()
        total = self.sesion.recuento.total_boletas()
        listas_especiales = self.sesion.recuento.mesa.listas_especiales

        datos = {"boletas_procesadas": boletas_procesadas,
                 "boletas_totales": total,
                 "listas_especiales": listas_especiales}
        self.send_command("pantalla_clasificacion_votos", datos)

    def guardar_listas_especiales(self, data):
        for lista in self.sesion.recuento.mesa.listas_especiales:
            self.sesion.recuento.actualizar_lista_especial(lista,
                                                           data[lista])
        self.actualizar(ACT_ESPECIALES)

    def iniciar_secuencia_impresion(self, data=None):
        self.modulo.imprimir_documentos()

    def _get_imagen_reverso_acta(self, tipo):
        configs_svg = {
            CIERRE_RECUENTO: CONFIG_BOLETA_CIERRE,
            CIERRE_TRANSMISION: CONFIG_BOLETA_TRANSMISION,
            CIERRE_ESCRUTINIO: CONFIG_BOLETA_ESCRUTINIO,
            CIERRE_COPIA_FIEL: CONFIG_BOLETA_ESCRUTINIO,
            CIERRE_CERTIFICADO: CONFIG_BOLETA_ESCRUTINIO
        }
        return ImagenReversoBoleta(configs_svg[tipo]).render_svg()

    def pedir_acta(self, tipo):
        imagen = self._get_imagen_reverso_acta(tipo)
        self.send_command("pantalla_pedir_acta",
                          {"tipo": tipo, "imagen": quote(imagen)})

    def set_pantalla_asistente_cierre(self):
        usar_qr = self.modulo.config("usar_qr")
        qr = self.sesion.recuento.a_qr_b64_encoded(
            self.sesion.recuento.grupo_cat) if usar_qr else None
        self.send_command("pantalla_asistente_cierre", qr)

    def set_pantalla_anterior_asistente(self):
        self.send_command("show_slide")

    def habilitar_recuento(self, data):
        self.modulo.estado = E_RECUENTO

    def preguntar_salida(self):
        self.send_command("preguntar_salida")

    def aceptar_salida(self, data):
        self.modulo.salir_a_modulo(MODULO_INICIO)

    def mostrar_imprimiendo(self):
        self.send_command("mensaje_imprimiendo")

    def mostrar_pantalla_copias(self):
        self.send_command("pantalla_copias")

    def apagar(self, data):
        self.modulo.apagar()

    def get_desc_especiales(self):
        desc_especiales = {}
        for lista in self.sesion.mesa.listas_especiales:
            file_name = "escrutinio/descripcion_votos_{}.txt".format(lista)
            path = join(PATH_TEMPLATES_VARS, file_name)
            with open(path, "r") as file_:
                desc_especiales[lista] = file_.read().strip()

        return desc_especiales

    def get_constants(self):
        textos_especiales = {lista: _("titulo_votos_{}".format(lista)) for
                             lista in self.sesion.mesa.listas_especiales}
        desc_especiales = self.get_desc_especiales()

        local_constants = {
            "cod_lista_blanco": COD_LISTA_BLANCO,
            "templates": self.get_templates(),
            "MINIMO_BOLETAS_RECUENTO": MINIMO_BOLETAS_RECUENTO,
            "titulos_especiales": textos_especiales,
            "tipo_act": {
                "ACT_INICIAL": ACT_INICIAL,
                "ACT_BOLETA_NUEVA": ACT_BOLETA_NUEVA,
                "ACT_BOLETA_REPETIDA": ACT_BOLETA_REPETIDA,
                "ACT_ERROR": ACT_ERROR,
                "ACT_ESPECIALES": ACT_ESPECIALES,
                "ACT_VERIFICAR_ACTA": ACT_VERIFICAR_ACTA,
            },
            "descripcion_especiales": desc_especiales,
            "TABLA_MUESTRA_ALIANZA": self.modulo.config("tabla_muestra_alianza"),
            "TABLA_MUESTRA_PARTIDO": self.modulo.config("tabla_muestra_partido"),
            "numero_mesa": self.sesion.recuento.mesa.numero,
            "USAR_NOMBRE_CORTO": self.modulo.config("usar_nombre_corto"),
            "USAR_COLOR": self.modulo.config("mostrar_color"),
            "USAR_NUMERO_LISTA": self.modulo.config("mostrar_numero_lista"),
            "totalizador": False,
            "muestra_svg": self.modulo.config("muestra_svg"),
            "templates_compiladas": self.modulo.config("templates_compiladas"),
        }
        constants_dict = self.base_constants_dict()
        constants_dict.update(local_constants)
        return constants_dict

    def get_templates(self):
        flavor = self.modulo.config("flavor")
        templates = {}
        template_names = ("candidato_recuento", )
        for template in template_names:
            file_name = "%s.html" % template
            template_file = join(flavor, file_name)
            templates[template] = template_file
        return templates

    def get_templates_modulo(self):
        templates = [
            "campo_extra", "candidato", "context/panel_acciones",
            "context/panel_asistente", "context/panel_blanco",
            "context/panel_clasificacion", "context/panel_copias",
            "context/panel_derecho", "context/panel_estado",
            "context/panel_finalizar", "context/tabla", "context/teclado",
            "copias", "imprimiendo", "loading", "mensaje_confirmar_apagar",
            "mensaje_fin_escrutinio", "mensaje_pocas_boletas", "mensaje_salir",
            "pantalla_boleta", "pantalla_boleta_error",
            "pantalla_boleta_repetida", "pantalla_clasificacion_votos",
            "pantalla_verificar_acta", "pantalla_clasificacion_votos",
            "pantalla_copias", "pantalla_inicial", "pedir_acta",
            "slides/certificados_extra", "slides/devolucion_sobre",
            "slides/devolucion_urna", "slides/firmar_acta",
            "slides/qr_fiscales", "tabla", "colores"
        ]
        return templates
