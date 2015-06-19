# coding: utf-8
import hashlib
import os
from urllib2 import quote

from zaguan import WebContainerController
from zaguan.actions import BaseActionController
from zaguan.functions import asynchronous_gtk_message

from msa.core import get_config
from msa.core.clases import Autoridad
from msa.core.data import Ubicacion
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.core.imaging import ImagenReversoBoleta
from msa.core.settings import USA_ARMVE, USAR_BUFFER_IMPRESION
from msa.settings import DEBUG
from msa.voto.constants import (CANTIDAD_SUPLENTES, E_INGRESO_ACTA,
    E_INGRESO_DATOS, E_MESAYPIN, CONFIG_BOLETA_CIERRE,
    CONFIG_BOLETA_APERTURA, MODULO_APERTURA, MODULO_RECUENTO, MODULO_TOTALIZADOR,
    CONFIG_BOLETA_TRANSMISION, TIPO_DOC)
from msa.voto.sesion import get_sesion
from msa.voto.settings import (EFECTOS_VOTO, EXT_IMG_VOTO, FLAVOR,
    MOSTRAR_CURSOR, PATH_TEMPLATES_VOTO, USA_TILDES)


class Actions(BaseActionController):
    def document_ready(self, data):
        self.controller._inicializa_pantalla()

    def administrador(self, data):
        self.controller.parent.administrador()

    def msg_confirmar_ingreso(self, data):
        self.controller.msg_confirmar_ingreso()

    def msg_confirmar_apertura(self, data):
        asynchronous_gtk_message(self.controller.msg_confirmar_apertura)(data)

    def recibir_mesaypin(self, data):
        self.controller.recibir_mesaypin(data)

    def recibir_autoridades(self, data):
        self.controller.recibir_datospersonales(data)

    def dialogo(self, data):
        self.controller.procesar_dialogo(data)

    def volver(self, data):
        self.controller.parent.volver()

    def salir(self, data):
        self.controller.parent.salir()

    def log(self, data):
        self.controller.sesion.logger.debug("LOG >>>%s" % data)


