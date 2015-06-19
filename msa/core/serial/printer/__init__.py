# -*- coding: utf-8 -*-
""" Este modulo implementa los controladores para las distintas impresoras. """

import itertools
import serial
import time
import os
import platform

from PIL import Image

from msa import get_logger
from msa.core.helpers import detect_printer_port
from msa.core.settings import COMPRESION_IMPRESION, USB_PRINTER_PRODUCT_ID, \
    USB_PRINTER_VENDOR_ID, USAR_CYTHON, IMPRESION_USBLP
from msa.core.imaging import get_dpi_boletas
from msa.core.constants import DPI_VOTO_BAJA, DPI_VOTO_ALTA, \
    DEBUG_IMPRESION_TEST_FILE

_usb_printer = False
logger = get_logger("impresion")


if IMPRESION_USBLP:
    try:
        import usb.core
        _usb_printer = IMPRESION_USBLP
    except ImportError:
        pass


def obtener_impresora():
    """Devuelve una clase que sabe manejar la impresora conectada."""
    if _usb_printer:
        try:
            impresora = CustomTPTUSB()
            logger.info('Usando Impresora Serial')
        except RuntimeError:
            logger.info('No se detecto impresora USB. Usando impresora Serial')
            impresora = CustomTPTSerial()
    else:
        logger.info('Usando Impresora Serial')
        impresora = CustomTPTSerial()

    return impresora


class Buffer(object):

    """Buffer interno para trasponer."""

    def __init__(self):
        self.buf = {}

    def __setitem__(self, pos, value):
        self.buf[(pos.start, pos.stop)] = value

    def __getitem__(self, pos):
        if (pos.start, pos.stop) in self.buf:
            return self.buf[(pos.start, pos.stop)]
        else:
            return " ",  []


