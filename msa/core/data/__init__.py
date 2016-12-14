# -*- coding: utf-8 -*-
"""Fuente de datos para la BUE."""
from hashlib import sha256
from os.path import join

from cryptography.exceptions import InvalidTag
from ojota import Ojota, current_data_code, set_data_source
from ojota.base import OjotaHierarchy
from ojota.sources import JSONSource

from msa.core.crypto import derivar_clave, desencriptar
from msa.core.data.candidaturas import Candidatura
from msa.core.data.settings import (NOMBRE_JSON_MESAS, PATH_CARPETA_DATOS,
                                    PATH_DATOS_JSON)


set_data_source(PATH_DATOS_JSON)


class Ubicacion(OjotaHierarchy):

    """Ubicacion de votacion."""

    plural_name = NOMBRE_JSON_MESAS
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("descripcion", "cod_datos", "clase")

    def __init__(self, *args, **kwargs):
        OjotaHierarchy.__init__(self, *args, **kwargs)
        self.__aes_key = None

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

    @property
    def descripcion_completa(self):
        """Devuelve la ubicacion completa."""
        return "%s %s" % (self.clase, self.descripcion)

    def validar(self, salt, pin, key_credencial):
        mesa_valida = False
        if len(key_credencial):
            try:
                self.decode_aes_key(salt, pin, key_credencial)
                cred = salt + key_credencial[16:]
                hash_credencial = sha256(cred).hexdigest()
                if hash_credencial == self.credencial:
                    mesa_valida = True
            except InvalidTag:
                pass
        return mesa_valida

    @property
    def listas_especiales(self):
        codigos = []
        especiales = Candidatura.many(clase="Especial",
                                      sorted="orden_absoluto")
        for especial in especiales:
            if especial.id_candidatura not in codigos:
                codigos.append(especial.id_candidatura)

        return codigos

    def usar_cod_datos(self):
        current_data_code(self.cod_datos)

    def set_aes_key(self, key):
        self.__aes_key = key

    def get_aes_key(self):
        return self.__aes_key

    def decode_aes_key(self, salt, pin, key_credencial):
        clave = derivar_clave(bytes(pin, "utf8"), salt)
        key_mesa = desencriptar(clave, key_credencial)
        self.set_aes_key(key_mesa)



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