class ControllerInteraccion(WebContainerController):
    """ Controller para las pantallas de ingreso de datos
    """
    def __init__(self, parent, estado=None, modulo=MODULO_RECUENTO):
        super(ControllerInteraccion, self).__init__()
        self.sesion = get_sesion()
        self.parent = parent
        self.modulo = modulo
        self.estado = estado if estado is not None else E_INGRESO_ACTA
        self._intento = 0
        self.add_processor(self.parent.web_template, Actions(self))
        self.MSG_DEFAULT = _("introduzca_acta_cierre")
        self.MSG_TOTALIZADOR = _("introduzca_acta_totalizacion")
        self.MSG_APERTURA = _("introduzca_acta_apertura")
        self.MSG_RETIRE_E_INGRESE = _("retire_acta_apertura")
        self.MSG_ESPERE = _("aguarde_procesando_acta")
        self.mensaje = self.MSG_DEFAULT
        self.set_imagen_acta()

    def set_imagen_acta(self):
        """
        selecciona config de svg para el modulo
        """

        imagenes = {
            MODULO_APERTURA: CONFIG_BOLETA_APERTURA,
            MODULO_RECUENTO: CONFIG_BOLETA_CIERRE,
            MODULO_TOTALIZADOR: CONFIG_BOLETA_TRANSMISION
        }

        self.imagen_acta = ImagenReversoBoleta(
            imagenes[self.modulo]).render_svg()

    def _inicializa_pantalla(self):
        """
        Prepara la primera pantalla de la interacción ocultando todos
        los elementos innecesarios del template y
        mostrando la imagen de la boleta.
        """
        self.send_constants()
        self.set_imagen_acta()

        if self.modulo == MODULO_APERTURA:
            self.mensaje = self.MSG_APERTURA
        elif self.modulo == MODULO_TOTALIZADOR:
            self.mensaje = self.MSG_TOTALIZADOR
        else:
            self.mensaje = self.MSG_DEFAULT

        self.set_pantalla()
        self.send_command("show_body")

        # Si ya hay una boleta en la impresora la expulsamos
        if self.parent.rampa.tiene_papel:
            self.parent.rampa.expulsar_boleta()

    def set_pantalla(self, data=None):
        """
        Setea la pantalla de acuerdo al estado actual
        """
        if data is None:
            data = {}

        if self.estado == E_INGRESO_ACTA:
            self.send_command("pantalla_ingresoacta",
                              {"mensaje": self.mensaje,
                               "imagen_acta": quote(self.imagen_acta)})

        elif self.estado == E_MESAYPIN:
            self.send_command("pantalla_mesaypin", [DEBUG,
                                                    "aceptar_mesa_y_pin",
                                                    data.get("mesa", "")])
        elif self.estado == E_INGRESO_DATOS:
            self.cargar_datos_personales(data)
        self.send_constants()

    def cargar_datos_personales(self, data):
        data["teclado_fisico"] = DEBUG
        data["callback_aceptar"] = "aceptar_datos_personales"

        if hasattr(self.parent, "apertura") and self.parent.apertura is not None:
            autoridades = [(autoridad.a_dict()) for autoridad in \
                           self.parent.apertura.autoridades]
            data['foco_hora'] = True
            data["autoridades"] = autoridades
        else:
            data['foco_hora'] = False

            self.parent.apertura = None
        self.set_pantalla_datospersonales(data)

    def set_pantalla_datospersonales(self, data=None):
        if 'autoridades' in data and data['autoridades'] is not None:
            for autoridad in data['autoridades']:
                autoridad['nombre'] = autoridad['nombre'].replace("'", "&#39;")
                autoridad['apellido'] = autoridad['apellido'].replace("'", "&#39;")

        self.send_command("pantalla_datospersonales", data)

    def set_mensaje(self, mensaje):
        self.mensaje = mensaje
        self.send_command("set_mensaje", mensaje)

    def set_pantalla_confirmacion(self, imagen):
        self.send_command("pantalla_confirmacion_apertura",
                          [_("acta_apertura_mesa"), imagen])
        self.send_constants()

    def mensaje_inicial(self):
        if self.modulo == MODULO_APERTURA:
            self.set_mensaje(self.MSG_APERTURA)
        elif self.modulo == MODULO_TOTALIZADOR:
            self.set_mensaje(self.MSG_TOTALIZADOR)
        else:
            self.set_mensaje(self.MSG_DEFAULT)

    def _procesar_callback(self):
        #self.set_mensaje(self.MSG_ESPERE)
        self.sesion.impresora.remover_consultar_tarjeta()
        self.callback()

    def procesar_dialogo(self, respuesta):
        if respuesta:
            if self.callback_aceptar is not None:
                self.callback_aceptar()
        else:
            if self.callback_cancelar is not None:
                self.callback_cancelar()

    def show_dialogo(self, mensaje=None, callback_cancelar=None,
                     callback_aceptar=None, btn_cancelar=False,
                     btn_aceptar=False, confirmacion=False,
                     error=True):
        self.callback_aceptar = callback_aceptar
        self.callback_cancelar = callback_cancelar
        if confirmacion:
            self.send_command("show_dialogo_confirmacion")
        else:
            dialogo = {"mensaje": mensaje,
                       "btn_aceptar": btn_aceptar,
                       "btn_cancelar": btn_cancelar}
            if error:
                self.send_command("show_dialogo_error", dialogo)
            else:
                self.send_command("show_dialogo_accion", dialogo)

    def hide_dialogo(self):
        self.send_command("hide_dialogo_confirmacion")
        self.send_command("hide_dialogo")

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

        self.show_dialogo(callback_aceptar=self.confirmar_envio,
                          callback_cancelar=self.hide_dialogo,
                          confirmacion=True)

    def msg_confirmar_apertura(self, respuesta):
        if respuesta:
            self.parent.confirmar_apertura()
        else:
            self.parent.cargar_datos(self.parent.apertura)

    def msg_mesaypin_incorrecto(self):
        mensaje = {"pregunta": _("mesa_pin_incorrectos")}
        self.show_dialogo(mensaje=mensaje,
                          btn_aceptar=True,
                          callback_aceptar=self.hide_dialogo)

    def msg_error_apertura(self, hay_tag=False):
        if not hay_tag:
            mensaje = {"pregunta": _("papel_no_puesto")}
        else:
            mensaje = {"pregunta": _("apertura_no_almacenada")}
        self.show_dialogo(mensaje=mensaje,
                          btn_aceptar=_("reintentar"),
                          btn_cancelar=True,
                          callback_aceptar=self.reintenta_apertura,
                          callback_cancelar=self.parent.salir)

    def reintenta_apertura(self):
        self.hide_dialogo()
        self.parent.confirmar_apertura()

    def recibir_mesaypin(self, data):
        """ Recibe la mesa y pin ingresada y la valida para
        pasar a la siguiente pantalla, o rechaza el ingreso y vuelve
        a pedir el ingreso de datos
        Respuesta es un json:
            {"mesa": 1,
            "pin": 23533}
        """
        mesa = data['mesa']
        pin = data['pin']
        mesa_obj = Ubicacion.one(numero=mesa)

        if mesa_obj is not None and (pin is not None and
                                     hashlib.sha1(pin).hexdigest() ==
                                     mesa_obj.pin):
            try:
                self.parent._validar_configuracion(mesa, pin)
            except:
                self.sesion.mesa = mesa_obj
                self.estado = E_INGRESO_DATOS
                self.set_pantalla({"callback": ""})
        else:
            self.msg_mesaypin_incorrecto()
            self._intento += 1
            if self._intento >= 3:
                self.sesion.impresora.expulsar_boleta()
                self.parent.quit()

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
                largos = map(lambda x: len(x), autoridad)
                del largos[2]
                if largos != [0, 0, 0]:
                    autoridad_mesa = Autoridad(*autoridad)
                    autoridades.append(autoridad_mesa)

        horaIsNone = (data['hora']['horas'] is None or
                      data['hora']['minutos'] is None)
        if self.modulo == MODULO_APERTURA:
            if horaIsNone:
                data['hora'] = {'horas': 8, 'minutos': 0}
            self.parent.crear_objeto(autoridades, data['hora'])
        else:
            if horaIsNone:
                data['hora'] = {'horas': 18, 'minutos': 0}
            self.parent.guardar_datos_del_presidente(autoridades,
                                                        data['hora'])

    def send_constants(self):
        """Envia todas las constantes de la eleccion."""
        constants_dict = get_constants()
        self.send_command("set_constants", constants_dict)


