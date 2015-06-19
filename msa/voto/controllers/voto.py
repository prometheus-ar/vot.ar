# -*- coding: utf-8 -*-
import os

from copy import copy
from urllib2 import quote
from random import shuffle
from time import sleep

from zaguan.actions import BaseActionController
from zaguan import WebContainerController

from msa.constants import COD_LISTA_BLANCO
from msa.core import get_tipo_elec, get_config
from msa.core.clases import Seleccion
from msa.core.data import TemplateImpresion, TemplateMap
from msa.core.data.candidaturas import Categoria, Candidato, Lista, Partido, \
    Alianza, Boleta
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.core.settings import USA_ARMVE, USAR_BUFFER_IMPRESION
from msa.helpers import cambiar_locale
from msa.voto.constants import BOTON_VOTAR_POR_CATEGORIAS, \
    PANTALLA_CONSULTA, BOTON_LISTA_COMPLETA, NUMEROS_TEMPLATES, E_VOTANDO
from msa.voto.controllers.helpers import _image_name
from msa.voto.sesion import get_sesion
from msa.voto.settings import BOTONES_SELECCION_MODO, MOSTRAR_CURSOR, \
    PATH_TEMPLATES_VOTO, EXT_IMG_VOTO, MEZCLAR_CANDIDATOS, MEZCLAR_LISTAS, \
    MEZCLAR_INTERNAS, IDIOMAS_DISPONIBLES, EFECTOS_VOTO, FLAVOR, \
    MEZCLAR_CONSULTA, AGRUPAR_POR_PARTIDO, BARRA_SELECCION, \
    AGRUPAR_POR_ALIANZA


def solo_votando(func):
    def _inner(self, *args, **kwargs):
        if self.parent.estado == E_VOTANDO:
            return func(self, *args, **kwargs)
        else:
            self.parent.rampa.maestro()
    return _inner


class Actions(BaseActionController):

    def document_ready(self, data):
        self.controller.parent.rampa.expulsar_boleta()
        self.controller.mostrar_loader()

    def cargar_cache(self, data):
        self.controller._precache_datos()
        #self.controller._precache_generacion_img()
        self.controller.ocultar_loader()

    def inicializar_interfaz(self, data):
        parent = self.controller.parent
        parent.pantalla_insercion()

    def cargar_categorias(self, data):
        self.controller.cargar_categorias(force=True, force_cat=data[0])

    def get_pantalla_voto(self, data):
        self.controller.parent.get_pantalla_inicial_voto()

    def get_partidos(self, data):
        self.controller.set_pantalla_partidos()

    def reiniciar_seleccion(self, data):
        self.reiniciar_seleccion()

    def prepara_impresion(self, data):
        self.controller.prepara_impresion()

    def imagen_consulta(self, data):
        self.controller.imagen_consulta()

    def dialogo(self, data):
        self.controller.procesar_dialogo(data)

    def log(self, data):
        self.sesion.logger.debug("LOG >>> %s" % data)


