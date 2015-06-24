# -*- coding: utf-8 -*-
from zaguan import WebContainerController
from zaguan.actions import BaseActionController

from msa.core import get_config
from msa.core.data import Ubicacion
from msa.voto.settings import MOSTRAR_CURSOR, PATH_TEMPLATES_VOTO


class Actions(BaseActionController):
    pass


class ControllerDemo(WebContainerController):

    """Controller para la interfaz web de la demo."""

    def __init__(self, parent):
        super(ControllerDemo, self).__init__()
        self.parent = parent
        self.add_processor("demo", Actions(self))

    def document_ready(self, data):
        self.parent._ready()

    def _get_data_mesas(self):
        # Uso un set para tomar las N distintas configuraciones
        configuraciones = set()
        # En mesas_demo guardo las mesas de ejemplo.
        mesas_demo = []

        # Tomo una mesa testigo por cada lugar diferente
        for obj in Ubicacion.many(clase="Mesa"):
            key = (obj.municipio, obj.extranjera)
            if key not in configuraciones:
                configuraciones.add(key)
                ext = obj.extranjera and "(Ext)" or ''
                mesas_demo.append((obj.numero, obj.departamento,
                                   obj.municipio, ext))
        return mesas_demo

    def cargar_botones(self):
        def _cmp(a, b):
            return cmp(a[1], b[1])
        datos_mesas = self._get_data_mesas()
        datos_mesas = sorted(datos_mesas, cmp=_cmp)
        #if len(datos_mesas) == 1:
        nro_mesa = datos_mesas[0][0]
        self.configurar_mesa(nro_mesa)
        #else:
        #    self.send_command("cargar_botones_ubicaciones", datos_mesas)

    def configurar_mesa(self, data):
        self.parent._configurar_ubicacion_demo(data)
        self.parent._iniciar_demo()

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants()
        self.send_command("set_constants", constants_dict)


def get_constants():
    translations = ("seleccion_ubicacion_demo", )
    encabezado = get_config('datos_eleccion')

    constants_dict = {
        "mostrar_cursor": MOSTRAR_CURSOR,
        "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
        "i18n": [(trans, _(trans)) for trans in translations],
        "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO
    }
    return constants_dict
