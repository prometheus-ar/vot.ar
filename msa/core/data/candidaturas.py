""" Modulo con las clases para manejo de datos de las candidaturas."""
# -*- coding: utf-8 -*-
from random import shuffle

from ojota import Ojota, Relation, OjotaSet
from ojota.sources import JSONSource

from msa.constants import COD_LISTA_BLANCO
from msa.core import get_tipo_elec
from msa.core.data.constants import NOMBRE_JSON_CATEGORIAS, \
    NOMBRE_JSON_CANDIDATOS, NOMBRE_JSON_LISTAS, NOMBRE_JSON_PARTIDOS, \
    NOMBRE_JSON_BOLETAS, NOMBRE_JSON_ALIANZAS


class EleccionSet(OjotaSet):

    """Un OjotaSet adaptado a las necesidades de Voto."""

    def to_dict(self):
        """Devuelve una lista de diccionarios con los datos del OjotaSet."""
        return [elem.to_dict() for elem in self.all()]

    def all(self):
        """Devuelve todos los elementos del Set."""
        return self.many()

    def full_dict(self, img_func=None):
        """
        Devuelve una lista de diccionarios con los datos de los full dicts de
        los objetos.
        """
        return [elem.full_dict(img_func) for elem in self.all()]

    def shuffle(self):
        shuffle(self._list)


class Candidatura(Ojota):

    """Clase base de todos los Objetos de candidaturas."""

    data_in_root = False
    default_order = "codigo"
    pk_field = "codigo"
    queryset_type = EleccionSet
    data_source = JSONSource(create_empty=False)

    def es_blanco(self):
        """
        Determina si es voto en blanco o no (necesario para comportarse
        como un objeto candidato, en botonera).
        """
        return False

    @property
    def texto_asistida(self):
        """
        Property que devuelve el texto asistida si esta especificado y sino el
        nombre.
        """
        if hasattr(self, "nombre"):
            ret = self.nombre
            if self.asistida is not None:
                ret = self.asistida
        else:
            ret = None
        return ret

    def to_dict(self):
        """Devuelve una representacion en diccionario del objeto."""
        dict_ = Ojota.to_dict(self)
        if hasattr(self, "asistida"):
            dict_['texto_asistida'] = self.texto_asistida
            del dict_['asistida']
        return dict_

    def __str__(self):
        """Representacion del objeto. Codigo y nombre de la Candidatura."""
        return "%s - %s" % (self.codigo, self.nombre)


class Categoria(Candidatura):

    """Categoria de candidatos a elegir."""

    plural_name = NOMBRE_JSON_CATEGORIAS
    required_fields = ("nombre", "posicion", "consulta_popular", "adhiere")

    @property
    def texto_asistida_ingrese_nro(self):
        """
        Devuelve el texto para a descripcion de la proxima categoria en
        asistida.
        """
        msg = u'A continuación usted elegirá su candidato para %s'
        return msg % self.texto_asistida

    def candidatos(self, cod_partido=None, clase_agrupacion=None):
        """
        Devuelve los candidatos principales de la Categoria.

        Argumentos:
            cod_partido: codigo del partido por el que filtrar.
            clase_agrupacion: clase por la que se va a agrupar. Generalmente
            Partido o Alianza.
        """
        if clase_agrupacion is None:
            clase_agrupacion = Partido

        if cod_partido is not None:
            partido = clase_agrupacion.one(cod_partido)
            candidatos = partido.candidatos_principales(self.codigo)
        else:
            candidatos = Candidato.principales(self.codigo)
        return candidatos

    def next(self, consulta_popular=None):
        """Devuelve la siguiente Categoria."""

        filter = {"posicion__gt": self.posicion,
                  "sorted": "posicion"}
        if consulta_popular is not None:
            filter['consulta_popular'] = consulta_popular
        return Categoria.one(**filter)

    def get_madre(self):
        """Devuelve la Categoria madre de esta Categoria si es que la hay."""
        return Categoria.one(codigo=self.adhiere)

    def get_hijas(self):
        """Devuelve las Categorias hijas de esta Categoria si es que la hay."""
        return Categoria.many(adhiere=self.codigo, sorted="posicion")

    def to_dict(self):
        """Devuelve una representacion en diccionario del objeto."""
        dict_ = Candidatura.to_dict(self)
        # Internacionalizando el nombre de la categoria
        dict_['nombre'] = _(self.nombre)
        return dict_


