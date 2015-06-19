# -*- coding: utf-8 -*-
import gobject
import time

from datetime import datetime

from msa.core.imaging import get_dpi_boletas
from msa.core.rfid.constants import TAG_VOTO
from msa.core.settings import USAR_BUFFER_IMPRESION, USA_ARMVE
from msa.settings import MODO_DEMO
from msa.voto.sesion import get_sesion
from msa.voto.settings import TIMEOUT_FINAL, \
    REINTENTOS_REGISTRADOR, REINTENTOS_REGISTRADOR_MALATA


sesion = get_sesion()


class Registrador(object):

    def __init__(self, callback, seleccion, parent):
        self.callback = callback
        self.seleccion = seleccion
        self.timeout = TIMEOUT_FINAL
        self.parent = parent
        self._lanzo_evento = False

    def _registrar_voto(self):
        fallo = False

        def atajar_no_evento():
            esperar_vacia({"paper_out_2": False})

        def esperar_vacia(estado):
            if not estado['paper_out_2'] and not self.lanzo_evento:
                self.lanzo_evento = True
                sesion.impresora.remover_consultar_tarjeta()
                sesion.impresora.consultar_tarjeta(
                    self.parent.rampa.cambio_sensor_2)
                if not fallo:
                    self.callback()
            return False
        self.lanzo_evento = False
        sesion.impresora.consultar_tarjeta(esperar_vacia)
        gobject.timeout_add(10000, atajar_no_evento)

        respuesta = sesion.impresora.registrar(self.seleccion)
        if respuesta['status'] == "TAG_NO_GUARDADO":
            fallo = True
            self._error()

    def _proceso(self):
        """Ciclo principal de registro.

        Guarda los datos en el tag, lo vuelve a leer y compara los dos
        strings para verificar la correcta escritura.
        Si los datos son iguales imprime la boleta.
        """

        def esperar_vacia(tiene_tarjeta):
            if not tiene_tarjeta:
                sesion.impresora.remover_consultar_tarjeta()
                self.callback()
                sesion.impresora.consultar_tarjeta(self.parent._chequear_papel)
            return False

        imprimiendo = False
        if USA_ARMVE:
            marcar_ro = not MODO_DEMO

            self._prepara_impresion(self.seleccion)
            sesion.impresora.linefeed(20)
            time.sleep(0.3)
            status = sesion.impresora.full_paper_status()
            if status is None or not status['paper_out_2']:
                self._recuperar_papel()
                return
            else:
                sesion.impresora.backfeed(20)
                time.sleep(0.1)
                tag_guardado = sesion.lector.guardar_tag(
                    TAG_VOTO, self.seleccion.a_string(), marcar_ro)
                if tag_guardado:
                    imprimiendo = True
                    self._imprime()
                    sesion.impresora.consultar_tarjeta(esperar_vacia)
                else:
                    self._error()
        else:
            datos1 = self.seleccion.a_tag()
            for i in range(REINTENTOS_REGISTRADOR_MALATA):
                tag_grabado = self._guarda_tag(datos1)
                if tag_grabado:
                    # Le doy tiempo al lector antes de consultarlo
                    datos2 = self._lee_tag()
                    if datos1 == datos2:
                        imprimiendo = True
                        self._imprime()
                        sesion.impresora.consultar_tarjeta(esperar_vacia)
                    else:
                        self._error()
                    break
        if not imprimiendo:
            self.callback()

    def _guarda_tag(self, datos):
        # Intenta guardar el tag devolviendo True o False si pudo o no.
        # Ciclo hasta encontrar un tag
        esperar = True
        reintentos = REINTENTOS_REGISTRADOR
        while esperar:
            if not USA_ARMVE:
                time.sleep(0.3)
            tag = sesion.lector.get_tag()
            esperar = tag is None
            if reintentos > 0:
                reintentos -= 1
            else:
                return False

        # No puedo grabar si el tag ya tiene algo
        if tag['datos'] != '':
            return False

        # No quemo los tags si estoy en modo debug
        marcar_ro = not MODO_DEMO

        # Intento grabar, si algo sale mal salgo con error.
        try:
            sesion.lector.escribe_datos(tag, datos, TAG_VOTO, marcar_ro)
        except Exception as e:
            sesion.logger.exception(e)
            return False

        # Si llegue hasta aca, es porque pude guardar los datos sin problemas.
        return True

    def _lee_tag(self):
        esperar = True
        reintentos = REINTENTOS_REGISTRADOR
        while esperar:
            if not USA_ARMVE:
                time.sleep(0.2)
            tag = sesion.lector.get_tag()
            esperar = tag is None
            if reintentos > 0:
                reintentos -= 1
            else:
                return False
        try:
            datos = tag['datos']
        except:
            datos = ''
        return datos

    def _imprime(self):
        if not USA_ARMVE:
            sesion.impresora.posicionar_al_inicio()

        if USAR_BUFFER_IMPRESION:
            sesion.impresora.do_print()
        else:
            self._imprimir_serializado(self.seleccion, transpose=True,
                                       only_buffer=False)

    def _imprimir_serializado(self, seleccion, transpose, only_buffer):
        tipo_tag = self.seleccion.__class__.__name__
        tag = self.seleccion.a_string()
        sesion.impresora.imprimir_serializado(tipo_tag, tag, transpose,
                                              only_buffer)

    def _prepara_impresion(self, seleccion):
        """ Método que se encarga de imprimir efectivamente la boleta debug
        voto"""
        self.seleccion = seleccion
        if USAR_BUFFER_IMPRESION:
            if not USA_ARMVE:
                sesion.logger.debug("iniciando buffer de impresion")
                start = datetime.now()
                # dibujo boleta
                imagen = seleccion.a_imagen()

                # genero imagen PIL para impresión:
                im = imagen.output()

                # imprimo:
                dpi = get_dpi_boletas()
                sesion.impresora.imprimir_image(im, dpi=dpi, transpose=True,
                                                only_buffer=True)
                end = datetime.now()
                txt_t = "tiempo total de buffer de impresion %s" % \
                    str(end - start)
                sesion.logger.debug(txt_t)
            else:
                self._imprimir_serializado(self.seleccion, transpose=True,
                                           only_buffer=True)

    def _recuperar_papel(self):
        """ Función de error, si el guardado de la boleta fue erróneo,
            se muestra un mensaje acorde.
        """
        mensaje = {"alerta": _("error_grabar_boleta_alerta"),
                   "aclaracion": _("quite_la_boleta")}
        self.parent.show_dialogo(mensaje=mensaje,
                                 btn_aceptar=False,
                                 callback_aceptar=None)

    def _error(self):
        """ Función de error, si el guardado de la boleta fue erróneo,
            se muestra un mensaje acorde.
        """
        self.parent.controller.send_command("hide_all")

        mensaje = {"alerta": _("error_grabar_boleta_alerta"),
                   "aclaracion": _("error_grabar_boleta_aclaracion")}

        def aceptar_error():
            sesion.impresora.expulsar_boleta()
            self.parent.pantalla_insercion()

        self.parent.show_dialogo(
            mensaje=mensaje, btn_aceptar=True,
            callback_aceptar=aceptar_error)


