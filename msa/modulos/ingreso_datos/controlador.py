"""Controlador para el modulo de ingreso de datos."""
from urllib.parse import quote

from msa.core.data import Ubicacion
from msa.core.data.constants import TIPO_DOC
from msa.core.documentos.autoridades import Autoridad
from msa.core.documentos.settings import CANTIDAD_SUPLENTES
from msa.core.imaging.constants import (CONFIG_BOLETA_APERTURA,
                                        CONFIG_BOLETA_CIERRE,
                                        CONFIG_BOLETA_TRANSMISION)
from msa.core.imaging.reverso import ImagenReversoBoleta
from msa.core.settings import USAR_BUFFER_IMPRESION
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.constants import (E_INGRESO_ACTA, E_INGRESO_DATOS, E_MESAYPIN,
                                   MODULO_APERTURA, MODULO_INICIO,
                                   MODULO_RECUENTO, MODULO_TOTALIZADOR)
from msa.modulos.ingreso_datos.constants import ERRORES, TEXTOS
from msa.settings import DEBUG, MODO_DEMO


class Actions(BaseActionController):
    """Actions del controlador de interaccion/"""
    def msg_confirmar_ingreso(self, data):
        """muestra el mensaje para confirmar el ingreso."""
        self.controlador.msg_confirmar_ingreso()

    def recibir_mesaypin(self, data):
        """Recive la mesa y el pin."""
        self.controlador.recibir_mesaypin(data)

    def recibir_autoridades(self, data):
        """Recibe la data de las autoridades."""
        self.controlador.recibir_datospersonales(data)