def get_constants():
    #TODO: ver cuáles de estas constantes son realmente necesarias en
    # las pantallas de interaccion
    translations = (
        "muchas_gracias", "titulo_segundo_suplente", "introduzca_acta_apertura",
        "puede_retirar_boleta", "no_retirar_boleta", "agradecimiento",
        "aguarde_unos_minutos", "aceptar", "cancelar", "introduzca_acta_cierre",
        "ingrese_datos_solicitados", "ingrese_numero_mesa", "confirmar",
        "ingrese_numero_pin", "confirma_datos_correctos", "hora_invalida",
        "titulo_hora", "titulo_minutos", "titulo_apellido", "titulo_nombre",
        "titulo_documento", "titulo_presidente", "titulo_suplente",
        "retire_acta_apertura", "acta_contiene_informacion", "volver_al_inicio",
        "aguarde_procesando_acta", "aguarde_configurando_mesa",
        "apertura_no_almacenada", "papel_no_puesto", "acta_apertura_mesa")
    encabezado = get_config('datos_eleccion')
    mensajes_error = ("hora_invalida", "hora_incompleta", "largo_invalido",
                      "autoridades_invalidas", "autoridades_incompletas",
                      "mesa_pin_incorrectos", "documentos_invalidos",
                      "documentos_numeros_invalidos")

    constants_dict = {
        "juego_de_datos": JUEGO_DE_DATOS,
        "mostrar_cursor": MOSTRAR_CURSOR,
        "encabezado": [(texto, encabezado[texto]) for texto in encabezado],
        "i18n": [(trans, _(trans)) for trans in translations],
        "tipo_doc": [(TIPO_DOC.index(tipo), tipo) for tipo in TIPO_DOC],
        "mensajes_error": dict([(trans, _(trans)) for trans in mensajes_error]),
        "usa_armve": USA_ARMVE,
        "ext_img_voto": EXT_IMG_VOTO,
        "effects": EFECTOS_VOTO,
        "flavor": FLAVOR,
        "cantidad_suplentes": CANTIDAD_SUPLENTES,
        "usa_tildes": USA_TILDES,
        "templates": get_templates(),
        "PATH_TEMPLATES_VOTO": "file:///%s/" % PATH_TEMPLATES_VOTO,
        "USAR_BUFFER_IMPRESION": USAR_BUFFER_IMPRESION,
    }
    return constants_dict


def get_templates():
    templates = {}
    template_names = ("candidato", "candidato_confirmacion", "categoria",
                      "lista", "partido")
    for template in template_names:
        file_name = "%s.html" % template
        template_file = os.path.join(FLAVOR, file_name)
        templates[template] = template_file
    return templates