class Alianza(Candidatura):

    """Alianza que participa de la eleccion."""

    plural_name = NOMBRE_JSON_ALIANZAS

    def full_dict(self, img_func, listas=True):
        """
        Devuelve una representacion completa de la Alianza y las relaciones
        relevantes para armar los botones de la eleccion.

        Argumentos:
            img_func: funcion que ayuda a resolver la ubicacion de la imagen y,
            en caso de ser necesario, rellenar con la imagen por defecto.
        """
        alianza = self.to_dict()
        alianza['imagen'] = img_func(alianza['codigo'])
        alianza['listas'] = []
        if listas:
            for lista in self.listas:
                lista_dict = lista.to_dict()
                lista_dict['candidatos'] = [cand.full_dict(img_func)
                                            for cand in lista.candidatos]
                alianza['listas'].append(lista_dict)
        return alianza

    def candidatos_principales(self, cod_categoria):
        """
        Devuelve los candidatos principales de todas las listas de esta
        Alianza para una categoria dada.

        Argumentos:
            cod_categoria: el codigo de la categoria de la que seran
            los candidatos.
        """
        ids_listas = [lista.codigo for lista in self.listas]
        candidatos = Candidato.many(titular=True, numero_de_orden=1,
                                    cod_lista__in=ids_listas,
                                    cod_categoria=cod_categoria)
        return candidatos

    @property
    def listas(self):
        """Property con todas las listas de los partidos de esta la Alianza."""
        listas = []
        for partido in self.partidos:
            listas.extend(partido.listas)

        return listas

    def es_blanco(self):
        """Determina si se trata o no de voto en blanco."""
        return self.codigo.endswith(COD_LISTA_BLANCO)


class Partido(Candidatura):

    """Partido de una eleccion."""

    plural_name = NOMBRE_JSON_PARTIDOS
    alianza = Relation('cod_alianza', Alianza, "partidos")

    def full_dict(self, img_func, listas=True):
        """
        Devuelve una representacion completa del partido y las relaciones
        relevantes para armar los botones de la eleccion.

        Argumentos:
            img_func: funcion que ayuda a resolver la ubicacion de la imagen y,
            en caso de ser necesario, rellenar con la imagen por defecto.
        """
        partido = self.to_dict()
        partido['imagen'] = img_func(partido['codigo'])
        if listas:
            partido['listas'] = []
            for lista in self.listas:
                lista_dict = lista.to_dict()
                lista_dict['candidatos'] = [cand.full_dict(img_func) for cand in
                                            lista.candidatos]
                partido['listas'].append(lista_dict)
        return partido

    def candidatos_principales(self, cod_categoria):
        """
        Devuelve los candidatos principales de todas las listas de este
        Partido para una categoria dada.

        Argumentos:
            cod_categoria: el codigo de la categoria de la que seran
            los candidatos.
        """
        ids_listas = [lista.codigo for lista in self.listas]
        candidatos = Candidato.principales().many(
                                    cod_lista__in=ids_listas,
                                    cod_categoria=cod_categoria)
        return candidatos

    def es_blanco(self):
        """Determina si se trata o no de voto en blanco."""
        return self.codigo.endswith(COD_LISTA_BLANCO)


class Lista(Candidatura):

    """Lista que agrupa candidatos."""

    plural_name = NOMBRE_JSON_LISTAS
    required_fields = ("numero", "nombre", "nombre_corto",
                       "cod_partido")
    partido = Relation('cod_partido', Partido, 'listas')

    def __init__(self, *args, **kwargs):
        super(Lista, self).__init__(*args, **kwargs)
        self.numero = self.numero or ''

    def es_blanco(self):
        """Determina si se trata o no de voto en blanco."""
        return self.codigo.endswith(COD_LISTA_BLANCO)

    @property
    def alianza(self):
        """Property que devuelve la Alianza a la que perteneces esta Lista."""
        if self.partido is not None:
            return self.partido.alianza

    @property
    def candidatos(self):
        """
        Property que devuelve todos los candidatos principales de esta lista,
        Incluye los candidatos adheridos a la lista.
        """
        categorias = Categoria.many(sorted="posicion")

        candidatos = []
        if self.codigo.endswith(COD_LISTA_BLANCO):
            for categoria in categorias:
                candidato = Candidato.one(cod_lista=self.codigo,
                                        cod_categoria=categoria.codigo,
                                        titular=True, numero_de_orden=1)
                if candidato is not None:
                    candidatos.append(candidato)
        else:
            boleta = Boleta.one(self.codigo)
            for categoria in categorias:
                candidato = boleta.get_candidato(categoria.codigo)
                if candidato is not None:
                    candidatos.append(candidato)

        return candidatos