class Controlador(ControladorBase):

    """Controller para las pantallas de ingreso de datos."""

    def __init__(self, modulo, estado=None, modulo_padre=MODULO_RECUENTO):
        """Constructor del controlador de interaccion."""
        super(Controlador, self).__init__(modulo)
        self.modulo_padre = modulo_padre
        self.estado = estado if estado is not None else E_INGRESO_ACTA
        self._intento = 0
        self.set_actions(Actions(self))
        self.MSG_DEFAULT = _("introduzca_acta_cierre")
        self.MSG_TOTALIZADOR = _("introduzca_acta_totalizacion")
        self.MSG_APERTURA = _("introduzca_acta_apertura")
        self.MSG_RETIRE_E_INGRESE = _("retire_acta_apertura")
        self.MSG_ESPERE = _("aguarde_procesando_acta")
        self.mensaje = self.MSG_DEFAULT
        self.textos = TEXTOS

    def document_ready(self, data):
        """Callback que llama el browser en el document.ready()"""
        self._inicializa_pantalla()

    def set_imagen_acta(self):
        """Selecciona config de svg para el modulo."""
        imagenes = {
            MODULO_APERTURA: CONFIG_BOLETA_APERTURA,
            MODULO_INICIO: CONFIG_BOLETA_APERTURA,
            MODULO_RECUENTO: CONFIG_BOLETA_CIERRE,
            MODULO_TOTALIZADOR: CONFIG_BOLETA_TRANSMISION
        }

        self.imagen_acta = ImagenReversoBoleta(
            imagenes[self.modulo_padre]).render_svg()

    def _inicializa_pantalla(self):
        """
        Prepara la primera pantalla de la interacción ocultando todos
        los elementos innecesarios del template y mostrando la imagen de la
        boleta.
        """
        self.send_constants()
        self.set_imagen_acta()

        if self.modulo_padre == MODULO_APERTURA:
            self.mensaje = self.MSG_APERTURA
        elif self.modulo_padre == MODULO_TOTALIZADOR:
            self.mensaje = self.MSG_TOTALIZADOR
        else:
            self.mensaje = self.MSG_DEFAULT

        self.set_pantalla()
        self.send_command("show_body")

        # Si ya hay una boleta en la impresora la expulsamos
        if self.estado == E_INGRESO_ACTA:
            self.modulo.rampa.expulsar_boleta()

    def set_cargando_recuento(self):
        """Muestra la pantalla de cargando el recuento."""
        mensaje = _("cargando_recuento")
        self.send_command("pantalla_ingresoacta",
                          {"mensaje": mensaje,
                           "imagen_acta": quote(self.imagen_acta)})

    def set_pantalla(self, data=None):
        """Setea la pantalla de acuerdo al estado actual."""
        if data is None:
            data = {}

        if self.estado == E_INGRESO_ACTA:
            self.send_command("pantalla_ingresoacta",
                              {"mensaje": self.mensaje,
                               "imagen_acta": quote(self.imagen_acta)})

        elif self.estado == E_MESAYPIN:
            self.send_command("pantalla_mesaypin",
                              [DEBUG,
                               "aceptar_mesa_y_pin",
                               data.get("mesa", getattr(self.sesion.mesa,
                                                        "numero", "")),
                               self.modulo_padre == MODULO_INICIO
                               ])
        elif self.estado == E_INGRESO_DATOS:
            self.cargar_datos_personales(data)
        self.send_constants()

    def cargar_datos_personales(self, data):
        """Carga los datos personales."""
        data["teclado_fisico"] = DEBUG
        data["callback_aceptar"] = "aceptar_datos_personales"

        if self.modulo_padre == MODULO_APERTURA:
            data['pattern_validacion_hora'] = "[0]?[8-9]|1[0-9]?|2[0-3]?"
        else:
            data['pattern_validacion_hora'] = "1[8-9]?|2[0-3]?"
            data["imagen_acta"] = quote(self.imagen_acta)

        if (hasattr(self.modulo, "apertura") and
                self.modulo.apertura is not None and
                self.sesion.mesa.numero == self.modulo.apertura.mesa.numero):
            autoridades = [(autoridad.a_dict()) for autoridad in
                           self.modulo.apertura.autoridades]
            if self.modulo_padre == MODULO_APERTURA:
                data['foco_hora'] = False
                data['hora'] = self.modulo.apertura.hora
            else:
                data['foco_hora'] = True
            data["autoridades"] = autoridades
        else:
            data['foco_hora'] = False

            self.modulo.apertura = None
        self.set_pantalla_datospersonales(data)

    def set_pantalla_datospersonales(self, data=None):
        """Muestra la pantalla de datos personales."""
        if 'autoridades' in data and data['autoridades'] is not None:
            for autoridad in data['autoridades']:
                nombre = autoridad['nombre'].replace("'", "&#39;")
                autoridad['nombre'] = nombre
                apellido = autoridad['apellido'].replace("'", "&#39;")
                autoridad['apellido'] = apellido

        if self.modulo_padre == MODULO_APERTURA:
            data['modulo'] = "apertura"
        else:
            data['modulo'] = "escrutinio"
        self.send_command("pantalla_datospersonales", data)

    def set_mensaje(self, mensaje):
        """Cambia el mensaje de la pantalla de ingreso de acta."""
        self.mensaje = mensaje
        self.send_command("set_mensaje", mensaje)

    def set_pantalla_confirmacion(self, imagen):
        """Carga la pantalla de confirmacion de apertura."""
        self.send_command("pantalla_confirmacion_apertura",
                          [_("acta_apertura_mesa"), imagen])

    def mensaje_inicial(self):
        """Establece el mensaje inicial."""
        if self.modulo_padre == MODULO_APERTURA:
            self.set_mensaje(self.MSG_APERTURA)
        elif self.modulo_padre == MODULO_TOTALIZADOR:
            self.set_mensaje(self.MSG_TOTALIZADOR)
        else:
            self.set_mensaje(self.MSG_DEFAULT)

    def _procesar_callback(self):
        """Procesa el callback."""
        self.sesion.impresora.remover_consultar_tarjeta()
        self.callback()

    def hide_dialogo(self):
        """Esconde el dialogo."""
        self.send_command("ocultar_mensaje")
        self.send_command("hide_dialogo")
        self.send_command("restaurar_foco_invalido")

    def confirmar_envio(self):
        """
        Del frontend se acepta el popup de ingreso de datos, así que se le pide
        que envíe los datos
        """
        if self.estado == E_MESAYPIN:
            self.send_command("enviar_mesaypin")
        elif self.estado == E_INGRESO_DATOS:
            self.send_command("enviar_datospersonales")

    def msg_confirmar_ingreso(self):
        """
        Muestra un popup para confirmar el ingreso del nro de mesa y pin o de
        los datos de las autoridades de mesa
        """
        self._callback_aceptar = self.confirmar_envio
        self._callback_cancelar = self.hide_dialogo
        self.send_command("show_dialogo_confirmacion")

    def msg_confirmar_apertura(self, respuesta):
        """Muestra el mensaje de confirmar la apertura."""
        if respuesta:
            self.modulo.confirmar_apertura()
        else:
            self.modulo.cargar_datos(self.modulo.apertura)

    def msg_mesaypin_incorrecto(self):
        """Muestra el mensaje de mesa y pin incorrecto."""
        self.cargar_dialogo(callback_template="msg_mesa_y_pin_incorrectos",
                            aceptar=self.hide_dialogo)

    def recibir_mesaypin(self, form_data, validar_mesa=not MODO_DEMO):
        """ Recibe la mesa y pin ingresada y la valida para
        pasar a la siguiente pantalla, o rechaza el ingreso y vuelve
        a pedir el ingreso de datos
        Respuesta es un json:
            {"mesa": 1,
            "pin": A1C2E3G4}
        """

        mesa = Ubicacion.one(numero=form_data['mesa'])

        if mesa is not None and mesa.validar(form_data, self.sesion.credencial,
                                             validar_mesa):
            self.modulo._abrir_mesa(mesa)
        else:
            self.msg_mesaypin_incorrecto()
            self._intento += 1
            if self._intento >= 3:
                self.modulo.rampa.expulsar_boleta()
                self.modulo.salir_a_modulo(MODULO_INICIO)

    def recibir_datospersonales(self, data):
        """
        Recibe los datos de las autoridades de mesa del frontend y genera
        una lista de instancias Autoridad para pasar al ModuloRecuento
        """
        autoridades = []
        for autoridad in data['autoridades']:
            # funciona para Autoridad = Apellido, Nombre, TipoDoc,
            # NroDoc
            if len(autoridad) == 4:
                largos = [len(x) for x in autoridad]
                del largos[2]
                if any(largos):
                    autoridad_mesa = Autoridad(*autoridad)
                    autoridades.append(autoridad_mesa)

        if self.modulo_padre == MODULO_APERTURA:
            self.modulo.crear_apertura(autoridades, data['hora'])
        else:
            self.modulo.generar_recuento(autoridades, data['hora'])

    def get_constants(self):
        """Genera las constantes propias de cada modulo."""
        local_constants = {
            "tipo_doc": [(TIPO_DOC.index(tipo), tipo) for tipo in TIPO_DOC],
            "mensajes_error": dict([(trans, _(trans)) for trans in ERRORES]),
            "cantidad_suplentes": CANTIDAD_SUPLENTES,
            "usa_tildes": self.modulo.config("teclado_usa_tildes"),
            "USAR_BUFFER_IMPRESION": USAR_BUFFER_IMPRESION,
            "realizar_apertura": self.modulo.config("realizar_apertura"),
            "usa_login_desde_inicio": self.modulo.config("login_desde_inicio"),
        }
        constants_dict = self.base_constants_dict()
        constants_dict.update(local_constants)
        return constants_dict
