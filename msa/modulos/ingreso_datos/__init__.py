"""
Modulo que maneja el ingreso de datos de los usuarios.

Maneja 3 pantallas distintas:
    * Introduccion de mesa y pin (usado en modulo Inicio)
    * Introduccion de datos personales (usado en Apertura y Escrutinio)
    * Pantalla de insercion de acta (usado en Apertura, pero soporta todos los
      tipos de acta)
"""
from gi.repository.GObject import idle_add, timeout_add
from msa.core.documentos.actas import Apertura, Recuento
from msa.modulos import get_sesion
from msa.modulos.base.modulo import ModuloBase
from msa.modulos.constants import (E_CARGA, E_CONFIGURADA, E_INGRESO_ACTA,
                                   E_INGRESO_DATOS, E_INICIAL, E_MESAYPIN,
                                   E_SETUP, MODULO_APERTURA, MODULO_INICIO,
                                   MODULO_MENU, MODULO_RECUENTO,
                                   SUBMODULO_DATOS_APERTURA,
                                   SUBMODULO_DATOS_ESCRUTINIO,
                                   SUBMODULO_MESA_Y_PIN_INICIO)
from msa.modulos.ingreso_datos.controlador import Controlador
from msa.modulos.ingreso_datos.rampa import (RampaApertura, RampaEscrutinio,
                                             RampaInicio)


