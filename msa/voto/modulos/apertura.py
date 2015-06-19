# -*- coding: utf-8 -*-
"""Implementa clases para hacer el circuito del apertura de mesa."""

import time

from base64 import b64encode
from urllib2 import quote

from msa.settings import QUEMA
from msa.core.clases import Apertura
from msa.core.rfid.constants import TAG_APERTURA
from msa.core.settings import USA_ARMVE
from msa.voto.constants import MODULO_APERTURA, MODULO_ADMIN, E_REGISTRANDO, \
    E_INICIAL, E_CARGA, E_CONFIRMACION, E_INGRESO_DATOS, E_INGRESO_ACTA
from msa.voto.controllers.interaccion import ControllerInteraccion
from msa.voto.modulos import Modulo
from msa.voto.modulos.rampa import RampaApertura
from msa.voto.sesion import get_sesion


sesion = get_sesion()


class ModuloApertura(Modulo):

    """ Modulo de Apertura de votos.

        Este módulo permite generar el acta de apertura de una mesa.
        El usuario debe ingresar el acta en la maquina, agregar y confirmar sus
        datos e imprimirla.
    """

    def __init__(self):
        """Constructor"""
        self.es_modulo_web = True
        self.web_template = "apertura"
        self.rampa = RampaApertura(self)
        self.controller = ControllerInteraccion(self, modulo=MODULO_APERTURA)
        self._mensaje = None

        Modulo.__init__(self)

        self.ret_code = MODULO_APERTURA
        self.estado = E_INICIAL
        self._cargar_ui_apertura()

    def _cargar_ui_apertura(self):
        pass
        #self.controller._inicializa_pantalla()

    def reiniciar_modulo(self):
        self.estado = E_INICIAL
        self.controller.estado = E_INGRESO_ACTA
        self.controller._inicializa_pantalla()

    def cargar_datos(self, apertura=None):
        """ Callback de salida del estado inicial, que indica que se obtuvo un
            tag de apertura.  Ahora se pasa al estado de carga de datos,
            solicita el ingreso de datos del Presidente de Mesa.
        """
        self.estado = E_CARGA
        self.controller.estado = E_INGRESO_DATOS

        hora = None
        autoridades = None
        if apertura is not None:
            hora = apertura.hora
            autoridades = [(autoridad.a_dict()) for autoridad in \
                           apertura.autoridades]

        self.controller.set_pantalla({"hora": hora,
                                      "autoridades": autoridades})

    def _configurar_mesa(self, datos_tag):
        """
        Configura la mesa con los datos que contiene el tag.
        """
        apertura = Apertura.desde_tag(datos_tag)
        if apertura.mesa is not None:
            sesion.apertura = apertura
            sesion.mesa = apertura.mesa
            sesion.impresora.expulsar_boleta()
            sesion.impresora.consultar_tarjeta(lambda x: self.salir())

    def crear_objeto(self, autoridades, hora):
        """
        Recibe un instancia de Presidente de Mesa y del suplente con los datos
        que cargo el usuario.
        """
        self.apertura = Apertura(sesion.mesa, autoridades, hora)
        self.estado = E_CONFIRMACION
        self.controller.estado = E_CONFIRMACION
        imagen_acta = self.apertura.a_imagen(svg=True, de_muestra=True)
        imagen_data = quote(imagen_acta.encode("utf-8"))
        self.controller.set_pantalla_confirmacion(imagen_data)

    def confirmar_apertura(self):
        if self.__guardar_e_imprimir():
            self.estado = E_REGISTRANDO

            def _inner(printer_status=None):
                sesion.impresora.remover_boleta_expulsada()
                sesion.impresora.remover_insertando_papel()
                self.salir()

            if USA_ARMVE:
                sesion.impresora.registar_boleta_expulsada(_inner)
            else:
                sesion.impresora.registrar_insertando_papel(_inner)
        else:
            tag = self.rampa.datos_tag
            self.controller.msg_error_apertura(tag)

    def __guardar_e_imprimir(self):
        """ Función que se encarga primero de guardar los datos y corroborar
            que esté todo ok.
            Si es así imprime y devuelve True o False en cualquier caso
            contrario
        """
        tag = self.rampa.datos_tag
        if not tag or not sesion.impresora:
            return False

        # Chequeo que el tag esté vacío
        datos_tag = tag['datos']
        if datos_tag != '':
            return False

        # Todo ok, guardo el acta de apertura, si devuelve True, imprimo.
        if self._guardar_apertura():
            sesion.apertura = self.apertura
            self._imprimir_acta()

            def esperar_vacia(tiene_tarjeta):
                if not tiene_tarjeta:
                    sesion.impresora.remover_consultar_tarjeta()
                    self.salir()
            sesion.impresora.consultar_tarjeta(esperar_vacia)
            return True
        else:
            return False

    def _guardar_apertura(self):
        """ Guarda los datos en el tag, lo vuelve a leer y compara los dos
            strings para verificar la correcta escritura.
            Devuelve True si el guardado y la comprobación están correctos,
            False en caso contrario.
        """
        guardado_ok = False

        if USA_ARMVE:
            datos = self.apertura.a_tag()
            marcar_ro = QUEMA
            guardado_ok = sesion.lector.guardar_tag(TAG_APERTURA, datos,
                                                    marcar_ro)
        else:
            datos1 = self.apertura.a_tag()
            tag_grabado = self._guarda_tag(datos1)

            if tag_grabado:
                datos2 = self._lee_tag()
                if datos1 == datos2:
                    guardado_ok = True
        return guardado_ok

    def _guarda_tag(self, datos):
        """ Esta función guarda los datos en el tag """
        # Intenta guardar el tag devolviendo True o False si pudo o no.
        # Ciclo hasta encontrar un tag
        tag = self.rampa.datos_tag
        if not tag:
            return False
        # No puedo grabar si el tag ya tiene algo
        if tag['datos'] != '':
            return False
        # Intento grabar, si algo sale mal salgo con error.
        try:
            #datos = datos.encode('utf-8')
            sesion.lector.escribe_datos(tag, datos, TAG_APERTURA)
        except Exception as e:
            sesion.logger.exception(e)
            return False
        # Si llegue hasta aca, es porque pude guardar los datos sin problemas.
        return True

    def _lee_tag(self):
        """ Función para obtener un tag y devolver sus datos o vacío """
        if USA_ARMVE:
            tag = self.rampa.datos_tag
        else:
            tag = sesion.lector.get_tag()
        datos = tag['datos']

        return datos

    def _imprimir_acta(self):
        tipo_tag = self.apertura.__class__.__name__
        tag = self.apertura.a_tag()
        sesion.impresora.posicionar_al_inicio()
        sesion.impresora.imprimir_serializado(tipo_tag, b64encode(tag))
        if not USA_ARMVE:
            time.sleep(15)

    def mensaje_inicial(self):
        self.apertura = None
        self.controller.mensaje_inicial()

    def volver(self, apertura):
        """Vuelve a la pantalla de inicial"""
        self.cargar_datos(apertura)

    def salir(self):
        """ Sale del módulo de apertura, vuelve al comienzo con la maquina
            desconfigurada
        """
        if hasattr(self, 'pantalla') and self.pantalla is not None:
            self.pantalla.destroy()
        if self.browser is not None:
            self.ventana.remove(self.browser)
        sesion.lector.remover_consultar_lector()
        self.ret_code = MODULO_ADMIN
        self.quit()

    def procesar_tag(self, tag_dict):
        read_only = tag_dict.get("read_only")
        if tag_dict['datos'] == '' and not read_only:
            if self.controller.estado == E_INGRESO_ACTA:
                self.cargar_datos()
        else:
            self.controller.set_mensaje(_("acta_contiene_informacion"))
            sesion.impresora.expulsar_boleta()