class Candidato(Candidatura):

    """Candidato que puede ser votado."""

    plural_name = NOMBRE_JSON_CANDIDATOS
    required_fields = ("nombre", "cod_lista", "numero_de_orden", "titular",
                       "cod_categoria", "sexo")

    categoria = Relation('cod_categoria', Categoria)
    lista = Relation('cod_lista', Lista, 'candidatos_full')

    def es_blanco(self):
        """Determina si se trata o no de voto en blanco."""
        return self.cod_lista.endswith(COD_LISTA_BLANCO)

    @property
    def partido(self):
        """Property que devuelve el Partido al que pertenece el candidato."""
        return self.lista.partido

    @property
    def alianza(self):
        """Property que devuelve la Alianza a la que pertenece el candidato."""
        if self.partido is not None:
            return self.partido.alianza

    def codigo_clean(self):
        """Devuelve la parte del codigo que es guardada en el chip de voto."""
        if self.es_blanco():
            codigo = COD_LISTA_BLANCO
        else:
            from msa.core.clases import Jerarquia
            codigo = Jerarquia(self.codigo).last_segment

        return codigo

    def to_dict(self):
        """Devuelve una representacion en diccionario del objeto."""
        dict_ = Candidatura.to_dict(self)
        # pequeño parche anti nombres con apostrofes (gracias Felipe D'Hont)
        dict_['nombre'] = self.nombre.replace("'", "`")
        dict_['texto_asistida'] = dict_['texto_asistida'].replace("'", "`")
        return dict_

    def full_dict(self, img_func=None, secundarios=True, suplentes=True,
                  hijas=True):
        """
        Devuelve una representacion completa del Candidato y las relaciones
        relevantes para armar los botones de la eleccion.

        Argumentos:
            img_func: funcion que ayuda a resolver la ubicacion de la imagen y,
            en caso de ser necesario, rellenar con la imagen por defecto.
        """
        candidato_dict = self.to_dict()
        candidato_dict['partido'] = self.partido.to_dict() \
            if self.partido is not None else {}
        candidato_dict['alianza'] = self.alianza.to_dict() \
            if self.alianza is not None else {}
        candidato_dict['lista'] = self.lista.to_dict()
        candidato_dict['lista']['imagen'] = img_func(self.lista.codigo)
        if img_func is not None:
            candidato_dict['imagen'] = img_func(self.codigo)

        if secundarios:
            candidato_dict['secundarios'] = self.secundarios.to_dict()
        if suplentes:
            candidato_dict['suplentes'] = self.suplentes.to_dict()
        if hijas:
            categorias_hijas = self.categoria.get_hijas()
            candidato_dict['categorias_hijas'] = []
            if len(categorias_hijas) > 0:
                for cat_hija in categorias_hijas:
                    principal = Candidato.one(cod_categoria=cat_hija.codigo,
                                              cod_lista=self.cod_lista,
                                              titular=True, numero_de_orden=1)
                    cand_hijo = principal.full_dict(img_func)
                    candidato_dict['categorias_hijas'].append(
                        [cat_hija.to_dict(), cand_hijo])

        return candidato_dict

    @classmethod
    def principales(self, cod_categoria=None):
        """
        Devuelve todos lo candidatos principales para una Categoria.

        Argumentos:
            cod_categoria: el codigo de la Categoria de la cual son los
            candidatos deseados.
        """
        filter = {"titular": True,
                  "numero_de_orden": 1}
        if cod_categoria is not None:
            filter['cod_categoria'] = cod_categoria
        candidatos = Candidato.many(**filter)
        return candidatos

    @property
    def secundarios(self):
        """Devuelve todos lo candidatos secundarios para este candidato."""
        candidatos = Candidato.many(cod_lista=self.cod_lista, titular=True,
                                    numero_de_orden__gt=1,
                                    cod_categoria=self.cod_categoria,
                                    sorted="numero_de_orden")
        return candidatos

    @property
    def suplentes(self):
        """Devuelve todos lo candidatos suplentes para este candidato."""
        candidatos = Candidato.many(cod_lista=self.cod_lista, titular=False,
                                    cod_categoria=self.cod_categoria,
                                    sorted="numero_de_orden")
        return candidatos

    @property
    def listas(self):
        listas = [boleta.lista for boleta in Boleta.many(GOB=self.codigo,
                                                         lista_completa=True)
                  if boleta.lista is not None]
        return listas

    @property
    def partidos(self):

        partidos = []
        codigos = []
        for lista in self.listas:
            if lista.partido not in codigos:
                codigos.append(lista.partido)
                partidos.append(lista.partido)

        return partidos

    @property
    def numero_colapsado(self):
        return 15 if hasattr(self, "agrupacion_partidos") and \
            self.agrupacion_partidos else get_tipo_elec("colapsar_partidos")


class Boleta(Candidatura):

    """Partido de una eleccion."""

    plural_name = NOMBRE_JSON_BOLETAS

    def __str__(self):
        """Representacion del objeto. Codigo y nombre de la Candidatura."""
        return "%s" % self.codigo

    def get_candidato(self, cod_categoria):
        if hasattr(self, cod_categoria):
            candidato = Candidato.one(getattr(self, cod_categoria))
        else:
            candidato = None

        return candidato
    @property
    def lista(self):
        lista = Lista.one(self.codigo)
        return lista
