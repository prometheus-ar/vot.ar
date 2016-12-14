"""Controlador del modulo capacitacion."""

from msa.core.data import Ubicacion
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.capacitacion.constants import MOSTRAR_DEPARTAMENTOS, TEXTOS
from msa.modulos.constants import (E_EN_CONFIGURACION, E_SETUP,
                                   MODULO_ASISTIDA, MODULO_CAPACITACION)


class Controlador(ControladorBase):

    """Controller para la interfaz web de la capacitacion."""

    def __init__(self, modulo):
        """Constructor de controlador de Capacitacion."""
        super(Controlador, self).__init__(modulo)
        self.set_actions(BaseActionController(self))
        self.estado = E_SETUP
        self.mesa = None
        self.textos = TEXTOS
        self.nombre = MODULO_CAPACITACION

    def document_ready(self, data):
        """Callback que se llama cuando el browser tira el document.ready()."""
        self.modulo._ready()

    def _get_data_mesas(self):
        """Devuelve la data de los botones de cada ubicacion diferente."""
        # Uso un set para tomar las N distintas configuraciones
        configuraciones = set()
        # En mesas_capacitacion guardo las mesas de ejemplo.
        mesas_capacitacion = []

        # Tomo una mesa testigo por cada lugar diferente
        for obj in Ubicacion.many(clase="Mesa"):
            if obj.cod_datos not in configuraciones:
                configuraciones.add(obj.cod_datos)
                mesas_capacitacion.append((obj.numero, obj.departamento,
                                           obj.municipio, obj.extranjera))

        return mesas_capacitacion

    def cargar_botones(self):
        """Carga loss botones a mostrar en el menu."""
        datos_mesas = self._get_data_mesas()
        self.send_command("cargar_botones_ubicaciones", datos_mesas)

    def configurar_mesa(self, data):
        """Configura la mesa seleccionada."""
        modulo, ubicacion = data
        self.modulo._configurar_ubicacion_capacitacion(ubicacion)

        if modulo == MODULO_ASISTIDA:
            self.modulo._iniciar_capacitacion_asistida()
        else:
            self.modulo._iniciar_capacitacion()

    def activar_impresion(self, nro_mesa):
        mesa = Ubicacion.one(numero=nro_mesa)
        self.mesa = mesa
        mesa.usar_cod_datos()
        self.estado = E_EN_CONFIGURACION

    def fin_boleta_demo(self):
        self.estado = E_SETUP

    def fin_boleta_demo_error(self):
        self.estado = E_SETUP
        self.modulo.rampa.expulsar_boleta()

    def consulta(self, *args, **kwargs):
        pass

    def cancelar_impresion(self, data):
        self.fin_boleta_demo()

    def get_constants(self):
        """Trae las constantes para el modulo."""
        constants = self.base_constants_dict()
        constants["preimpresion_boleta"] = \
            self.modulo.config("preimpresion_boleta")
        constants["mostrar_departamentos"] = MOSTRAR_DEPARTAMENTOS
        constants["items_columna"] = \
            self.modulo.config("items_columna")

        return constants

