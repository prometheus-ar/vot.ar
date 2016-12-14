"""Rampa del modulo Menu."""
from msa.core.rfid.constants import (TAG_APERTURA, TAG_DATOS,
                                     TAG_PRESIDENTE_MESA, TAG_USUARIO_MSA)
from msa.modulos.base.rampa import RampaBase, semaforo


class Rampa(RampaBase):

    """La Rampa especializada para el modulo de administracion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.tiene_papel:
            self.expulsar_boleta()

    def registrar_eventos(self):
        """Registra los eventos."""
        lector = self.sesion.lector
        if lector is not None:
            self._ev_lector = lector.consultar_lector(self._cambio_tag)
        imp = self.sesion.impresora
        if imp is not None:
            self._ev_sensor_1 = imp.registrar_insertando_papel(
                self.cambio_sensor_1)
            self._ev_sensor_2 = imp.registrar_autofeed_end(
                self.cambio_sensor_2)

    def desregistrar_eventos(self):
        """desegistra los eventos por default de la rampa."""
        if self.sesion.lector is not None:
            self.sesion.lector.remover_consultar_lector()
        if self.sesion.impresora is not None:
            self.sesion.impresora.remover_insertando_papel()
            self.remover_nuevo_papel()

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        boton_mantenimiento = self.modulo.boton_mantenimiento
        timer = self.modulo.controlador.timer

        if (tag_dict is not None and tag_dict['tipo'] == TAG_USUARIO_MSA and
            timer is not None):
            if boton_mantenimiento:
                self.modulo._calibrar_pantalla()
            else:
                self.modulo._show_maintenance_button()
        elif (tag_dict is not None and tag_dict['tipo'] == TAG_PRESIDENTE_MESA
              and timer is None):
            self.modulo.controlador.cargar_botones(self.modulo.mesa_abierta)
        elif not self.modulo.mesa_abierta and tipo_tag == TAG_DATOS and \
                tag_dict['tipo'] == TAG_APERTURA:
            datos_tag = tag_dict['datos']
            self.modulo._configurar_mesa(datos_tag)
        else:
            if self.tiene_papel:
                self.expulsar_boleta()
