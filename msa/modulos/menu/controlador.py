"""Constrolador del modulo Menu."""

from gi.repository.GObject import source_remove, timeout_add_seconds

from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.constants import MODULO_TOTALIZADOR
from msa.modulos.menu.constants import TEXTOS


class Actions(BaseActionController):

    """Actions para el controlador del menu."""

    def click_boton(self, data):
        self.async(self.controlador.modulo._btn_presionado, data)

    def calibrar(self, data):
        self.async(self.controlador.modulo._calibrar_pantalla)

    def apagar(self, data):
        self.controlador.modulo._btn_apagar_clicked()


class Controlador(ControladorBase):

    """Controller para la interfaz web de voto."""

    def __init__(self, modulo):
        super(Controlador, self).__init__(modulo)
        self.set_actions(Actions(self))
        self.textos = TEXTOS
        self.timer = None

    def document_ready(self, data):
        self.modulo._inicio()

    def iniciar_timer(self):
        if self.modulo.config("usar_lockscreen") and not self.sesion.modo_demo:
            self.timer = timeout_add_seconds(
                self.modulo.config("tiempo_lockscreen"),
                self.lockear_menu)
        else:
            # diferenciar de pantalla bloqueada (ver rampa)
            self.timer = False

    def quitar_timer(self):
        if self.timer is not None:
            source_remove(self.timer)

    def reiniciar_timer(self):
        self.quitar_timer()
        self.iniciar_timer()

    def lockear_menu(self):
        self.quitar_timer()
        self.send_command("mostrar_lockscreen")
        self.timer = None
        return False

    def cargar_botones(self, mesa_abierta):
        self.reiniciar_timer()
        usar_asistida = self.modulo.config("usar_asistida")
        usar_sufragio = self.modulo.config("usar_sufragio")
        usar_totalizador = self.modulo.config("usar_totalizador")
        # aún estando habilitado el totalizador nos aseguramos de que esté
        # siendo usado en este disco de esta elección.
        if usar_totalizador:
            usar_totalizador = self.modulo.en_disco(MODULO_TOTALIZADOR)

        modo_demo = self.sesion.modo_demo
        usar_capacitacion = (self.modulo.config("usar_capacitacion") and
                             modo_demo)
        self.send_command("mostrar_pantalla",
                          {'USAR_ASISTIDA': usar_asistida,
                           'USAR_VOTO': usar_sufragio,
                           'USAR_TOTALIZADOR': usar_totalizador,
                           'USAR_CAPACITACION': usar_capacitacion})

    def mostrar_botonera(self):
        self.cargar_botones(self.modulo.mesa_abierta)

    def show_maintenance_button(self):
        usar_mantenimiento = self.modulo.config("usar_mantenimiento")
        if usar_mantenimiento:
            self.send_command("mostrar_boton_mantenimiento")

    def get_constants(self):
        con_datos_personales = self.modulo.config("con_datos_personales")
        local_constants = {
            "CON_DATOS_PERSONALES": con_datos_personales,
        }
        constants_dict = self.base_constants_dict()
        constants_dict.update(local_constants)
        return constants_dict