class Modulo(ModuloBase):

    """ Modulo de ingreso de datos.
        Este modulo funciona como submodulo de Inicio, Apertura y Recuento.
        Muestra las siguientes 3 "pantallas":
            * Ingreso de Mesa y PIN
            * Ingreso de Datos Personales
            * Ingreso de Actas y Certificados
    """
    def __init__(self, nombre):
        """Constructor."""
        self.sesion = get_sesion()
        self.nombre = nombre
        self.web_template = "ingreso_datos"
        self._start_audio()

        # Pantalla de introduccion de mesa y pin del modulo Inicio
        if nombre == SUBMODULO_MESA_Y_PIN_INICIO:
            self.controlador = Controlador(self, E_MESAYPIN, MODULO_INICIO)
            ModuloBase.__init__(self, nombre)
            self.rampa = RampaInicio(self)

        # Pantallas de introduccion de boleta e Introduccion de Datos
        # Personales del podulo de apertura
        elif nombre == SUBMODULO_DATOS_APERTURA:
            # en _tmp_apertura se guarda la instancia temporal de apertura que
            # usamos para manejar el "volver atras" antes de imprimir la
            # apertura
            if self.sesion._tmp_apertura is not None:
                self.apertura = self.sesion._tmp_apertura
                self.estado = E_CARGA
                estado_controlador = E_INGRESO_DATOS
            else:
                self.estado = E_INICIAL
                estado_controlador = None

            self.controlador = Controlador(self, estado_controlador,
                                           MODULO_APERTURA)
            ModuloBase.__init__(self, nombre)
            self.rampa = RampaApertura(self)
        # Pantalla de introduccion de datos personales del escrutinio
        elif nombre == SUBMODULO_DATOS_ESCRUTINIO:
            if hasattr(self.sesion, "apertura"):
                self.apertura = self.sesion.apertura
            self.estado = E_SETUP
            estado_controlador = E_INGRESO_DATOS
            self.controlador = Controlador(self, estado_controlador,
                                           MODULO_RECUENTO)
            ModuloBase.__init__(self, nombre)
            self.rampa = RampaEscrutinio(self)

    def _cargar_ui_inicio(self):
        """Carga la UI del modulo."""
        ModuloBase._cargar_ui_web(self)
        self._inicio()
        self.controlador.set_pantalla()
        self.ventana.show_all()

    def set_pantalla(self, pantalla):
        """Setea la pantalla indicada."""
        self.controlador.set_screen(pantalla)

    def _inicio(self):
        """Funcion llamada desde el controlador."""
        self.controlador.send_constants()

    def _abrir_mesa(self, mesa):
        """ Abre la mesa. """
        if mesa is not None:
            self._mesa = mesa
            # Le seteo el atributo abierta si la configuración de la mesa fue
            # con el acta de apertura
            self.sesion.mesa = mesa
            # establezco el estado del modulo como "configurada"
            self.estado = E_CONFIGURADA
            # si es una elección que usa apertura vamos al modulo, sino
            # directamente mostramos el menú
            if self.config("realizar_apertura"):
                self.ret_code = SUBMODULO_DATOS_APERTURA
            else:
                self.ret_code = MODULO_MENU
            # expulsamos la boleta y salimos
            self.rampa.expulsar_boleta()
            idle_add(self.quit)
        else:
            # si la mesa no es válida volvemos al estado inicial y mostramos
            # pin incorrecto
            self.estado = E_INICIAL
            self.ventana.remove(self.ventana.children()[0])
            self._cargar_ui_web()
            self.ventana.show_all()
            self._pantalla_principal()
            self.controlador.msg_mesaypin_incorrecto()

    def salir(self):
        self.salir_a_menu()

    def procesar_tag_apertura(self, tag):
        """Procesa el tag que se apoya en el lector."""
        if tag.vacio and not tag.read_only:
            if self.controlador.estado == E_INGRESO_ACTA:
                if self.rampa.tiene_papel:
                    self.apertura = None
                    self.sesion.apertura = None

                    con_datos = self.config("con_datos_personales")
                    if con_datos:
                        self.cargar_datos()
                    else:
                        self.crear_apertura()
                else:
                    self.controlador.set_mensaje(_("apoyo_acta"))

        elif not tag.es_apertura():
            self.controlador.set_mensaje(_("acta_contiene_informacion"))

            def _expulsar():
                self.controlador.set_mensaje(self.controlador.MSG_APERTURA)
                self.rampa.expulsar_boleta()
            timeout_add(2500, _expulsar)

    def mensaje_inicial(self):
        """Muestra el mensaje_inicial, borra la apertura de la sesion."""
        self.apertura = None
        self.sesion.apertura = None
        self.controlador.mensaje_inicial()

    def volver(self, apertura):
        """Vuelve a la pantalla de inicial"""
        self.cargar_datos(apertura)

    def cargar_datos(self, apertura=None):
        """ Callback de salida del estado inicial, que indica que se obtuvo un
            tag de apertura.  Ahora se pasa al estado de carga de datos,
            solicita el ingreso de datos del Presidente de Mesa.
        """
        self.estado = E_CARGA
        self.controlador.estado = E_INGRESO_DATOS

        hora = None
        autoridades = None
        if apertura is not None:
            hora = apertura.hora
            autoridades = [(autoridad.a_dict()) for autoridad in
                           apertura.autoridades]

        self.controlador.set_pantalla({"hora": hora,
                                      "autoridades": autoridades})

    def cargar_apertura(self, tag):
        """Carga los datos de la apertura en el menu cuando se apoya."""
        apertura = Apertura.desde_tag(tag.datos)
        estado = self.controlador.estado
        mesa = self.sesion.mesa
        if estado != E_INGRESO_DATOS or (estado == E_INGRESO_DATOS and
                                         mesa.numero == apertura.mesa.numero):
            self.apertura = apertura
            self.controlador.set_pantalla({"mesa": apertura.mesa.numero})

    def reiniciar_modulo(self):
        """Reinicia modulo."""
        self.estado = E_INICIAL
        self.controlador.estado = E_INGRESO_ACTA
        self.controlador._inicializa_pantalla()

    def crear_apertura(self, autoridades=None, hora=None):
        """
        Recibe un instancia de Presidente de Mesa y del suplente con los datos
        que cargo el usuario.
        """
        if autoridades is None:
            autoridades = []
        self.sesion._tmp_apertura = Apertura(self.sesion.mesa, autoridades,
                                             hora)

        self.salir_a_apertura()

    def salir_a_apertura(self):
        self.ret_code = MODULO_APERTURA
        self.quit()

    def configurar_desde_apertura(self, tag):
        """
        Configura la mesa con los datos que contiene el tag.
        """
        # traemos el objeto apertura desde los datos del tag
        apertura = Apertura.desde_tag(tag.datos)

        def _salir():
            """Estamblece la apertura y la mesa en la sesion y sale al menu."""
            apertura.mesa = self.sesion.mesa
            self.sesion.apertura = apertura
            self.rampa.desregistrar_eventos()
            self.salir_a_menu()

        # si la apertura es válida y el número de la mesa que estamos abriendo
        # coincide con el número de la mesa de la apertura apoyada abrimos la
        # mesa en caso contrario mostramos un mensaje de error
        if apertura.mesa is not None:
            if apertura.mesa.numero == self.sesion.mesa.numero:
                self.rampa.expulsar_boleta()
                self.rampa.consultar_tarjeta(
                    lambda x: timeout_add(500, _salir))
            else:
                self.controlador.set_mensaje(_("acta_mesa_erronea"))
                self.rampa.expulsar_boleta()

    def salir_a_menu(self):
        """ Sale del módulo de apertura, vuelve al comienzo con la maquina
            desconfigurada.
        """
        if hasattr(self, 'pantalla') and self.pantalla is not None:
            self.pantalla.destroy()
        if self.browser is not None:
            self.ventana.remove(self.browser)
        self.rampa.remover_consultar_lector()
        self.ret_code = MODULO_MENU
        self.quit()

    def generar_recuento(self, autoridades=None, hora=None):
        """
        Recibe un instancia de Presidente de Mesa, con los datos que cargo el
        usuario.
        """
        self.sesion.recuento = Recuento(self.sesion.mesa, autoridades, hora)
        self.ret_code = MODULO_RECUENTO
        self.quit()

    def cargar_recuento_copias(self, datos_tag):
        """Carga el modulo recuento en modo de copia de actas"""
        recuento = Recuento.desde_tag(datos_tag.datos)
        recuento.reimpresion = True
        self.sesion.recuento = recuento
        self.ret_code = MODULO_RECUENTO
        self.quit()
