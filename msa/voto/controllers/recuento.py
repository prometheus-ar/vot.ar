# -*- coding: utf-8 -*-
import os

from urllib2 import quote

from zaguan import WebContainerController
from zaguan.actions import BaseActionController

from msa.constants import COD_LISTA_BLANCO
from msa.core import get_tipo_elec, get_config
from msa.core.audioplayer import WavPlayer
from msa.core.data.candidaturas import Categoria, Candidato, Lista
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.core.constants import CIERRE_ESCRUTINIO, CIERRE_TRANSMISION
from msa.core.imaging import ImagenReversoBoleta
from msa.core.settings import USAR_QR, USA_ARMVE, ACTA_DESGLOSADA
from msa.voto.constants import RECUENTO_OK, RECUENTO_ERROR, \
    RECUENTO_ERROR_REPETIDO, RECUENTO_NO_TAG, RECUENTO_VER_RESULTADOS,\
    RECUENTO_RECUENTO_OK, RECUENTO_RECUENTO_ERROR, RECUENTO_IMPRIMIENDO,\
    RECUENTO_GENERANDO, SECUENCIA_CERTIFICADOS, E_RESULTADO, \
    CONFIG_BOLETA_CIERRE, CONFIG_BOLETA_ESCRUTINIO, CONFIG_BOLETA_TRANSMISION
from msa.voto.sesion import get_sesion
from msa.voto.settings import MOSTRAR_CURSOR, PATH_TEMPLATES_VOTO,\
    EXT_IMG_VOTO, PATH_SONIDOS_VOTO, VOLUMEN_GENERAL, EFECTOS_RECUENTO,\
    FLAVOR


_audio_player = None


class Actions(BaseActionController):

    def document_ready(self, data):
        self.controller.send_constants()
        self.controller.set_pantalla_recuento()
        self.controller.parent._inicio()

    def administrador(self, data):
        self.controller.parent.administrador()

    def salir(self, data):
        self.controller.parent.salir()

    def terminar_escrutinio(self, data):
        self.controller.parent._finalizar()

    def set_campos_extra(self, data):
        self.controller.parent.set_campos_extra(data)
        self.controller.set_pantalla_preimpresion()

    def imprimir(self, data):
        self.controller.parent._imprimir()

    def copiar_certificados(self, data):
        self.controller.parent.copiar_certificados()

    def dialogo(self, data):
        self.controller.procesar_dialogo(data)

    def volver(self, data):
        self.controller.parent.volver()

    def log(self, data):
        self.sesion.logger.debug("LOG >>>%s" % data)