class ControllerVoto(WebContainerController):

    """Controller para la interfaz web de voto."""

    def __init__(self, parent):
        super(ControllerVoto, self).__init__()
        self.sesion = get_sesion()
        self.parent = parent
        self.agrupador = Alianza if AGRUPAR_POR_ALIANZA else Partido
        self._cache_categorias = {}
        self.agrupacion = None
        self.precache_data()
        self.add_processor("voto", Actions(self))

    def mostrar_loader(self):
        self.send_constants()
        self.send_command("mostrar_loader")

    def ocultar_loader(self):
        self.send_command("ocultar_loader")

    def precache_data(self):
        classes = (Candidato, Categoria, Partido, Alianza, Lista,
                   TemplateImpresion, TemplateMap)
        for class_ in classes:
            class_.all()

    @solo_votando
    def confirmar_seleccion(self, data):
        self.parent._guardar_voto()
        self.reiniciar_seleccion()

    def _get_categorias(self, consulta_popular=False, todas=False):
        """Devuelve las categorias para esta mesa y para esta partido en caso
        de que sea una interna no PASO."""
        if not get_tipo_elec("interna"):
            filter = {'sorted': "posicion",
                      'consulta_popular': consulta_popular}
            if not todas:
                filter['adhiere'] = None
            categorias = Categoria.many(**filter)
        else:
            candidatos = Candidato.many(cod_partido=self.agrupacion.codigo)
            cod_cats = set([candidato.categoria.codigo for candidato in
                            candidatos])
            filter = {'sorted': "posicion",
                      'consulta_popular': consulta_popular,
                      'codigo__in': cod_cats}
            if not todas:
                filter['adhiere'] = None
            categorias = Categoria.all(**filter)
        return categorias

    def get_data_categorias(self, consulta_popular=False, todas=False):
        """Devuelve la informacion de las categorias y los candidatos elegidos
        para cada una de ellas en caso de que los haya."""
        categorias = self._get_categorias(consulta_popular, todas)
        cat_list = []
        for categoria in categorias:
            candidatos = self.parent.seleccion.candidato_categoria(
                categoria.codigo)
            categoria_dict = categoria.to_dict()
            # si la categoria tiene algun candidato seleccionado
            if candidatos is not None:
                for candidato in candidatos:
                    # vamos a devolver una categoria por candidato, despues la
                    # parte del JS lo sabe manejar bien.
                    candidato_dict = candidato.full_dict(_image_name)
                    cat_dict = {'categoria': categoria_dict,
                                'candidato': candidato_dict}
                    cat_list.append(cat_dict)
            else:
                cat_dict = {'categoria': categoria_dict,
                            'candidato': None}
                cat_list.append(cat_dict)
        return cat_list

    @solo_votando
    def cargar_categorias(self, force=False, force_cat=None):
        """Envia el comando de cargar categorias o el comando de mostrar
        confirmacion dependiendo del contexto.
        En caso de que haya una categoria que no se voto o se este modificando
        una categoria envia el comando "cargar_categorias" en caso de que las
        categorias ya esten llenas envia el comando de mostrar confirmacion.
        """
        cat_list = self.get_data_categorias()
        next_cat = self.get_next_cat()

        run_command = True
        if next_cat is None:
            # este es el caso en que no tenemos ninguna categoria sin candidatos
            # seleccionados.
            if force:
                if force_cat is None:
                    # si ya esta todo lleno y no forzamos ninguna categoria
                    # vamos a la primera
                    next_cat = self._get_categorias()[0].codigo
                else:
                    # este es el caso en el que forzamos una categoria
                    categoria = Categoria.one(force_cat)
                    if not categoria.consulta_popular:
                        # tenemos que ver si la categoria que forzamos esta
                        # adherida a otra categoria y cambiar por la madre en
                        # caso de que sea asi.
                        madre = categoria.get_madre()
                        if madre is not None:
                            next_cat = madre.codigo
                        else:
                            next_cat = force_cat
                    else:
                        # si la categoria que forzamos es una consulta_popular
                        # vamos a levantara en modo consulta_popular
                        self.mostrar_consulta_popular(force_cat)
                        run_command = False
            else:
                # si no hay siguiente categoria quiere decir que tenemos que
                # llamar a la confirmacion
                self.mostrar_confirmacion()
                run_command = False

        if run_command:
            # solo va a entrar aca el caso de haber una proxima categoria que no
            # sea consulta popular
            self.send_command("cargar_categorias", [cat_list, next_cat])

    @solo_votando
    def get_next_cat(self, consulta_popular=False):
        """Devuelve el codigo de la proxima categoria sin votos."""
        ret = None
        categorias = self._get_categorias(consulta_popular)
        for categoria in categorias:
            candidato = self.parent.seleccion.candidato_categoria(
                categoria.codigo)
            if candidato is None:
                ret = categoria.codigo
                break

        return ret

    def _precache_datos(self):
        sleep(0.1)
        self.sesion.logger.debug("cacheando categorias")
        alianzas = self.agrupador.all()
        for categoria in Categoria.all():
            candidatos = self._get_candidatos_categoria(categoria.codigo, None)
            if len(candidatos) > get_tipo_elec("colapsar_listas"):
                for alianza in alianzas:
                    if len(alianza.listas) > 10:
                        self._get_candidatos_categoria(categoria.codigo,
                                                       alianza.codigo)
        self.sesion.logger.debug("cacheando listas")
        for lista in Lista.all():
            self._get_dict_lista(lista)

        self.sesion.logger.debug("cacheando partidos")
        self._get_partidos()
        self.sesion.logger.debug("fin cache")

    def _precache_generacion_img(self):
        #Imagen dummy para importar lo relacionado a generar imagenes
        test_seleccion = Seleccion(self.sesion.mesa)
        test_seleccion.rellenar_de_blanco()
        test_seleccion.a_imagen(svg=True)
        del test_seleccion

    def _get_candidatos_categoria(self, cod_categoria, cod_partido):
        key = (cod_categoria, cod_partido)
        if key in self._cache_categorias:
            cand_list = self._cache_categorias[key]
        else:
            categoria = Categoria.one(cod_categoria)
            candidatos = categoria.candidatos(cod_partido, self.agrupador)
            cand_list = [candidato.full_dict(_image_name) for candidato in
                         candidatos]
            self._cache_categorias[key] = cand_list
        return cand_list

    def _get_dict_lista(self, lista):
        key = ("dict_lista", lista.codigo)
        if key in self._cache_categorias:
            listas_dict = self._cache_categorias[key]
        else:
            listas_dict = []
            candidatos = lista.candidatos

            if len(candidatos):
                lista_dict = lista.to_dict()
                lista_dict['imagen'] = _image_name(lista.codigo)
                lista_dict['candidatos'] = []

                for cand in candidatos:
                    candidato_dict = cand.full_dict(_image_name,
                                                    secundarios=False,
                                                    suplentes=False)
                    candidato_dict['categoria'] = cand.categoria.nombre
                    lista_dict['candidatos'].append(candidato_dict)

                listas_dict.append(lista_dict)
            self._cache_categorias[key] = listas_dict
        return listas_dict

    @solo_votando
    def cargar_candidatos(self, cod_categoria, cod_partido=None):
        """"Envia los candidatos a la interfaz web."""
        if self.agrupacion is not None and cod_partido is None:
            cod_partido = self.agrupacion.codigo

        cand_list = self._get_candidatos_categoria(cod_categoria, cod_partido)

        if MEZCLAR_CANDIDATOS:
            shuffle(cand_list)

        # si es una PASO y hay mas listas de las permitidas agrupamos por
        # Partido o Alianza segun sea el caso
        if cod_partido is None and get_tipo_elec("paso") and len(cand_list) > \
                get_tipo_elec("colapsar_listas"):

            partidos = {}
            for candidato in cand_list:
                cod_partido = candidato['partido']['codigo']
                if cod_partido not in partidos:
                    candidato['partido']['imagen'] = _image_name(cod_partido)
                    partidos[cod_partido] = candidato['partido']

            partidos = partidos.values()
            shuffle(partidos)

            self.send_command("cargar_partido_categorias",
                              {'candidatos': cand_list,
                               'cod_categoria': cod_categoria,
                               'partidos': partidos,
                               'agrupador': self.agrupador.__name__.lower()})
        else:
            # En caso de que haya un solo candidato lo seleccionamos y pasamos
            # a la proxima categoria, esto es porque puede pasar que la
            # organizacion politica tenga una sola lista
            if len(cand_list) == 1:
                self.seleccionar_candidatos([cod_categoria,
                                            [cand_list[0]['codigo']]])
            else:
                self.send_command("cargar_candidatos",
                                  {'candidatos': cand_list,
                                   'cod_categoria': cod_categoria})

    @solo_votando
    def mostrar_consulta_popular(self, cod_categoria):
        candidatos = Candidato.principales(cod_categoria)
        candidatos_dict = candidatos.full_dict(_image_name)

        if MEZCLAR_CONSULTA:
            shuffle(candidatos_dict)

        self.send_command("cargar_consulta_popular", [candidatos_dict,
                                                      cod_categoria])

    @solo_votando
    def mostrar_confirmacion(self):
        """Envia el comando para mostrar confirmacion. En caso de haber
           Consultas Populares disponibles en las que no hayamos votadonos la
           va a mostrar.
        """
        next_cat_consulta = None
        consultas = self.get_data_categorias(consulta_popular=True)
        if len(consultas):
            next_cat_consulta = self.get_next_cat(consulta_popular=True)

        if next_cat_consulta is not None:
            self.mostrar_consulta_popular(next_cat_consulta)
        else:
            cat_list = self.get_data_categorias(todas=True)
            cat_list += consultas
            self.send_command("mostrar_confirmacion", cat_list)

    def previsualizar_voto(self, data):
        imagen = self.parent.seleccion.a_imagen(verificador=False,
                                                solo_mostrar=True, svg=True)
        image_data = quote(imagen.encode("utf-8"))
        self.send_command("mostrar_voto", image_data)

    @solo_votando
    def prepara_impresion(self):
        self.parent.registrador._prepara_impresion(self.parent.seleccion)

    @solo_votando
    def seleccionar_candidatos(self, data):
        """Selecciona el candidato y envia el comando para cargar las
        categorias.
        """
        cod_categoria, cod_candidatos = data
        muchos_candidatos = len(cod_candidatos) > 1

        if muchos_candidatos:
            self.parent.seleccion.borrar_categoria(cod_categoria)

        for elem in data[1]:
            candidato = Candidato.one(elem)
            self.parent.seleccion.elegir_candidato(candidato,
                                                   not muchos_candidatos)

        categoria = Categoria.one(cod_categoria)
        if categoria.consulta_popular:
            self.mostrar_confirmacion()
        else:
            self.cargar_categorias()

    @solo_votando
    def seleccionar_partido(self, data):
        """Selecciona el partido y envia el comando para ver la pantalla de
        modos.
        """
        if data[1] is None:
            self.agrupacion = self.agrupador.one(data[0])
        if get_tipo_elec("paso"):
            if data[1] is None:
                self.cargar_listas()
            else:
                self.cargar_candidatos(data[1], data[0])
        else:
            self.get_pantalla_modos()

    @solo_votando
    def seleccionar_lista(self, data):
        """Selecciona la lista y envia el comando para ver la pantalla de
        confirmacion.
        """
        cod_lista, categoria_adhesion, cod_candidatos, es_ultima = data
        if es_ultima or cod_lista == COD_LISTA_BLANCO:
            lista = Lista.one(cod_lista)
            for candidato in lista.candidatos:
                if not candidato.categoria.consulta_popular:
                    self.parent.seleccion.elegir_candidato(candidato)
            self.parent.seleccion.rellenar_de_blanco()

            categorias = self.get_data_categorias()
            self.send_command("actualizar_categorias", categorias)
            self.mostrar_confirmacion()
        else:
            if cod_candidatos is None:
                cod_candidatos = []
            self.cargar_listas(cod_candidatos + [cod_lista],
                               categoria_adhesion)

    @solo_votando
    def seleccionar_modo(self, modo):
        """Envia el comando de cargar categorias o el de cargar listas
        dependiendo del modo de votacion elegido.
        """
        self.reiniciar_seleccion()
        if get_tipo_elec("paso"):
            self.agrupacion = None

        if modo == BOTON_VOTAR_POR_CATEGORIAS:
            self.cargar_categorias()
        elif modo == BOTON_LISTA_COMPLETA:
            if get_tipo_elec("paso"):
                self.set_pantalla_partidos()
            else:
                self.cargar_listas()

    @solo_votando
    def seleccionar_idioma(self, idioma):
        cambiar_locale(idioma)
        self.send_constants()
        if get_tipo_elec("interna"):
            self.set_pantalla_partidos()
        else:
            self.get_pantalla_modos()

    def _contiene(self, hash_lista, candidatos):
        contiene = True
        for i in range(len(candidatos)):
            if candidatos[i] != hash_lista[i]:
                contiene = False
                break
        return contiene

    def _matchea_adhesiones(self, cod_candidatos, listas, cat):
        lis_con_cand = []
        for lista in listas:
            if self._contiene(lista['hash'], cod_candidatos):
                lis_con_cand.append(lista)
        return lis_con_cand

    def _cat_con_adh(self, listas, cat, search_cat, cod_candidatos,
                     repite=False):
        if cat is not None and len(cod_candidatos):
            lis_con_cand = self._matchea_adhesiones(cod_candidatos, listas,
                                                    cat)
            listas = lis_con_cand
        ids_lista = set()
        listas_filtradas = []
        for lista in listas:
            for candidato in lista['candidatos']:
                if candidato['cod_categoria'] == search_cat.codigo:
                    if candidato['codigo'] in ids_lista:
                        repite = True
                    else:
                        ids_lista.add(candidato['codigo'])
                        listas_filtradas.append(candidato)
        next_search_cat = search_cat.next(consulta_popular=False)
        if (len(listas_filtradas) == len(listas) or
            len(listas_filtradas) < 2 or
            get_tipo_elec("adh_segmentada_nivel") <= len(cod_candidatos)) and \
                next_search_cat is not None:

            repite, listas_filtradas, next_search_cat = \
                self._cat_con_adh(listas, cat, next_search_cat, cod_candidatos,
                                  repite)

        return repite, listas_filtradas, next_search_cat

    @solo_votando
    def cargar_listas(self, cod_candidatos=None, cat=None):
        """Envia el comando para cargar las listas."""
        if cod_candidatos is None:
            cod_candidatos = []
        cod_partido = self.agrupacion.codigo if self.agrupacion is not None \
            else None
        if cod_partido is None:
            listas = Lista.all()
        else:
            listas = self.agrupador.one(cod_partido).listas
        listas_dict = []

        if MEZCLAR_LISTAS:
            listas.shuffle()

        for lista in listas:
            candidatos = lista.candidatos
            if len(candidatos):
                hash_lista = [candidato.codigo for candidato in candidatos]
                lista_dict = lista.to_dict()
                lista_dict['hash'] = hash_lista
                lista_dict['imagen'] = _image_name(lista.codigo)
                lista_dict['candidatos'] = []

                for candidato in candidatos:
                    candidato_dict = candidato.full_dict(_image_name)
                    candidato_dict['hash_lista'] = hash_lista
                    candidato_dict['categoria'] = candidato.categoria.nombre
                    lista_dict['candidatos'].append(candidato_dict)

                listas_dict.append(lista_dict)

        if get_tipo_elec("adh_segmentada"):
            if cat is None:
                search_cat = Categoria.one(sorted="posicion")
            else:
                cat = Categoria.one(cat)
                search_cat = cat.next(consulta_popular=False)
            repite, listas_filtradas, next_search_cat = \
                self._cat_con_adh(listas_dict, cat, search_cat, cod_candidatos)
            if repite and next_search_cat is not None:
                listas_dict = listas_filtradas
                ultima_cat = False
            else:
                ultima_cat = True
                listas_finales = []
                for lista in listas_dict:
                    for candidato in listas_filtradas:
                        if lista['hash'] == candidato['hash_lista']:
                            listas_finales.append(lista)
                listas_dict = listas_finales

        if len(listas_dict) > 1:
            if get_tipo_elec("adh_segmentada") and repite and \
                get_tipo_elec("adh_segmentada_nivel") > len(cod_candidatos):

                    self.send_command("cargar_adhesiones",
                                      [listas_dict, search_cat.codigo,
                                       cod_candidatos, ultima_cat])
            else:
                self.send_command("cargar_listas_params", [listas_dict, None,
                                  cod_candidatos])
        else:
            self.seleccionar_lista([listas_dict[0]['codigo'], None, None,
                                    True])

    def consulta(self, seleccion_tag):
        try:
            self._datos_verificacion = seleccion_tag
            imagen = self._datos_verificacion.a_imagen(verificador=False,
                                                       solo_mostrar=True,
                                                       svg=True)
            self._imagen_verificacion = imagen
            self.set_screen(PANTALLA_CONSULTA)
        except AttributeError:
            self.parent.rampa.expulsar_boleta()

    def imagen_consulta(self):
        # Sr. desarrollador, resista la tentacion de mandar base64 encoded
        # SVG es mas rapido
        image_data = quote(self._imagen_verificacion.encode("utf-8"))
        self.send_command("imagen_consulta", image_data)
        self._imagen_verificacion = None
        self._datos_verificacion = None

    @solo_votando
    def get_candidatos(self, data):
        """Devuelve los candidatos para la proxima categoria vacia. En caso de
        estar llenos los candidatos muestra la confimacion.
        """
        cod_categoria, revisando, partido = data
        if not revisando:
            if cod_categoria is None:
                cod_categoria = self.get_next_cat()
            if cod_categoria is None:
                self.mostrar_confirmacion()
            else:
                self.cargar_candidatos(cod_categoria, partido)
        else:
            if cod_categoria is None:
                cod_categoria = self._get_categorias()[0].codigo
            self.cargar_candidatos(cod_categoria, partido)

    def _get_partidos(self):
        """Devuelve las partidos."""
        key = "partidos"
        if key in self._cache_categorias:
            partidos = self._cache_categorias.get(key)
        else:
            partidos = [agr.full_dict(_image_name, listas=False) for agr in
                        self.agrupador.all() if not agr.es_blanco()]
            self._cache_categorias[key] = partidos

        if MEZCLAR_INTERNAS:
            shuffle(partidos)
        return partidos

    @solo_votando
    def get_pantalla_modos(self):
        """Devuelve la pantalla de modos. En caso de que las listas sean para
        una sola categoria se saltea la pantalla de modos y directo va a
        lista completa.
        """
        if len(BOTONES_SELECCION_MODO) > 1 and len(self._get_categorias()) > 1:
            self.send_command("pantalla_modos", BOTONES_SELECCION_MODO)
        elif len(BOTONES_SELECCION_MODO) == 1 and \
            BOTONES_SELECCION_MODO[0] == BOTON_LISTA_COMPLETA:

            self.send_command("guardar_modo", BOTON_LISTA_COMPLETA)
            self.send_command("set_unico_modo", True)
            self.seleccionar_modo(BOTON_LISTA_COMPLETA)
        else:
            self.send_command("guardar_modo", BOTON_VOTAR_POR_CATEGORIAS)
            self.send_command("set_unico_modo", True)
            self.seleccionar_modo(BOTON_VOTAR_POR_CATEGORIAS)

    @solo_votando
    def set_pantalla_partidos(self):
        """Envia el comando para mostrar los botones para seleccionar la
        partido.
        """
        partidos = self._get_partidos()
        listas = Lista.all()

        if not get_tipo_elec("interna") and len(partidos) == len(listas):
            self.cargar_listas()
        else:
            self.send_command("seleccion_partido", partidos)

    @solo_votando
    def set_pantalla_idiomas(self):
        self.send_command("pantalla_idiomas", IDIOMAS_DISPONIBLES)

    def procesar_dialogo(self, respuesta):
        if(respuesta):
            if self.callback_aceptar is not None:
                self.callback_aceptar()
        else:
            if self.callback_cancelar is not None:
                self.callback_cancelar()

    def show_dialogo(self, mensaje, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=False,
                     btn_aceptar=False):
        self.callback_aceptar = callback_aceptar
        self.callback_cancelar = callback_cancelar
        dialogo = {"mensaje": mensaje,
                   "btn_aceptar": btn_aceptar,
                   "btn_cancelar": btn_cancelar}
        self.send_command("show_dialogo", dialogo)

    def hide_dialogo(self):
        self.send_command("hide_dialogo")

    def reiniciar_seleccion(self):
        """Resetea la seleccion. Elimina lo que el usuario eligió."""
        self.parent.seleccion = Seleccion(self.sesion.mesa)

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants(self.sesion.mesa.codigo,
                                       self.sesion.mesa.departamento,
                                       self.sesion.mesa.municipio)
        self.send_command("set_constants", constants_dict)