class Printer(object):

    """ Clase que permite el acceso a una impresorar. """

    def __init__(self, bps=None, vendor=None):
        self._isprinting = False
        self._isopen = False
        self.vendor = vendor
        self.bps = bps

    def get_vendor(self):
        return self.vendor

    def is_open(self):
        return self._isopen

    def imprimiendo(self):
        return self._isprinting

    # =======================================================================
    # To Override
    # =======================================================================

    def initialize(self):
        raise NotImplementedError

    def open(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def write(self, value):
        raise NotImplementedError

    def read(self, count):
        raise NotImplementedError

    def flush(self):
        raise NotImplementedError

    def linefeed(self, n=1):
        raise NotImplementedError

    def backfeed(self, n=1):
        raise NotImplementedError

    def expulsar_boleta(self):
        raise NotImplementedError

    def tomar_tarjeta(self, loops=None):
        raise NotImplementedError

    def posicionar_al_inicio(self):
        raise NotImplementedError

    def limpiar_cola(self):
        raise NotImplementedError

    def imprimir_image(self, image, dpi=get_dpi_boletas(), transpose=False,
                       compress=COMPRESION_IMPRESION, only_buffer=False):
        raise NotImplementedError

    def do_print(self):
        raise NotImplementedError

    def simular_impresion(self):
        raise NotImplementedError

    # Methods related to printer status

    def tarjeta_ingresada(self):
        raise NotImplementedError

    def tarjeta_sin_retirar(self):
        raise NotImplementedError


class CustomTPT(Printer):

    ESC = '\x1b'
    LF = '\n'
    FF = LF * 100

    # Printer types
    USB = 'usb'
    SERIAL = 'serial'
    DUMMY = 'dummy'

    def __init__(self, _type):
        Printer.__init__(self, vendor='CustomTPT')
        self._type = _type

    def __get_state_values(self):
        estados = {}
        if self.is_dummy():
            return estados

        try:
            self.flush()
        except Exception:
            self.initialize()

        self.write('\x10\x04\x14')

        # TODO: Cuanto debo leer???
        ret = self.read(18)

        # TODO: Depuración
        if ret[2:3]:
            bytes = ord(ret[2:3])
            estados['without_paper'] = bool(bytes & 0x01)
            estados['near_paper_end'] = bool(bytes & 0x04)
            estados['ticket_out'] = bool(bytes & 0x20)
        return estados

    # Debe ser reescrito con la inicialización necesaria para la clase hija
    def prepare(self):
        raise NotImplementedError

    def initialize(self):
        self.prepare()
        try:
            self.write(self.ESC + '@')
            self.write('\x18')
        except:
            pass

    def linefeed(self, n=1):
        self.write(self.LF * n)

    def backfeed(self, n=1):
        self.write('\x1D\xF9' + ('%02x' % n).decode('hex'))

    def expulsar_boleta(self):
        self.write("\x1D\xF8")

    def tomar_tarjeta(self, loops=None):
        # TODO: Depuración
        logger.debug("Tomando tarjeta")

        if self.is_dummy():
            self.write(self.LF * 20)
            return

        continuo = loops is None
        while loops or continuo:
            if self.tarjeta_ingresada():
                self.write(self.LF * 20)
                break
            if not continuo:
                loops -= 1

    def posicionar_al_inicio(self):
        # TODO: Depuración
        #sesion.logger.debug("Moviendo la tarjeta a la posición inicial")
        if self.tarjeta_ingresada():
            self.write('\x1d\xf7')

    def limpiar_cola(self):
        self.initialize()

    def imprimir_image(self, image, dpi=get_dpi_boletas(), transpose=False,
                       compress=COMPRESION_IMPRESION, only_buffer=False):
        """Decide el metodo de impresion segun las settings y en caso de que
        sea necesario prepara la imagen.
        """
        if USAR_CYTHON:
            if transpose:
                image = image.transpose(Image.ROTATE_270)
            self.imprimir_image_fast(image, only_buffer=only_buffer)
        else:
            self.imprimir_image_slow(image, dpi, transpose, compress,
                                     only_buffer)

    def imprimir_image_slow(self, image, dpi=get_dpi_boletas(),
                            transpose=False, compress=COMPRESION_IMPRESION,
                            only_buffer=False):
        """Imprime la imagen en velocidad lenta."""
        self._isprinting = True

        #borro la data
        self.write('\x18')

        # des-activo modo comprimido en baja calidad (para pruebas)
        if compress and dpi != DPI_VOTO_ALTA:
            compress = False

        t0 = time.time() # tiempo inicial

        im = image
        if im.mode != "1":
            logger.debug("Convirtiendo a B/N...")
            im = im.convert("1")              # convertir B/W (1 bit)

        t1 = time.time()# tiempo apertura/conversion

        if transpose:
            logger.debug("Rotando 270º (apaisado)...")
            im = im.transpose(Image.ROTATE_270)     # landscape
        if dpi == (67, 67):
            logger.debug("Ajustando aspecto a 100x67 dpi (redimensionando)...")
            logger.debug("Tamaño anterior: %s" % im.size)
            im = im.resize((im.size[0] * 100 / 67, im.size[1]))# aspecto ratio
            dpi = DPI_VOTO_BAJA
            logger.debug("Tamaño actual: %s" % im.size)

        # bit verticales (manual pp. 28 "Select image mode")
        if dpi == DPI_VOTO_BAJA:
            v = 8   # (baja calidad)
        elif dpi == DPI_VOTO_ALTA:
            v = 24  # (alta calidad)
        else:
            # 67x200 y 200x100 DPI se complica armar el bitmap
            raise RuntimeError("Calidad de impresión requerida no soportada: %s"
                                % str(dpi))

        buf = []
        t2 = time.time()
        logger.debug("Iniciando buffering: %s" % t2)
        # recorro pixels, armo buffer de bits para enviar a la impresora
        # obtengo los datos internos de PIL para optimizar (en vez de getpixel)
        data = list(im.getdata())
        xmax = im.size[0]
        if not compress:
            # buferring sin compresión: recorre de arriba a abajo, izq a der
            #   en baja: transpone 8 pixeles verticales (1 byte)
            #   en alta: transpone 24 pixeles verticales (3 bytes)
            for y in range(0, im.size[1], v):
                d = []
                for x in range(im.size[0]):
                    for k in range(0, v / 8):
                        b = 0
                        for j in range(0, 8):
                            try:
                                b = b | ((0 if data[(x + (y + j + 8 * k) * xmax)] else 1) << (7 - j))
                            except IndexError:
                                # ultimo boundary != 8bits! (completar con blancos)
                                #logger.debug("IndexError: alto debe ser múltiplo de 8 bits")
                                pass
                        d.append(chr(b))
                buf.append(d)
        else:
            # buffering para compresion: recorre de arriba a abjo, izq a der
            #   en alta: empaqueta de a 8 pixeles horizontales (1 byte)
            for y in range(0, im.size[1]):
                d = ""
                for x in range(0, im.size[0], 8):
                    b = 0
                    i0 = x + y * xmax
                    # optimización para bajar 50% el tiempo de buffering:
                    try:
                        if not data[i0 + 0]: b += 128
                        if not data[i0 + 1]: b += 64
                        if not data[i0 + 2]: b += 32
                        if not data[i0 + 3]: b += 16
                        if not data[i0 + 4]: b += 8
                        if not data[i0 + 5]: b += 4
                        if not data[i0 + 6]: b += 2
                        if not data[i0 + 7]: b += 1
                        d += chr(b)
                    except IndexError:
                        pass
                buf.append(d)
        t3 = time.time()
        logger.debug("Inicio impresion: %s" % t3)
        if not only_buffer:
            self.write("\x1D\xF9\x04") # return 4 lines

        if compress:
            # sets the page lenght in dots
            self.write("\x1b\xa5\x6c%s\x50" % 100)#im.size[1])
            # Enable data compression ("Graphics Advanced Mode Commands" p19)
            self.write("\x1b\xa5\x62\x31\x4d")
            # Set absolute positioning on the x axis (origin)
            self.write("\x1b\xa5\x70%s\x58" % 0)
            # Set absolute positioning on the y axis (origin)
            self.write("\x1b\xa5\x70%s\x59" % 0)
        # recorro buffer de bits, armo bytes y envio a la impresora:
        # TODO: optimizar con struct o similar?
        saved = 0
        for li, d in enumerate(buf):
            if not compress:
                m = v == 8 and '\x00' or '\x21' # 24 dot double density (200DPI)
                n = len(d)/(v/8)
                #logger.debug("line %s length %s" % (li, n))
                self.write("\x1b\x2A%s%s%s" % (m, ("%04x" % n).decode("hex")[::-1], ''.join(d)))
                self.write("\x0a\x0d")
            else:
                cant_bytes = len(d)
                ##assert 0 <= cant_byte <= 110 # máximo 1 bit por pixel
                # Receive graphic data ("Graphics Advanced Mode Commands" p20)
                self.write("\x1b\xa5\x62%s\x57" % cant_bytes)
                buf = ''
                for char, group in itertools.groupby(d):
                    group_len = len(list(group))
                    if char < '\xc0' and group_len == 1:
                        # envio el caracter sin comprimir
                        buf += char
                    else:
                        # comprimo por RLE en hasta 63 repeticiones por vez
                        while group_len:
                            if group_len > 63:
                                multiplication_factor = 63
                            else:
                                multiplication_factor = group_len
                            saved = saved + multiplication_factor - 1
                            # envio cantidad de repeticiones y caracter:
                            buf += chr(0xc0 + multiplication_factor) + char
                            group_len -= multiplication_factor
                self.write(buf)

        if compress and not only_buffer:
            self.do_print()

        logger.debug("compressed, bytes saved: %s" % saved)

        t4 = time.time()
        logger.info("Fin impresion: %s" % t4)
        logger.info("Total apertura: %s" % (t1 - t0))
        logger.info("Total tranform: %s" % (t2 - t1))
        logger.info("Total buffering: %s" % (t3 - t2))
        logger.info("Total impresion: %s" % (t4 - t3))
        logger.info("Total general: %s" % (t4 - t0))
        # expulso la hoja:
        if not only_buffer:
            self.expulsar_boleta()

            if self.is_dummy():
                im.save("customtpt-dummy.png", "PNG")
                os.system("eog customtpt-dummy.png")
        self._isprinting = False

    def imprimir_image_fast(self, im, only_buffer=False):
        if platform.architecture()[0] == "64bit":
            from msa.core.printer.x86_64.impresion_cython \
                import imprimir_image_fast as iif
        else:
            from msa.core.printer.i686.impresion_cython \
                import imprimir_image_fast as iif

        logger.debug("IMPRIMIENDO RAPIDO")
        t0 = time.time() # tiempo inicial

        self.write('\x18')              # borro la data

        # sets the page lenght in dots
        self.write("\x1b\xa5\x6c%s\x50" % 100)# im.size[1])
        # Enable data compression ("Graphics Advanced Mode Commands" p19)
        self.write("\x1b\xa5\x62\x31\x4d")
        # Set absolute positioning on the x axis (origin)
        self.write("\x1b\xa5\x70%s\x58" % 0)
        # Set absolute positioning on the y axis (origin)
        self.write("\x1b\xa5\x70%s\x59" % 0)

        iif(self, im)

        t4 = time.time()
        logger.debug("Total general FAST: %s" % (t4 - t0))

        # expulso la hoja:
        if not only_buffer:
            self.do_print()
            self.expulsar_boleta()

    def do_print(self):
        # Mover 4 espacios para atras
        self.write("\x1D\xF9\x04")
        # Disable data compression ("Graphics Advanced Mode Commands" p19)
        self.write("\x1b\xa5\x62\x30\x4d")
        # Print the entire graphics page with all its contents
        self.write("\x1b\xa5\x72\x30")
        self.write('\x18')

    def simular_impresion(self):
        self.initialize()
        self.write(self.FF)

    def tarjeta_ingresada(self):
        without_paper = self.__get_state_values().get('without_paper', None)
        return without_paper if without_paper is None else not without_paper

    def tarjeta_sin_retirar(self):
        return self.__get_state_values().get('ticket_out', None)

    def is_usb(self):
        return self._type == self.USB

    def is_serial(self):
        return self._type == self.SERIAL

    def is_dummy(self):
        return self._type == self.DUMMY

    def get_type(self):
        return self._type.upper()


class CustomTPTSerial(serial.Serial, CustomTPT):

    # OJO, RTS_CTS DEBE ir en 0
    RTS_CTS = 0
    XON_XOFF = 1
    TIMEOUT = 0.1
    BPS = 57600

    def __init__(self):
        CustomTPT.__init__(self, self.SERIAL)
        serial.Serial.__init__(self, timeout=self.TIMEOUT)

        self.initialize()

    def prepare(self):
        if self.is_open():
            self.close()

        for i in range(2):
            try:
                self.port = detect_printer_port()
                self.baudrate = self.bps or self.BPS
                self.setRtsCts(self.RTS_CTS)
                self.setXonXoff(self.XON_XOFF)
                self.setTimeout(self.TIMEOUT)
                self.open()
                return
            except Exception:
                time.sleep(self.TIMEOUT)

    def open(self):
        serial.Serial.open(self)
        self._isopen = True

    def close(self):
        serial.Serial.close(self)
        self._isopen = False

    def flush(self):
        serial.Serial.flush(self)
        serial.Serial.flushInput(self)
        serial.Serial.flushOutput(self)

def with_reconnect(func):
    """ Decorador para ejecutar funciones en un try y reconectar ante errores.
    """
    def encapsular(self, *args, **kwargs):
        for i in range(2):
            try:
                return func(self, *args, **kwargs)
            except usb.core.USBError:
                #logger.info('Impresora desconectada, reconectando...')
                self.open()
    return encapsular

class CustomTPTUSB(CustomTPT):
    def __init__(self):
        CustomTPT.__init__(self, self.USB)

        self.initialize()

    def prepare(self):
        self.open()

    def open(self):
        """ Realiza la apertura del USB"""
        #logger.debug("usblp %s : opening..." % (id(self), ))

        # El vendor y el product son los de la CustomTPT 112
        self.printer = usb.core.find(idVendor=USB_PRINTER_VENDOR_ID,
                                     idProduct=USB_PRINTER_PRODUCT_ID)
        if not self.printer:
            raise RuntimeError('No hay impresora')

        # Chequear si un driver de kernel, como usblp, está cargado y
        # ocupando el dispositivo; si eso pasa, lo descarga
        if self.printer.is_kernel_driver_active(0):
            self.printer.detach_kernel_driver(0)

        # Establecer la configuración USB por defecto
        self.printer.set_configuration()
        config = self.printer.get_active_configuration()
        interfaces = []
        for iface in config:
            interfaces.append(iface)

        # Interface 0 for usbprint
        interface = interfaces[0]
        # Get an endpoint instance
        self.ep_read = interface[0]
        self.ep_write = interface[1]
        self._isopen = True

    def close(self):
        # Cerrar y liberar recursos
#        logger.debug("usblp %s : closing..." % (id(self), ))

        del self.ep_read
        del self.ep_write
        del self.printer
        self._isopen = False

    def read(self, count=None):
        data = self.ep_read.read(count)
#        logger.debug("usblp %s < %s" % (id(self), repr(data)))
        return ''.join([chr(x) for x in data])

    @with_reconnect
    def write(self, data):
#        logger.debug("usblp %s > %s" % (id(self), data.encode('hex')))
        return self.ep_write.write(data, 2000)

    def flush(self):
        pass

    instance = None

    @classmethod
    def get_instance(klass):
        "Singleton: el puerto USB no se puede compartir"
        if not klass.instance:
            klass.instance = klass()
        return klass.instance


class CustomTPTDummy(CustomTPT):
    def __init__(self):
        CustomTPT.__init__(self, self.DUMMY)

        self.initialize()

    def prepare(self):
        self.fd = None
        self.open()

    def open(self):
        self.fd = open(DEBUG_IMPRESION_TEST_FILE, "ab")
        self._isopen = True

    def close(self):
        self.fd.close()
        self._isopen = False

    def read(self, count=None):
        return self.fd.read(count)

    def write(self, value):
        self.fd.write(value)

    def flush(self):
        pass