class ControllerRecuento(WebContainerController):

    """Controller para la interfaz web de recuento."""

    def __init__(self, parent):
        global _audio_player
        super(ControllerRecuento, self).__init__()
        self.sesion = get_sesion()
        self.parent = parent
        self.partido = None
        self.add_processor("recuento", Actions(self))

        self.callback_aceptar = None
        self.callback_cancelar = None

        self.msjs_panel = {
            RECUENTO_OK: (_("lectura_ok"),
                          os.path.join(PATH_SONIDOS_VOTO, 'ok.wav')),
            RECUENTO_ERROR: (_("error_lectura"),
                             os.path.join(PATH_SONIDOS_VOTO, 'error.wav')),
            RECUENTO_ERROR_REPETIDO: (_("boleta_repetida"),
                                      os.path.join(PATH_SONIDOS_VOTO,
                                                   'warning.wav')),
            RECUENTO_NO_TAG: (_("listo_para_leer"), None),
            RECUENTO_VER_RESULTADOS: (None, None),
            RECUENTO_RECUENTO_OK: (_("guardado_correc"), None),
            RECUENTO_RECUENTO_ERROR: (_("error_escribir_rec"), None),
            RECUENTO_IMPRIMIENDO: (_("mensaje_imprimiendo"), None),
            RECUENTO_GENERANDO: (_("mensaje_generando"), None)
        }

        if not _audio_player or not _audio_player.is_alive():
            _audio_player = WavPlayer()
            _audio_player.start()
            _audio_player.set_volume(VOLUMEN_GENERAL)
        self._player = _audio_player

    def _get_categorias(self):
        """Devuelve las categorias para esta mesa y para esta partido en caso
        de que sea ese tipo de eleccion."""
        if not get_tipo_elec("interna"):
            categorias = Categoria.many(sorted="posicion")
        else:
            cod_cats = set([candidato.categoria.codigo for candidato in
                            Candidato.many(cod_partido=self.partido.codigo)])
            categorias = Categoria.many(codigo__in=cod_cats, sorted="posicion")
        return categorias

    def _get_data_categorias(self, seleccion):
        """Devuelve la informacion de las categorias y los candidatos elegidos
        para cada una de ellas en caso de que los haya."""
        categorias = self._get_categorias()
        cat_list = []
        seleccion = self.sesion.ultima_seleccion
        for categoria in categorias:
            candidatos = seleccion.candidato_categoria(categoria.codigo)
            if candidatos is not None:
                for candidato in candidatos:
                    candidato_dict = candidato.full_dict(self._image_name)
                    cat_dict = {'categoria': categoria.to_dict(),
                                'candidato': candidato_dict}
                    # traduce el nombre de la categoria en caso de que sea necesario
                    cat_dict['categoria']['nombre'] = \
                        _(cat_dict['categoria']['nombre'])
                    cat_list.append(cat_dict)
                    candidato_dict['votos'] = \
                        self.sesion.recuento.obtener_resultado(
                            candidato.cod_categoria, candidato.codigo)
            else:
                cat_dict = {'categoria': categoria.to_dict(),
                            'candidato': None}
                cat_list.append(cat_dict)
        return cat_list

    def _get_data_listas(self):
        categorias = self._get_categorias()
        data_listas = [l for l in Lista.many(sorted='cod_partido,codigo')
                       if not l.es_blanco()]

        if get_tipo_elec("paso"):
            def _sort_listas_paso(lista_a, lista_b):
                return cmp((lista_a.partido.nombre.upper(), lista_a.numero),
                           (lista_b.partido.nombre.upper(), lista_b.numero))
            data_listas = sorted(data_listas, _sort_listas_paso)
        else:
            def _sort_listas(lista_a, lista_b):
                return cmp(int(lista_a.numero)if lista_a.numero != ""
                        else lista_a.codigo,
                        int(lista_b.numero)if lista_b.numero != ""
                        else lista_b.codigo)
            data_listas = sorted(data_listas, _sort_listas)

        lista_blanca = Lista.one(COD_LISTA_BLANCO)
        if lista_blanca is not None:
            data_listas.append(lista_blanca)
        listas = []
        principales = {(candidato.cod_lista, candidato.cod_categoria): candidato
                       for candidato in Candidato.many(titular=True,
                                                       numero_de_orden=1)}
        for lista in data_listas:
            lista_dict = lista.to_dict()
            if lista.partido is not None:
                lista_dict['nombre_partido'] = lista.partido.nombre
            lista_dict['candidatos'] = []
            for categoria in categorias:
                candidato = principales.get((lista.codigo, categoria.codigo))
                if candidato is not None:
                    candidato_dict = candidato.to_dict()
                    candidato_dict['votos'] = \
                        self.sesion.recuento.obtener_resultado(categoria.codigo,
                                                               candidato.codigo)
                else:
                    candidato_dict = None
                lista_dict['candidatos'].append(candidato_dict)
            listas.append(lista_dict)

        cat_list = []
        for categoria in categorias:
            cat_dict = categoria.to_dict()
            cat_dict['nombre'] = _(cat_dict['nombre'])
            cat_list.append(cat_dict)

        return cat_list, listas

    def _image_name(self, cod_candidato):
        if cod_candidato is not None:
            imagen = "%s.%s" % (cod_candidato, EXT_IMG_VOTO)
            path_foto = os.path.join(PATH_TEMPLATES_VOTO,
                                     "imagenes_candidaturas", JUEGO_DE_DATOS,
                                     imagen)
            if not os.path.exists(path_foto):
                imagen = None
        return imagen

    def get_imagen_acta(self, tipo=None):
        if tipo is None:
            if not ACTA_DESGLOSADA:
                tipo = (SECUENCIA_CERTIFICADOS[0], None)
            elif self.sesion.recuento.cod_categoria is not None:
                tipo = (SECUENCIA_CERTIFICADOS[0],
                        self.sesion.recuento.cod_categoria)
            else:
                primera_categoria = Categoria.one(sorted="posicion").codigo
                tipo = (SECUENCIA_CERTIFICADOS[0], primera_categoria)

        imagen = self.sesion.recuento.a_imagen(tipo, de_muestra=True, svg=True)
        image_data = quote(imagen.encode("utf-8"))
        return image_data

    def set_pantalla_recuento(self):
        num_mesa = self.sesion.recuento.mesa.descripcion.title()
        cant_leidas = self.sesion.recuento.boletas_contadas()

        if self.parent.estado == E_RESULTADO:
            self.set_pantalla_revision()
        else:
            cat_list, listas = self._get_data_listas()
            self.send_command("pantalla_recuento",
                              {"cat_list": cat_list,
                               "listas": listas,
                               "num_mesa": num_mesa,
                               "cant_leidas": cant_leidas})

    def set_pantalla_confirmacion(self):
        campos_recuento = self.parent.get_campos_extra()
        self.send_command("pantalla_confirmacion", campos_recuento)

    def set_pantalla_preimpresion(self):

        image_data = self.get_imagen_acta()
        campos_extra = self.parent.get_campos_extra()
        self.send_command("pantalla_preimpresion",
                          {"image_data": image_data,
                           "campos_extra": campos_extra})

    def set_pantalla_asistente_cierre(self):
        # TODO: Arreglar leak de archivos QR en /tmp/qr-*/
        qr = self.sesion.recuento.a_qr_b64_encoded(
            self.sesion.recuento.cod_categoria)
        self.parent.habilitar_impresion_certificados()
        self.send_command("pantalla_asistente_cierre", qr)

    def set_pantalla_impresion_certificados(self):
        qr = self.sesion.recuento.a_qr_b64_encoded(
            self.sesion.recuento.cod_categoria)
        self.send_command("pantalla_impresion_certificados", qr)

    def hide_pantalla_impresion_certificados(self):
        self.send_command("hide_pantalla_impresion_certificados")

    def set_pantalla_revision(self):
        cat_list, listas = self._get_data_listas()
        qr = self.sesion.recuento.a_qr_b64_encoded(
            self.sesion.recuento.cod_categoria)
        campos_extra = self.parent.get_campos_extra()
        num_mesa = self.sesion.recuento.mesa.descripcion.title()
        self.send_command("pantalla_revision", {"path_qr": qr,
                                                "num_mesa": num_mesa,
                                                "cat_list": cat_list,
                                                "listas": listas,
                                                "campos_extra": campos_extra})

    def actualizar_resultados(self, seleccion, cant_leidas, image_data):
        """ Actualiza la grilla de resultados del recuento """
        cat_list = self._get_data_categorias(seleccion)
        self.send_command("actualizar_resultados", {"seleccion": cat_list,
                                                    "cant_leidas": cant_leidas,
                                                    "image_data": image_data})

    def _get_imagen_reverso_acta(self, tipo):
        configs_svg = {
            'recuento': CONFIG_BOLETA_CIERRE,
            'transmision': CONFIG_BOLETA_TRANSMISION,
            'escrutinio': CONFIG_BOLETA_ESCRUTINIO,
            'copia_fiel': CONFIG_BOLETA_ESCRUTINIO,
            'certificado': CONFIG_BOLETA_ESCRUTINIO
        }
        return ImagenReversoBoleta(configs_svg[tipo]).render_svg()

    def pedir_acta(self, tipo):
        imagen = self._get_imagen_reverso_acta(tipo)
        self.send_command("pedir_acta",
                          {"tipo": tipo, "imagen": quote(imagen)})

    def mostrar_imprimiendo(self, tipo):
        imagen = self.get_imagen_acta(tipo=tipo)
        self.send_command("preview_acta",
                          {"imagen": imagen, "tipo": tipo})

    def procesar_dialogo(self, respuesta):
        if respuesta:
            if self.callback_aceptar is not None:
                self.callback_aceptar()
        else:
            if self.callback_cancelar is not None:
                self.callback_cancelar()

    def show_dialogo(self, mensaje, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=False,
                     btn_aceptar=False, error=False):
        self.callback_aceptar = callback_aceptar
        self.callback_cancelar = callback_cancelar
        dialogo = {"mensaje": mensaje,
                   "btn_aceptar": btn_aceptar,
                   "btn_cancelar": btn_cancelar}
        self.send_command("show_dialogo", dialogo)

    def hide_dialogo(self):
        self.send_command("hide_dialogo")

    def set_panel_estado(self, cod_mensaje):
        self.send_command("show_elements", "#panel_estado")
        sonido = self.msjs_panel[cod_mensaje][1]
        if sonido is not None:
            self._player.play(sonido)
        self.send_command("set_panel_estado", cod_mensaje)

    def ocultar_panel_estado(self):
        self.send_command("hide_elements", "#panel_estado")

    def hide_preview(self):
        self.send_command("hide_elements", ".contenedor-acta")

    def limpiar_panel_estado(self):
        self.send_command("limpiar_panel_estado")

    def cancelar_impresion(self):
        self.habilitar_botones()
        self.send_command("volver_a_campos")

    def deshabilitar_botones(self):
        self.send_command("hide_botones")
        self.send_command("hide_scroll_acta")
        self.send_command("hide_btn_qr")

    def habilitar_botones(self):
        self.send_command("show_botones")
        self.send_command("show_btn_qr")

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants()
        constants_dict["mensajes_panel"] = self.msjs_panel
        self.send_command("set_constants", constants_dict)


