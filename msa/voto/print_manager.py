# -*- coding: utf-8 -*-
import gobject
import time

from base64 import b64encode
from dbus.exceptions import DBusException
from json import dumps

from msa.core.clases import Categoria
from msa.core.constants import CIERRE_RECUENTO, CIERRE_TRANSMISION, \
    CIERRE_ESCRUTINIO, CIERRE_COPIA_FIEL, CIERRE_CERTIFICADO
from msa.core.rfid.constants import TAG_RECUENTO, TAG_NO_ENTRA
from msa.core.settings import DESPLAZAMIENTO_BOLETA, USA_ARMVE, ACTA_DESGLOSADA
from msa.settings import QUEMA
from msa.voto.constants import RECUENTO_GENERANDO, RECUENTO_IMPRIMIENDO, \
    SECUENCIA_CERTIFICADOS
from msa.voto.sesion import get_sesion


sesion = get_sesion()


class PrintManager(object):
    secuencia_certificados = SECUENCIA_CERTIFICADOS

    def __init__(self, modulo, callback, pre_page_callback=None,
            post_page_callback=None, waiting_paper_callback=None):
        self.modulo = modulo
        self.callback = callback
        self.pre_page_callback = pre_page_callback
        self.post_page_callback = post_page_callback
        self.waiting_paper_callback = waiting_paper_callback
        self.controller = modulo.controller
        self.primer_acta = False

        self.mensajes = {
            CIERRE_RECUENTO: {
                "alerta": _("recuento_no_almacenado_alerta"),
                "aclaracion": _("recuento_no_almacenado_aclaracion")
            },
            CIERRE_TRANSMISION: {
                "alerta": _("transmision_no_almacenada_alerta"),
                "aclaracion": _("transmision_no_almacenada_aclaracion")
            },
            CIERRE_ESCRUTINIO: {
                "alerta": _("certificado_no_impreso_alerta"),
                "aclaracion": _("certificado_no_impreso_aclaracion")
            },
            CIERRE_CERTIFICADO: {
                "alerta": _("certificado_no_impreso_alerta"),
                "aclaracion": _("certificado_no_impreso_aclaracion")
            },
            CIERRE_COPIA_FIEL: {
                "alerta": _("certificado_no_impreso_alerta"),
                "aclaracion": _("certificado_no_impreso_aclaracion")
            }

        }
        self.create_pages()

    def create_pages(self):
        if not ACTA_DESGLOSADA:
            self.pages = [(cert, None, None) for cert
                          in self.secuencia_certificados]
        else:
            self.pages = []
            categorias = Categoria.many(sorted="posicion")
            for tipo_certificado in self.secuencia_certificados:
                for categoria in categorias:
                    self.pages.append((tipo_certificado, categoria.codigo,
                                       categoria.nombre))

    def panel(self, msg):
        self.controller.set_panel_estado(msg)

    def reset_copias(self):
        if USA_ARMVE:
            sesion.impresora.remover_insertando_papel()
        else:
            sesion.impresora.remover_consultar_tarjeta()
        self.controller.hide_preview()
        self.controller.limpiar_panel_estado()
        self.controller.habilitar_botones()
        self.controller.set_pantalla_impresion_certificados()
        self.modulo.habilitar_impresion_certificados()

    def imprimir_secuencia(self, copias=False, pre_page_callback=None,
                           post_page_callback=None,
                           waiting_paper_callback=None):
        """ pre_page_callback y post_page_callback reciben como parametro
            la page sobre la cual son llamados.
        """
        # Solo modifico los callbacks de post y pre impresion de página si los
        # paso explicitamente para evitar que se sobreescriban en la
        # autorreferencia que hace esta funcion
        if pre_page_callback is not None:
            self.pre_page_callback = pre_page_callback
        if post_page_callback is not None:
            self.post_page_callback = post_page_callback
        if waiting_paper_callback is not None:
            self.waiting_paper_callback = waiting_paper_callback

        if copias:
            self.primer_acta = False
            if sesion.recuento.hora is None:
                self.callback = self.reset_copias
                tipo_acta = CIERRE_COPIA_FIEL
            else:
                tipo_acta = CIERRE_CERTIFICADO

            if not ACTA_DESGLOSADA:
                self.pages = [(tipo_acta, None, None)]
            elif sesion.recuento.cod_categoria is not None:
                categoria = Categoria.get(sesion.recuento.cod_categoria)
                self.pages = [(tipo_acta, sesion.recuento.cod_categoria,
                               categoria.nombre)]
            else:
                self.pages = []
                categorias = Categoria.all(sorted="posicion")
                for categoria in categorias:
                    self.pages.append((tipo_acta, categoria.codigo,
                                       categoria.nombre))
        try:
            page = self.pages.pop(0)

            def _inner(datos_sensores):
                tiene_tarjeta = datos_sensores['paper_out_1']
                if tiene_tarjeta:
                    if USA_ARMVE:
                        self.modulo.rampa.remover_nuevo_papel()
                    else:
                        sesion.impresora.remover_insertando_papel()

                    self.panel(RECUENTO_GENERANDO)
                    gobject.timeout_add(200, self.imprimir, page,
                                        self.imprimir_secuencia, copias)
            papel = sesion.impresora.full_paper_status()
            if papel is not None and papel['paper_out_1']:
                _inner(papel)
            else:
                if self.waiting_paper_callback is not None:
                    self.waiting_paper_callback(page)
                    if USA_ARMVE:
                        self.modulo.rampa.registrar_nuevo_papel(_inner)
                    else:
                        sesion.impresora.registrar_insertando_papel(_inner)
        except IndexError:
            self.callback()

    def imprimir(self, tipo_acta, callback, copias=False):
        """ Callback que se ejecuta cuando el usuario confirma guardar e
        imprimir el tag/boleta de recuento """
        if self.pre_page_callback is not None:
            self.pre_page_callback(tipo_acta)

        def reintentar_impresion():
            self._reintentar(tipo_acta)

        def _inner(copias=False):
            papel = sesion.impresora.full_paper_status()
            if papel is not None and papel['paper_out_1']:
                if self.primer_acta:
                    self.primer_acta = False
                    if USA_ARMVE:
                        sesion.impresora.backfeed(DESPLAZAMIENTO_BOLETA * 4)
                        time.sleep(0.3)
                    else:
                        sesion.impresora.linefeed(DESPLAZAMIENTO_BOLETA)
                elif not copias:
                    sesion.impresora.tomar_tarjeta()

                # Espero que se posicione el acta.
                if not USA_ARMVE:
                    time.sleep(1)
                if self._guardar_e_imprimir(tipo_acta):
                    def esperar_vacia(datos_sensores=None):
                        if self.post_page_callback is not None:
                            self.post_page_callback(tipo_acta)
                        if USA_ARMVE:
                            sesion.impresora.remover_boleta_expulsada()
                        else:
                            sesion.impresora.remover_insertando_papel()

                        self.controller.limpiar_panel_estado()
                        callback()

                    if USA_ARMVE:
                        sesion.impresora.registar_boleta_expulsada(esperar_vacia)
                    else:
                        sesion.impresora.registrar_insertando_papel(esperar_vacia)

                else:
                    sesion.impresora.expulsar_boleta()
                    self.controller.limpiar_panel_estado()
                    mensaje = self.mensajes[tipo_acta[0]]

                    self.modulo.show_dialogo(mensaje=mensaje,
                        btn_aceptar=True,
                        callback_aceptar=reintentar_impresion)
            elif not copias:
                self.controller.ocultar_panel_estado()
                mensaje = {"alerta": _("papel_no_puesto")}
                self.modulo.show_dialogo(mensaje=mensaje,
                                         btn_aceptar=True,
                                         callback_aceptar=reintentar_impresion)
        gobject.timeout_add(200, _inner, copias)

    def _guardar_e_imprimir(self, tipo_acta):
        """ Función que se encarga primero de guardar los datos y corroborar
        que esté todo ok. Si es así imprime y devuelve True o False en
        cualquier caso contrario
        """
        tag = sesion.lector.get_tag()
        if tipo_acta[0] in (CIERRE_RECUENTO, CIERRE_TRANSMISION):
            if not tag or not sesion.impresora:
                return False
        elif tipo_acta[0] in (CIERRE_ESCRUTINIO, CIERRE_COPIA_FIEL,
                              CIERRE_CERTIFICADO) and tag is not None:
            return False
        else:
            tag = None

        # Guardo el recuento, si devuelve True, imprimo.
        if (tipo_acta[0] in (CIERRE_ESCRUTINIO, CIERRE_COPIA_FIEL,
                             CIERRE_CERTIFICADO) and tag is None) or \
            (tipo_acta[0] in (CIERRE_RECUENTO, CIERRE_TRANSMISION)
             and self._guardar_recuento(tag, tipo_acta[1])):

            self._imprimir_acta(tipo_acta)

            return True
        else:
            return False

    def _reintentar(self, tipo_acta):
        if tipo_acta[0] != CIERRE_RECUENTO or (
                sesion.impresora.tarjeta_ingresada() and
                sesion.impresora.tarjeta_sin_retirar()):
            self.panel(RECUENTO_GENERANDO)
            gobject.timeout_add(200, self.imprimir, tipo_acta,
                                self.imprimir_secuencia)
        else:
            # TODO: implementar una pantalla mas linda desde el lado del HTML.
            mensaje = {"aclaracion": _("ingrese_certificado_correspondiente")}
            self.modulo.show_dialogo(mensaje=mensaje)

            def esperar(tiene_tarjeta):
                if tiene_tarjeta:
                    sesion.impresora.remover_consultar_tarjeta()
                    self.controller.hide_dialogo()
                    if self.primer_acta:
                        if USA_ARMVE:
                            desp = DESPLAZAMIENTO_BOLETA * 4
                            sesion.impresora.linefeed(desp)
                    self.panel(RECUENTO_GENERANDO)
                    gobject.timeout_add(200, self.imprimir, tipo_acta,
                                        self.imprimir_secuencia)

            if USA_ARMVE:
                self.modulo.rampa.registrar_nuevo_papel(esperar)
            else:
                sesion.impresora.registrar_insertando_papel(esperar)

    def _imprimir_acta(self, tipo_acta):
        if not USA_ARMVE:
            sesion.impresora.posicionar_al_inicio()
            self.panel(RECUENTO_IMPRIMIENDO)

        if sesion.recuento.autoridades:
            autoridades = [aut.a_dict() for aut in sesion.recuento.autoridades]
        else:
            autoridades = None

        extra_data = {
            "tipo_acta": tipo_acta,
            "autoridades": autoridades,
            "hora": sesion.recuento.hora
        }
        try:
            sesion.impresora.imprimir_serializado(
                "Recuento", b64encode(sesion.recuento.a_tag(tipo_acta[1])),
                extra_data=dumps(extra_data))
        except DBusException:
            # ignorando posible timeout de dbus para carga de buffer
            pass

        if USA_ARMVE:
            self.panel(RECUENTO_IMPRIMIENDO)

    def _guardar_recuento(self, tag, categoria=None):
        """ Guarda los datos en el tag, lo vuelve a leer y compara los dos
            strings para verificar la correcta escritura.
            Devuelve True si el guardado y la comprobación están correctos,
            False en caso contrario.
        """
        guardado_ok = False
        marcar_ro = QUEMA
        datos1 = sesion.recuento.a_tag(categoria)

        if tag['datos'] != '':
            return False

        if not USA_ARMVE:
            # No quemo los tags si estoy en modo debug
            tag_grabado = self._guardar_tag(tag, datos1, marcar_ro)
            if tag_grabado:
                datos2 = self.modulo._lee_tag()
                if datos2 == "":
                    metadata = sesion.lector.get_tag_metadata()
                    guardado_ok = (metadata["tipo"] == TAG_NO_ENTRA or
                                   datos1 == datos2)
                else:
                    guardado_ok = datos1 == datos2
        else:
            guardado_ok = sesion.lector.guardar_tag(TAG_RECUENTO, datos1,
                                                    marcar_ro)
            if not guardado_ok:
                sesion.lector.reset()
                guardado_ok = sesion.lector.guardar_tag(TAG_RECUENTO, datos1,
                                                        marcar_ro)
        return guardado_ok

    def _guardar_tag(self, tag, datos, marcar_ro):
        #Esta función guarda los datos en el tag para malata
        # Intento grabar, si algo sale mal salgo con error.
        positivo = False
        for i in range(10):
            try:
                sesion.lector.escribe_datos(tag, datos, TAG_RECUENTO,
                                            marcar_ro)
            except Exception, e:
                sesion.logger.exception(e)
                sesion.logger.debug(_("fallo_en_intento") % i)
                time.sleep(0.5)
            else:
                sesion.logger.debug(_("guardo_en_intento") % i)
                positivo = True
                break
        return positivo

    def _lee_tag(self):
        """ Función para obtener un tag y devolver sus datos o vacío """
        tag = self._get_tag()
        try:
            datos = tag['datos']
        except:
            datos = ''
        return datos
