"""Rampa del modulo mantenimiento."""
from msa.modulos import get_sesion
from msa.modulos.base.rampa import RampaBase, semaforo


sesion = get_sesion()


class Rampa(RampaBase):

    """La Rampa especializada para el modulo de administracion."""

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        pass

    def registrar_eventos(self):
        """Registra los eventos por default de la rampa."""
        imp = sesion.impresora
        lector = sesion.lector

        if lector is not None:
            self._ev_lector = lector.consultar_lector(self._cambio_tag)
        if imp is not None:
            self._ev_sensor_1 = imp.registrar_insertando_papel(
                self.cambio_sensor_1)
            self._ev_sensor_2 = imp.registrar_autofeed_end(
                self.cambio_sensor_2)

        if hasattr(sesion, "powermanager"):
            pwr_mgr = sesion.powermanager

            self.signal_ac = pwr_mgr.check_ac(self.modulo._recheck_batteries)
            self.signal_batt_discharging = pwr_mgr.check_battery_discharging(
                self.modulo._recheck_batteries)
            self.signal_batt_plugged = pwr_mgr.check_battery_plugged(
                self.modulo._recheck_batteries)
            self.signal_batt_unplugged = pwr_mgr.check_battery_unplugged(
                self.modulo._recheck_batteries)

        if hasattr(sesion, "pir"):
            pir = sesion.pir
            self.signal_pir_detected = pir.check_detected(
                self.modulo._recheck_pir_detected)
            self.signal_pir_not_detected = pir.check_not_detected(
                self.modulo._recheck_pir_not_detected)

    def desregistrar_eventos(self):
        """desegistra los eventos por default de la rampa."""
        if sesion.lector is not None:
            sesion.lector.remover_consultar_lector()
        if sesion.impresora is not None:
            sesion.impresora.remover_insertando_papel()
            self.remover_nuevo_papel()
        if hasattr(self, "signal_ac") and self.signal_ac is not None:
            self.signal_ac.remove()
        if hasattr(self, "signal_batt_discharging") and \
                self.signal_batt_discharging is not None:
            self.signal_batt_discharging.remove()
        if hasattr(self, "signal_batt_plugged") and \
                self.signal_batt_plugged is not None:
            self.signal_batt_plugged.remove()
        if hasattr(self, "signal_batt_unplugged") and \
                self.signal_batt_unplugged is not None:
            self.signal_batt_unplugged.remove()
        if hasattr(self, "signal_pir_detected") and \
                self.signal_pir_detected is not None:
            self.signal_pir_detected.remove()
        if hasattr(self, "signal_pir_not_detected") and \
                self.signal_pir_not_detected is not None:
            self.signal_pir_not_detected.remove()

        if hasattr(sesion, "powermanager"):
            pwr_mgr = sesion.powermanager
            pwr_mgr.uncheck_ac()
            pwr_mgr.uncheck_battery_discharging()
            pwr_mgr.uncheck_battery_plugged()
            pwr_mgr.uncheck_battery_unplugged()
        if hasattr(sesion, "pir"):
            sesion.pir.uncheck_detected()
            sesion.pir.uncheck_not_detected()

    def cambio_tag(self, tipo_tag, tag_dict):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- los datos del tag
        """
        self.modulo.rfid_check(tag_dict)
