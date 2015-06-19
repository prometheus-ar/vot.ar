# -*- coding: utf-8 -*-
from ojota import Ojota, set_data_source
from ojota.base import OjotaHierarchy

from msa.core.constants import COD_IMPRESION_BAJA
from msa.core.exceptions import TemplateNoEncontrado
from msa.core.data.settings import PATH_DATOS_JSON, NOMBRE_JSON_MESAS
from msa.core.settings import IMPRESION_HD_BOLETAS


set_data_source(PATH_DATOS_JSON)


class Ubicacion(OjotaHierarchy):

    """Ubicacion de votacion."""

    plural_name = NOMBRE_JSON_MESAS
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("descripcion", "cod_datos", "clase")

    def templates_impresion(self, forzar_media=False):
        mejor_match = None
        for t in TemplateMap.all():
            if self.cod_datos.startswith(t.codigo):
                if not mejor_match or \
                   len(t.codigo) > len(mejor_match.codigo):
                    mejor_match = t
        # TODO: solucionar este lio de raiseo de excepciones y de return fuera
        # de lugar
        if mejor_match:
            cod_template = mejor_match.cod_template
            if not forzar_media and not IMPRESION_HD_BOLETAS:
                cod_template += COD_IMPRESION_BAJA
            template_impresion = TemplateImpresion.one(cod_template)
            if template_impresion is None:
                raise TemplateNoEncontrado()
            return template_impresion.templates
        else:
            raise TemplateNoEncontrado()

    def __str__(self):
        return self.descripcion

    @property
    def departamento(self):
        return self._get_data_clase("Departamento")

    @property
    def municipio(self):
        return self._get_data_clase("Localidad")

    @property
    def escuela(self):
        return self._get_data_clase("Establecimiento")

    def _get_data_clase(self, clase):
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
        return "%s %s" % (self.clase, self.descripcion)


class Speech(Ojota):

    """Discurso para pronunciar por tts."""
    plural_name = 'Speech'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("texto", )


class TemplateImpresion(Ojota):

    """Template de impresion de categoria en voto."""
    plural_name = 'TemplatesImpresion'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("templates", )

class TemplateMap(Ojota):

    """Map de codigo de ubicacion a template de impresion."""
    plural_name = 'TemplatesMap'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("cod_template", )


class Configuracion(Ojota):
    plural_name = 'Configuraciones'
    pk_field = "codigo"
    default_order = "codigo"
    required_fields = ("descripcion", "valor")

    def __repr__(self):
        return self.codigo
