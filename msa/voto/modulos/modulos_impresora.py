# -*- coding: utf-8 -*-
"""Un modulo de prueba de impresion.

Hereda de Modulo (definido en modulos.py)

Imiprime una hoja de prueba, muestra un mensaje y sale, volviendo al modulo
administrador.
"""
import pygtk
import gtk
import gobject

pygtk.require('2.0')

from msa.voto.constants import MODULO_ADMIN, DEFAULT_FONT
from msa.voto.gui.clasesgui import Panel
from msa.voto.modulos import Modulo
from msa.voto.sesion import get_sesion


sesion = get_sesion()


class ModuloOperacionImpresora(Modulo):

    """ Permite Mostrar un pequeño mensaje mientras se hace
        una operación con una impresora, llamado desde el módulo
        administracion. Está hecho para ser
        reutilizado por clases hijas, y no ser instanciado.
    """

    def __init__(self, mensaje):
        Modulo.__init__(self)
        self.ret_code = MODULO_ADMIN

        lbl = gtk.Label()
        lbl.set_markup(_("formato_titulo") % mensaje)
        lbl.modify_font(DEFAULT_FONT)
        panel = Panel()
        panel.add(lbl)
        self.set_pantalla(panel)


class ModuloPruebaImpresion(ModuloOperacionImpresora):

    """Imprime una pagina de prueba y sale"""

    def __init__(self):
        ModuloOperacionImpresora.__init__(self, _("impr_pag_prueba"))

    def main(self):
        #sesion.reiniciar_impresora()
        # Lo comenté porque estoy casi seguro de que no funciona.
        # TODO: Implementar esto.
        sesion.impresora.imprimir_prueba()

        gobject.timeout_add(5000, self.quit)
        return Modulo.main(self)


class ModuloExpulsarBoleta(ModuloOperacionImpresora):

    """ Permite hacer operaciones sobre la impresora directamente """

    def __init__(self):
        ModuloOperacionImpresora.__init__(self, _("expulsando_boleta"))

    def main(self):
        #sesion.reiniciar_impresora()
        gobject.timeout_add(3000, self.quit)
        sesion.impresora.expulsar_boleta()
        return Modulo.main(self)