def get_constants(ubicacion=None, departamento=None, municipio=None):
    translations = (
        "conformar_voto", "si",
        "votar_por_categorias", "votar_lista_completa", "su_seleccion",
        "votar_en_blanco", "confirmar_voto", "alto_contraste",
        "introduzca_boleta", "si_tiene_dudas", "su_voto_impreso", "no",
        "muchas_gracias", "puede_retirar_boleta", "si_desea_verificarlo",
        "imprimiendo_voto", "no_retirar_boleta", "agradecimiento",
        "este_es_su_voto", "volver_al_inicio", "aguarde_unos_minutos",
        "seleccionar_idioma", "aceptar", "cancelar", "confirmar_seleccion",
        "cargando_interfaz", "espere_por_favor", "verificando_voto")

    encabezado = get_config('datos_eleccion')
    if departamento is not None and municipio is not None:
        encabezado = copy(encabezado)
        encabezado["fecha"] += " - %s - %s" % (departamento, municipio)

    constants_dict = {
        "juego_de_datos": JUEGO_DE_DATOS,
        "ubicacion": ubicacion,
        "cod_lista_blanco": COD_LISTA_BLANCO,
        "elecciones_internas": get_tipo_elec("interna"),
        "elecciones_paso": get_tipo_elec("paso"),
        "agrupar_por_partido": AGRUPAR_POR_PARTIDO,
        "mostrar_cursor": MOSTRAR_CURSOR,
        "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
        "i18n": [(trans, _(trans)) for trans in translations],
        "palabra_lista": _("lista"),
        "sus_candidatos": _("sus_candidatos"),
        "candidato_no_seleccionado": _("candidato_no_seleccionado"),
        "usa_armve": USA_ARMVE,
        "ext_img_voto": EXT_IMG_VOTO,
        "effects": EFECTOS_VOTO,
        "flavor": FLAVOR,
        "templates": get_templates(),
        "numeros_templates": NUMEROS_TEMPLATES[FLAVOR],
        "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO,
        "ADHESION_SEGMENTADA": get_tipo_elec("adh_segmentada"),
        "USAR_BUFFER_IMPRESION": USAR_BUFFER_IMPRESION,
        "COLAPSAR_LISTAS_PASO": get_tipo_elec("colapsar_listas"),
        "COLAPSAR_INTERNAS_PASO": get_tipo_elec("colapsar_partidos"),
        "BARRA_SELECCION": BARRA_SELECCION,
        "asistida": False,
        "imagenes": []#get_nombres_imagenes()
    }
    return constants_dict


def get_templates():
    templates = {}
    template_names = ("candidato", "candidato_confirmacion", "categoria",
                      "lista", "partido")
    for template in template_names:
        file_name = "%s.html" % template
        template_file = os.path.join("flavors", FLAVOR, file_name)
        templates[template] = template_file
    return templates


def get_nombres_imagenes():
    nombres_imagenes = []
    for candidato in Candidato.principales():
        nombres_imagenes.append(_image_name(candidato.codigo))

    for lista in Lista.all():
        nombres_imagenes.append(_image_name(lista.codigo))
    for partido in Partido.all():
        nombres_imagenes.append(_image_name(partido.codigo))
    for alianza in Alianza.all():
        nombres_imagenes.append(_image_name(alianza.codigo))

    return nombres_imagenes
