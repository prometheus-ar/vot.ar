"""
Modulo base de las rampas.

maneja la interaccion entre la impresora y el lector y el usuario.
"""
from gi.repository.GLib import timeout_add

from msa.core.armve.constants import DEV_PRINTER
from msa.core.exceptions import MesaNoEncontrada
from msa.core.rfid.constants import (TAG_ADMIN, TAG_APERTURA, TAG_COLISION,
                                     TAG_PRESIDENTE_MESA, TAG_RECUENTO,
                                     TAG_USUARIO_MSA, TAG_VACIO, TAG_VOTO)
from msa.modulos import get_sesion
from msa.modulos.base.decorators import semaforo, si_tiene_conexion
from msa.modulos.constants import (E_CARGA, E_CONFIRMACION, E_INICIAL,
                                   E_REGISTRANDO, E_SETUP,
                                   SUBMODULO_DATOS_ESCRUTINIO)


class RampaBase(object):

    """Rampa generica de la que heredan el resto de las rampas.

    Esta clase se encarga de manejar los estados de papel en la impresora y el
    estado de los chips.
    """

    def __init__(self, modulo):
        """Constructor de la clase de manejo de rampa.

        Argumentos:
            modulo -- referencia al modulo que maneja la rampa.
        """
        self.modulo = modulo
        self.sesion = get_sesion()

        self._servicio = self.sesion._servicio
        self.tiene_conexion = self._servicio is not None

        if self.tiene_conexion:
            # reseteamos el RFID por precaución cada vez que arrancamos una
            # rampa nueva
            self.sesion.logger.debug("Iniciando rampa...")
            self.reset_rfid()
            # ojo que esto no verifica correctamente que tenga papel, no puedo
            # saber si está viendo el sensor solamente o ademas el papel esta
            # tomado, pero este conocimiento es mejor que nada.
            self.tiene_papel = self._servicio.tiene_papel
            self.tag_leido = self._servicio.get_tag()
        else:
            self.tiene_papel = False
            self.tag_leido = None

        self.desregistrar_eventos()
        self.registrar_eventos()


    def maestro(self):
        pass

    def cambio_sensor_1(self, data):
        """Callback que se corre cuando el sensor 1 se dispara.

        El evento que nos interesa es el que manda False en el sensor_1
        ya que nos dice que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['sensor_1']

        if not sensor_1:
            self.tiene_papel = False
            self.maestro()

    def cambio_sensor_2(self, data):
        """
        Callback que se corre cuando el sensor 2 se dispara.

        El evento que nos interesa es el que manda "0" ya que nos dice
        que el papel ya esta listo para leer el chip.
        """
        sensor_1 = data['sensor_1']
        sensor_2 = data['sensor_2']

        if not sensor_2 and sensor_1:
            self.tiene_papel = True
            self.maestro()

    def _cambio_tag(self, tipo_lectura, tag=None):
        """
        Esto es un filtro que formatea el tag para que sea un diccionario y
        hace el base 64 decoding.

        Argumentos:
            tipo_lectura -- el tipo de lectura.
            tag -- una instancia de SoporteDigital
        """
        valido = True

        if tag is not None and tag.tipo in (TAG_PRESIDENTE_MESA,
                                            TAG_USUARIO_MSA):
            valido = tag.verificar_firma_credencial()

        if valido:
            return self.cambio_tag(tipo_lectura, tag)
        else:
            self.sesion.logger.info("Falló la verificación de la firma.")

    def cambio_tag(self, tipo_lectura, tag):
        """ Callback de cambio de tag.

        Argumentos:
            tipo_tag -- el tipo de tag
            tag_dict -- un diccionario con los datos del tag
        """
        if tipo_lectura == TAG_COLISION:
            self.modulo.pantalla_insercion()
            self.tag_colision()
        elif tipo_lectura == TAG_ADMIN:
            self.tag_admin(tag)
        else:
            if tag != self.tag_leido:
                self.tag_leido = tag
                self.maestro()

    def tag_colision(self):
        """Metodo que se llama cuando se detecta colision."""
        self.expulsar_boleta("colision")

    def expulsar_boleta(self, motivo=""):
        """Metodo de expulsion de boleta."""
        self.sesion.logger.debug("EXPULSION dese modulo rampa (%s)", motivo)
        self.tiene_papel = False
        self.tag_leido = None
        if self.tiene_conexion:
            self._servicio.expulsar_boleta()

    def tag_admin(self, tag=None):
        """Metodo que se llama cuando se apoya un tag de admin."""
        self.desregistrar_eventos()
        if self.tiene_papel:
            self.expulsar_boleta("tag_admin")
        self.modulo.salir()

    def registrar_eventos(self):
        """Registra los eventos por default de la rampa."""
        self.registrar_default_lector()
        self.registrar_default_sensor_1()
        self.registrar_default_sensor_2()

    def desregistrar_eventos(self):
        """Desregistra los eventos por default de la rampa."""
        self.remover_consultar_lector()
        self.remover_insertando_papel()
        self.remover_nuevo_papel()

    @si_tiene_conexion
    def registrar_error_impresion(self, callback):
        self._servicio.registrar_error_impresion(callback)

    @si_tiene_conexion
    def remover_error_impresion(self):
        self._servicio.remover_error_impresion()

    @si_tiene_conexion
    def registrar_fin_impresion(self, callback):
        self._servicio.registrar_fin_impresion(callback)

    @si_tiene_conexion
    def remover_fin_impresion(self):
        self._servicio.remover_fin_impresion()

    @si_tiene_conexion
    def registrar_default_lector(self):
        self._servicio.consultar_lector(self._cambio_tag)

    @si_tiene_conexion
    def remover_consultar_lector(self):
        self._servicio.remover_consultar_lector()

    def registrar_default_sensor_1(self):
        self.registrar_insertando_papel(self.cambio_sensor_1)

    def registrar_default_sensor_2(self):
        self.registrar_nuevo_papel(self.cambio_sensor_2)

    @si_tiene_conexion
    def registrar_nuevo_papel(self, callback):
        """Registra el evento de nuevo papel."""
        self._servicio.registrar_autofeed_end(callback)

    @si_tiene_conexion
    def consultar_tarjeta(self, callback):
        """Registra el evento de nuevo papel."""
        self._servicio.consultar_tarjeta(callback)

    @si_tiene_conexion
    def remover_consultar_tarjeta(self):
        """Remueve el evento de nuevo papel."""
        self._servicio.remover_consultar_tarjeta()

    @si_tiene_conexion
    def remover_nuevo_papel(self):
        """Remueve el evento de nuevo papel."""
        self._servicio.remover_autofeed_end()

    @si_tiene_conexion
    def remover_insertando_papel(self):
        self._servicio.remover_insertando_papel()

    @si_tiene_conexion
    def registrar_insertando_papel(self, callback):
        self._servicio.registrar_insertando_papel(callback)

    def registrar_boleta_expulsada(self, callback):
        self._servicio.registrar_boleta_expulsada(callback)

    def remover_boleta_expulsada(self):
        self._servicio.remover_boleta_expulsada()

    def get_tag(self):
        self.tag_leido = self._servicio.get_tag()
        return self.tag_leido

    def get_tag_async(self, callback):

        def _inner(data):
            tag = self._servicio._parse_tag(data)
            self.tag_leido = tag
            callback(tag)

        self._servicio.async("read", _inner)

    def guardar_tag(self, tipo_tag, datos, quema):
        return self._servicio.guardar_tag(tipo_tag, datos, quema)

    def guardar_tag_async(self, callback, tipo_tag, datos, quema):
        return self._servicio.guardar_tag_async(callback, tipo_tag, datos,
                                                quema)

    @si_tiene_conexion
    def reset_rfid(self):
        self._servicio.reset_rfid()

    @si_tiene_conexion
    def reset_printer(self):
        self._servicio.reset(DEV_PRINTER)

    def imprimir_serializado(self, tipo_tag, tag, transpose=False,
                             only_buffer=False, extra_data=None):
        self._servicio.imprimir_serializado(tipo_tag, tag, transpose=transpose,
                                      only_buffer=only_buffer,
                                      extra_data=extra_data)

    def get_arm_version(self):
        return self._servicio.get_arm_version()

    def get_arm_build(self):
        return self._servicio.get_arm_build()

    def get_antenna_level(self):
        return self._servicio.get_antenna_level()

    def get_brightness(self):
        return self._servicio.get_brightness()

    def set_brightness(self, value):
        return self._servicio.set_brightness(value)

    def get_fan_mode(self):
        return self._servicio.get_fan_mode()

    def set_fan_mode(self, value):
        return self._servicio.set_fan_mode(value)

    def get_fan_speed(self):
        return self._servicio.get_fan_speed()

    def set_fan_speed(self, value):
        return self._servicio.set_fan_speed(value)

    def reset(self, device):
        return self._servicio.reset(device)

    def get_autofeed_mode(self):
        return self._servicio.get_autofeed_mode()

    def set_autofeed_mode(self, value):
        return self._servicio.set_autofeed_mode(value)

    def get_printer_quality(self):
        return self._servicio.get_printer_quality()

    def set_printer_quality(self, value):
        return self._servicio.set_printer_quality(value)

    @si_tiene_conexion
    def registrar_reset_device(self, callback):
        self._servicio.registrar_reset_device(callback)

    @si_tiene_conexion
    def remover_reset_device(self):
        self._servicio.remover_reset_device()

    @si_tiene_conexion
    def registrar_ac(self, callback):
        self._servicio.registrar_ac(callback)

    @si_tiene_conexion
    def registrar_battery_discharging(self, callback):
        self._servicio.registrar_battery_discharging(callback)

    @si_tiene_conexion
    def registrar_battery_plugged(self, callback):
        self._servicio.registrar_battery_plugged(callback)

    @si_tiene_conexion
    def registrar_battery_unplugged(self, callback):
        self._servicio.registrar_battery_unplugged(callback)

    @si_tiene_conexion
    def registrar_pir_detected(self, callback):
        self._servicio.registrar_pir_detected(callback)

    @si_tiene_conexion
    def registrar_pir_not_detected(self, callback):
        self._servicio.registrar_pir_not_detected(callback)

    @si_tiene_conexion
    def remover_ac(self):
        self._servicio.remover_ac()

    @si_tiene_conexion
    def remover_battery_discharging(self):
        self._servicio.remover_battery_discharging()

    @si_tiene_conexion
    def remover_battery_plugged(self):
        self._servicio.remover_battery_plugged()

    @si_tiene_conexion
    def remover_battery_unplugged(self):
        self._servicio.remover_battery_unplugged()

    @si_tiene_conexion
    def remover_pir_detected(self):
        self._servicio.remover_pir_detected()

    @si_tiene_conexion
    def remover_pir_not_detected(self):
        self._servicio.remover_pir_not_detected()

    def get_power_source(self):
        return self._servicio.get_power_source()

    def get_power_status(self):
        return self._servicio.get_power_status()

    def get_pir_status(self):
        return self._servicio.get_pir_status()

    def get_pir_mode(self):
        return self._servicio.get_pir_mode()


class RampaActas(RampaBase):

    """
    Rampa generica para el modulo de apertura y el cierre ya que ambos usan el
    controlador de interacion y manejan de una manera similar la toma de papel.
    """

    @semaforo
    def maestro(self):
        """El maestro de ceremonias, el que dice que se hace y que no."""
        if self.tag_leido is not None \
                and (self.tag_leido.tipo in (TAG_RECUENTO, TAG_VOTO,
                                             TAG_VACIO, TAG_APERTURA)):
            try:
                self.procesar_tag(self.tag_leido)
            except MesaNoEncontrada:
                self.expulsar_boleta("mesa_no_encontrada")
        elif self.modulo.estado in (E_CARGA, E_CONFIRMACION, E_SETUP):
            if self.modulo.nombre != SUBMODULO_DATOS_ESCRUTINIO:
                self.modulo.reiniciar_modulo()
            else:
                self.expulsar_boleta("submodulo_datos_escrutinio")
        elif self.modulo.estado == E_INICIAL and self.tiene_papel and \
                self.tag_leido is None:
            def _expulsar():
                if self.tiene_papel and self.tag_leido is None:
                    self.expulsar_boleta("inicial")
            timeout_add(1000, _expulsar)
        elif self.modulo.estado != E_REGISTRANDO:
            self.modulo.mensaje_inicial()