def get_constants():
        translations = ("si", "no", "ver_qr",
            "alto_contraste", "muchas_gracias", "puede_retirar_boleta",
            "si_desea_verificarlo", "imprimiendo_voto", "no_retirar_boleta",
            "agradecimiento", "cancelar", "volver_al_inicio", "salir",
            "terminar_escrutinio", "aceptar", "boletas_procesadas",
            "escrutinio_mesa", "iniciar_instructivo", "finalizar_instructivo",
            "bienvenida_recuento", "boleta_unica_electronica",
            "caracteristicas_pantalla", "slide_2_titulo", "slide_2_contenido",
            "slide_3_subtitulo", "slide_3_recuadro_1", "slide_3_recuadro_2",
            "slide_3_recuadro_3", "slide_4_subtitulo", "slide_4_recuadro_1",
            "slide_5_subtitulo", "slide_5_recuadro_1", "slide_6_titulo",
            "slide_6_subtitulo", "presione_imprimir", "fiscales_qr",
            "introduzca_acta_transmision", "introduzca_cerfificado_escrutinio",
            "asegurese_firmar_acta", "introduzca_certificado_boletas",
            "slide_2_bullet_1", "slide_2_bullet_2", "slide_2_bullet_3",
            "introduzca_sobre_actas", "slide_3_bullet_1", "slide_3_bullet_2",
            "slide_3_bullet_3", "slide_3_bullet_4", "slide_3_bullet_5",
            "entregue_certif_transmision", "el_suplente_acercara",
            "introduzca_certificados_para_fiscales", "usted_puede_imprimir",
            "introduzca_acta_cierre_nuevamente")
        encabezado = get_config('datos_eleccion')

        constants_dict = {
            "juego_de_datos": JUEGO_DE_DATOS,
            "cod_lista_blanco": COD_LISTA_BLANCO,
            "elecciones_internas": get_tipo_elec("interna"),
            "elecciones_paso": get_tipo_elec("paso"),
            "mostrar_cursor": MOSTRAR_CURSOR,
            "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
            "i18n": [(trans, _(trans)) for trans in translations],
            "palabra_lista": _("palabra_lista"),
            "palabra_nombre": _("palabra_nombre"),
            "palabra_categoria": _("palabra_categoria"),
            "palabra_siguiente": _("palabra_siguiente"),
            "palabra_anterior": _("palabra_anterior"),
            "palabra_imprimir": _("palabra_imprimir"),
            "terminar_escrutinio": _("terminar_escrutinio"),
            "terminar": _("terminar"),
            "salir": _("salir"),
            "sus_candidatos": _("sus_candidatos"),
            "candidato_no_seleccionado": _("candidato_no_seleccionado"),
            "cod_estado_espera": RECUENTO_NO_TAG,
            "cod_estado_ok": RECUENTO_OK,
            "cod_boleta_repetida": RECUENTO_ERROR_REPETIDO,
            "cod_error_lectura": RECUENTO_ERROR,
            "usar_qr": USAR_QR,
            "usa_armve": USA_ARMVE,
            "ext_img_voto": EXT_IMG_VOTO,
            "effects": EFECTOS_RECUENTO,
            "flavor": FLAVOR,
            "templates": get_templates(),
            "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO,
            "CIERRE_ESCRUTINIO": CIERRE_ESCRUTINIO,
            "CIERRE_TRANSMISION": CIERRE_TRANSMISION,
            "listas_especiales": get_config("listas_especiales"),
            "cod_estado_imprimiendo": RECUENTO_IMPRIMIENDO,
            "cod_estado_generando": RECUENTO_GENERANDO
        }
        return constants_dict


def get_templates():
    templates = {}
    template_names = ("candidato_recuento", )
    for template in template_names:
        file_name = "%s.html" % template
        template_file = os.path.join(FLAVOR, file_name)
        templates[template] = template_file
    return templates
