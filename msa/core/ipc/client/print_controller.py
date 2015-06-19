# coding: utf-8
import dbus

from base64 import b64encode
from json import loads
from tempfile import NamedTemporaryFile

from msa import get_logger
from msa.core.settings import DBUS_BUSNAME_PRINTER, DBUS_IMPRESORA_PATH, \
        COMPRESION_IMPRESION, USA_ARMVE
from msa.core.imaging import get_dpi_boletas


logger = get_logger("dbus_client")


class DbusPrintController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.printer = self._get_printer()
        self.tiene_papel = self._estado_inicial_tarjeta()
        self._callback_tarjeta = None
        self._signal_paper = self.registrar_estado_papel()
        self._signal_insertando = None
        self._signal_autofeed = None
        self._callback_expulsada = None

        self.printer.connect_to_signal("boleta_expulsada",
                                       self.boleta_expulsada)

    def _get_printer(self):
        return self.bus.get_object(DBUS_BUSNAME_PRINTER,
                                   DBUS_IMPRESORA_PATH)

    def imprimiendo(self):
        dbus_method = self.printer.get_dbus_method('imprimiendo')
        response = dbus_method()
        return response

    def do_print(self):
        dbus_method = self.printer.get_dbus_method('do_print')
        return dbus_method()

    def _estado_inicial_tarjeta(self):
        dbus_method = self.printer.get_dbus_method('tarjeta_ingresada')
        return dbus_method()

    def full_paper_status(self):
        dbus_method = self.printer.get_dbus_method('full_paper_status')
        data = dbus_method()
        if data is not None and 'paper_out_1' in data:
            self.tiene_papel = data['paper_out_1']
        return data

    def tarjeta_ingresada(self):
        return self.tiene_papel

    def expulsar_boleta(self):
        try:
            dbus_method = self.printer.get_dbus_method('expulsar_boleta')
        except dbus.exceptions.DBusException:
            pass
        dbus_method()

        self.tiene_papel = False

    def tarjeta_sin_retirar(self):
        dbus_method = self.printer.get_dbus_method('tarjeta_sin_retirar')
        return dbus_method()

    def posicionar_al_inicio(self):
        if not USA_ARMVE:
            dbus_method = self.printer.get_dbus_method('posicionar_al_inicio')
            return dbus_method()

    def tomar_tarjeta(self, loops=False):
        dbus_method = self.printer.get_dbus_method('tomar_tarjeta')
        return dbus_method(loops)

    def imprimir_image(self, image, dpi=get_dpi_boletas(), transpose=False,
                       compress=COMPRESION_IMPRESION, only_buffer=False):
        image_file = NamedTemporaryFile(prefix="imagen_impresion", dir="/tmp",
                                        bufsize=0, delete=False)
        data = image.tostring()
        image_file.write(data)
        image_file.flush()
        filepath = image_file.name
        mode = image.mode
        size = image.size

        dbus_method = self.printer.get_dbus_method('imprimir_image')
        return dbus_method(filepath, mode, size, dpi, transpose, compress,
                           only_buffer)

    def imprimir_serializado(self, tipo_tag, tag, transpose=False,
                             only_buffer=False, extra_data=None):
        if extra_data is None:
            extra_data = "[]"
        dbus_method = self.printer.get_dbus_method('imprimir_serializado')
        return dbus_method(tipo_tag, tag, transpose, only_buffer, extra_data)

    def registrar(self, seleccion):
        dbus_method = self.printer.get_dbus_method('registrar')
        tag = b64encode(seleccion.a_tag())
        return loads(dbus_method(tag))

    def limpiar_cola(self):
        dbus_method = self.printer.get_dbus_method('limpiar_cola')
        return dbus_method()

    def backfeed(self, lines):
        dbus_method = self.printer.get_dbus_method('backfeed')
        return dbus_method(lines)

    def linefeed(self, lines):
        dbus_method = self.printer.get_dbus_method('linefeed')
        return dbus_method(lines)

    def consultar_tarjeta(self, funcion):
        self._callback_tarjeta = funcion

    def registar_boleta_expulsada(self, funcion):
        self._callback_expulsada = funcion

    def boleta_expulsada(self):
        if self._callback_expulsada is not None:
            self._callback_expulsada()

    def remover_boleta_expulsada(self):
        self._callback_expulsada = None

    def registrar_estado_papel(self):
        self._signal_paper = self.printer.connect_to_signal("con_tarjeta",
            self.cambiar_estado_papel)
        return self._signal_paper

    def cambiar_estado_papel(self, estado):
        #logger.debug("recibiendo signal cambio estado de papel")
        self.tiene_papel = estado
        if self._callback_tarjeta is not None:
            self._callback_tarjeta(estado)

    def remover_consultar_tarjeta(self):
        self._callback_tarjeta = None

    def remover_estado_papel(self):
        if self._signal_paper is not None:
            self._signal_paper.remove()
            self._signal_paper = None

    def registrar_insertando_papel(self, callback):
        def _inner(data):
            if data is not None and 'paper_out_1' in data:
                self.tiene_papel = data['paper_out_1']
            return callback(data)
        self._signal_insertando = self.printer.connect_to_signal(
            "insertando_papel", _inner)

    def remover_insertando_papel(self):
        if self._signal_insertando is not None:
            self._signal_insertando.remove()
            self._signal_insertando = None

    def registrar_autofeed_end(self, callback):
        def _inner(data):
            if data is not None and 'paper_out_1' in data:
                self.tiene_papel = data['paper_out_1']
            return callback(data)
        self._signal_autofeed = self.printer.connect_to_signal(
            "autofeed_end", _inner)

    def remover_autofeed_end(self):
        if self._signal_autofeed is not None:
            self._signal_autofeed.remove()
            self._signal_autofeed = None

    def insertar_boleta(self, estado):
        dbus_method = self.printer.get_dbus_method('insertar_boleta')
        return dbus_method(estado)

    def get_autofeed_mode(self):
        dbus_method = self.printer.get_dbus_method('get_autofeed_mode')
        return dbus_method()

    def set_autofeed_mode(self, mode):
        dbus_method = self.printer.get_dbus_method('set_autofeed_mode')
        return dbus_method(mode)

    def connection(self, funcion):
        return self.printer.connect_to_signal('connection', funcion)

    def estado(self):
        dbus_method = self.printer.get_dbus_method('estado')
        return dbus_method()

    def get_quality(self):
        dbus_method = self.printer.get_dbus_method('get_quality')
        return dbus_method()

    def set_quality(self, level):
        dbus_method = self.printer.get_dbus_method('set_quality')
        return dbus_method(level)

    def quit(self):
        quit_method = self.printer.get_dbus_method('quit')
        return quit_method()
