# -*- coding: utf-8 -*-
import gobject
import time
from urllib2 import quote

from msa.core import get_config
from msa.core.clases import Recuento
from msa.voto.constants import E_RECUENTO, RECUENTO_ERROR, RECUENTO_OK, \
    RECUENTO_ERROR_REPETIDO, MODULO_TOTALIZADOR, \
    SECUENCIA_CERTIFICADOS_TOTALIZACION
from msa.voto.controllers.totalizador import ControllerTotalizador
from msa.voto.controllers.interaccion import ControllerInteraccion
from msa.voto.modulos.recuento import ModuloRecuento
from msa.core.rfid.constants import TAG_ADMIN, TAG_RECUENTO
from msa.voto.sesion import get_sesion


sesion = get_sesion()


class ModuloTotalizador(ModuloRecuento):
    controller_recuento = ControllerTotalizador

    def _cargar_controller_interaccion(self):
        self.controller = ControllerInteraccion(self,
                                                modulo=MODULO_TOTALIZADOR)

    def _procesar_tag(self, tag, datos):
        """ Evento. Procesa el tag recibido por parametro. Cumple la funcion
            del procesar_tag() de PantallaRecuento de recuento Gtk.

            Argumentos:
            tag   -- El objeto TAG recibido.
            datos -- Los datos almacenados en el tag recibido.

            Si el tag no es ICODE se descarta el evento.
            Si su tipo no es voto, o está vacío, se devuelve error.
            Se intenta sumar los datos al recuento, si devuelve False
            es porque el tag ya fue sumado, sino está ok.
        """
        # TODO: Rever esta logica cuando se implementen las pantallas
        # anteriones en HTML
        if self.estado == E_RECUENTO:
            serial = tag['serial']
            tipo_tag = tag['tipo']
            if datos is None:
                self.controller.set_panel_estado(RECUENTO_ERROR)
            elif tipo_tag != TAG_RECUENTO:
                if tipo_tag == TAG_ADMIN:
                    self.administrador()
                else:
                    self.controller.set_panel_estado(RECUENTO_ERROR)
            else:
                try:
                    recuento = Recuento.desde_tag(datos)
                    if not sesion.recuento.serial_sumado(serial):
                        if sesion.recuento.mesa.cod_datos == \
                                recuento.mesa.cod_datos:
                            sesion.recuento.sumar_recuento(recuento, serial)
                            sesion.recuento.hora_fin = time.time()
                            sesion.ultima_seleccion = recuento

                            # Dibujo boleta
                            imagen = recuento.a_imagen(de_muestra=True,
                                                       svg=True)
                            image_data = quote(imagen.encode("utf-8"))

                            cant_leidas = sesion.recuento.boletas_contadas()
                            self.controller.actualizar_resultados(
                                sesion.ultima_seleccion,
                                cant_leidas, image_data)
                            gobject.timeout_add(
                                200,
                                self.controller.set_panel_estado, RECUENTO_OK)
                        else:
                            self.controller.set_panel_estado(RECUENTO_ERROR)
                    else:
                        self.controller.set_panel_estado(
                            RECUENTO_ERROR_REPETIDO)
                except Exception as e:
                    print(e)
                    self.controller.set_panel_estado(RECUENTO_ERROR)
        else:
            if hasattr(self.controller, "procesar_tag"):
                self.controller.procesar_tag(tag, datos)

    def set_campos_extra(self, campos_recuento):
        pass

    def get_campos_extra(self):
        campos_extra = []
        campos_extra.append({"codigo": "",
                             "titulo": _("boletas_procesadas"),
                             "editable": False,
                             "valor": sesion.recuento.boletas_contadas()})

        for lista in get_config("listas_especiales"):
            campos_extra.append(
                {"codigo": lista,
                 "titulo": _("titulo_votos_%s" % lista[-3:]),
                 "editable": False,
                 "valor": sesion.recuento.listas_especiales[lista]})

        return campos_extra

    def set_print_manager(self, callback):
        ModuloRecuento.set_print_manager(self, callback)
        self.print_manager.secuencia_certificados = \
            SECUENCIA_CERTIFICADOS_TOTALIZACION
