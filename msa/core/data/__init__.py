# -*- coding: utf-8 -*-
"""Fuente de datos para la BUE."""
from os.path import join

from cryptography.exceptions import InvalidTag
from ojota import Ojota, current_data_code, set_data_source
from ojota.base import OjotaHierarchy
from ojota.sources import JSONSource

from msa.core.crypto import desencriptar_credencial
from msa.core.data.candidaturas import Candidatura
from msa.core.data.constants import NOMBRE_JSON_UBICACIONES
from msa.core.data.settings import (PATH_CARPETA_DATOS,
                                    PATH_DATOS_JSON)


set_data_source(PATH_DATOS_JSON)


class Ubicacion(OjotaHierarchy):

    """Ubicacion de votacion."""

    plural_name = NOMBRE_JSON_UBICACIONES
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("descripcion", "cod_datos", "clase")

    def template_ubic(self):
        """Devuelve el template adecuando para la ubicacion actual."""
        ret = None
        mejor_match = None
        for temp in TemplateMap.all():
            if self.cod_datos.startswith(temp.codigo):
                if not mejor_match or \
                   len(temp.codigo) > len(mejor_match.codigo):
                    mejor_match = temp

        if mejor_match is not None:
            cod_template = mejor_match.cod_template
            template_impresion = TemplateImpresion.one(cod_template)
            if template_impresion is None:
                ret = self.fallback_template()
            else:
                ret = template_impresion
        else:
            ret = self.fallback_template()

        return ret

    def fallback_template(self):
        template_obj = TemplateImpresion.one("fallback")
        if template_obj is not None:
            template_obj = template_obj
        return template_obj


    def __str__(self):
        """Representacion en string de la Ubicacion actual."""
        return "<Ubicacion> {} {} ({})".format(self.clase, self.descripcion,
                                               self.codigo)

    @property
    def departamento(self):
        """Devuelve el objeto con los datos del Departamento."""
        return self._get_data_clase("Departamento")

    @property
    def municipio(self):
        """Devuelve el objeto con los datos del Municipio."""
        return self._get_data_clase("Localidad")

    @property
    def escuela(self):
        """Devuelve el objeto con los datos de la escuela."""
        return self._get_data_clase("Establecimiento")

    def _get_data_clase(self, clase):
        """Devuelve el objeto con los datos de la ubicacion de tal clase."""
        parent = self.parent
        while parent is not None and parent.clase != clase:
            parent = parent.parent
        if parent is not None:
            descripcion = parent.descripcion
        else:
            descripcion = ""
        return descripcion

    def es_mesa(self):
        return self.clase == "Mesa"

    @property
    def descripcion_completa(self):
        """Devuelve la ubicacion completa."""
        return "%s %s" % (self.clase, self.descripcion)

    def validar(self, form_data, credencial, validar_mesa):
        """Valida una mesa.

        Argumentos:
            form_data -- un diccionario con la mesa y el pin que estamos
            tratando de validar/
            credencial -- un objeto de tipo SoporteDigital de la credencial.
        """
        mesa_valida = False
        key = None
        # si no es una mesa no nos tomamos la molestia.
        if self.es_mesa() and credencial is not None:
            # obtenemos el pin
            pin = bytes(form_data.get("pin"), "utf8")
            # si es modo demo la credencial no tiene la mesa en la
            # validacion
            if validar_mesa:
                id_unico_mesa = bytes(self.id_unico_mesa, "utf8")
            else:
                id_unico_mesa = None

            try:
                # obtenemos la key que está dentro de la credencial.
                key = desencriptar_credencial(id_unico_mesa, pin, credencial)
                mesa_valida = True
            except InvalidTag:
                pass

        self.set_aes_key(key)

        return mesa_valida

    @property
    def listas_especiales(self):
        """Devuelve los codigos de candidatura de las listas especiales."""
        codigos = []
        especiales = Candidatura.many(clase="Especial",
                                      sorted="orden_absoluto")
        for especial in especiales:
            if especial.id_candidatura not in codigos:
                codigos.append(especial.id_candidatura)

        return codigos

    def usar_cod_datos(self):
        """Establece el cod_datos de una ubicación."""
        current_data_code(self.cod_datos)

    def set_aes_key(self, key):
        """Establece la clave con la que vamos a encriptar los votos.

        Argumentos:
            key -- la clave que vamos a almacenar.
        """
        self.__aes_key = key

    def get_aes_key(self):
        """Devuelve la clave con la que vamos a encriptar los votos."""
        return self.__aes_key


class RootJSONSource(JSONSource):

    """JSONSource que le pega a la carpeta raiz de datos."""

    def _get_file_path(self, cls):
        """Devuelve la ubicacion en el que se encuentra la informacion."""
        full_path = join(PATH_CARPETA_DATOS, cls.get_plural_name())
        return full_path


class Speech(Ojota):

    """Discurso para pronunciar por tts."""

    plural_name = 'Speech'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("texto", )
    data_source = RootJSONSource()


class TemplateImpresion(Ojota):

    """Template de impresion de categoria en voto."""

    plural_name = 'TemplatesImpresion'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("bloques", )

    def get_default(self):
        ret = {}
        if hasattr(self, "comun"):
            ret = self.comun
        return ret



class TemplateMap(Ojota):

    """Map de codigo de ubicacion a template de impresion."""

    plural_name = 'TemplatesMap'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("cod_template", )


class Configuracion(Ojota):

    """Clase para los objetos de Configuracion de la aplicacion."""

    plural_name = 'Configuraciones'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("descripcion", "valor")

    def __repr__(self):
        """Representacion del objeto Configuracion."""
        return self.codigo
