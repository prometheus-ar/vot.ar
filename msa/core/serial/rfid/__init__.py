# coding: utf-8
import time

from base64 import b64encode
from binascii import hexlify
from serial import Serial
from serial.serialutil import SerialException

from msa.core.serial.rfid.helpers import detect_rfid_port
from msa.core.settings import DEBUG_RFID, TOKEN, CLASE_LECTOR


def get_lector(*args, **kwargs):
    """ Devuelve una instancia de la clase hija de LectorRFID configurado """
    nombre_clase = 'Lector%s' % CLASE_LECTOR
    modulo = __import__('%s.lector_%s' % (__name__, CLASE_LECTOR.lower()), \
                        fromlist=[nombre_clase])
    clase = getattr(modulo, nombre_clase, None)
    if clase:
        return clase(*args, **kwargs)


class LectorRFID(object):
    """ Clase de Lector abstracta para ser implementada por subclases """

    def __init__(self, token_id=TOKEN, comprobar_tag=True):
        self.baudrate = None
        self.timeout = None
        self.XonXoff = None
        self._configurar_puerto()
        self.token_id = chr(int(token_id, 16))
        self.comprobar_tag = comprobar_tag

    def _configurar_puerto(self):
        self._ser = Serial()
        self._ser.baudrate = 115200 if self.baudrate is None else self.baudrate
        self._ser.timeout = 1 if self.timeout is None else self.timeout
        self._ser.setXonXoff(False if self.XonXoff is None else self.XonXoff)
        self._ser.port = detect_rfid_port()
        if self._ser.port is None:
            raise SerialException

    def conectar(self):
        """ A implementar por la subclase.
            Método para conectarse al tag. La conexión abre el puerto serial
            especificado en el constructor de la clase y setea los parámetros
            de puerto correspondientes.
            Una vez abierto el puerto se comprueba que haya un lector multiiso,
            enviándole un comando de select y si la respuesta es la esperada,
            el método devuelve True. En caso contrario (el puerto no se abrió o
            el dispositivo conectado es otro, se devuelve False.
        """
        self._ser.close()
        self._configurar_puerto()
        self._ser.open()

    def desconectar(self):
        """ A implementar por la subclase.
            Método para desconectarse del lector.
        """
        self._ser.close()

    def get_timeout(self):
        """ Devuelve el timeout del puerto.
        """
        return self._ser.getTimeout()

    def get_tag(self):
        """ A implementar por la subclase.
            Consulta al lector por la disponibilidad de un tag.
            Devuelve una instancia de ICODE, ICODE2 o MIFARE, según el tipo de
            tag encontrado (todas subclases de TAG), o None en caso contrario.
        """
        pass

    def _enviar_comando(self, comando):
        """ A implementar por la subclase.
            Envía un comando al lector en el protocolo binario.
            Obtiene la respuesta del lector (interpreta el protocolo) y
            devuelve la respuesta como string. Ante cualquier error devuelve
            None.
        """
        pass

    def leer_bloque(self, tag, nro_bloque):
        """ A implementar por la subclase.
            Envía al lector el comando para leer un bloque del tag y retorna su
            valor como string
        """
        pass

    def leer_bloques(self, tag, nro_bloque, cantidad):
        """ A implementar por la subclase.
            Envía al lector el comando para leer N bloques del tag y retorna su
            valor como string
        """
        pass

    def escribir_bloque(self, tag, nro_bloque, valor):
        """ A implementar por la subclase.
            Envía al lector el comando para escribir en un bloque del tag el
            valor que se pasa como parámetro.
        """
        pass

    def is_read_only(self, tag):
        """ A implementar por la subclase.
            Chequea que si el tag en cuestión es de sólo lectura o no.
            Devuelve True en caso de que sea sólo lectura, False en caso
            contrario
        """
        pass

    def set_read_only(self, tag):
        """ A implementar por la subclase.
            Setea el tag en cuestión como de sólo lectura.
        """
        pass


class TAGError(Exception):
    """ Exception genérica creada para trabajar con el módulo """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class TAG:
    """ Clase que define un tag genérico """
    def __init__(self, serial, clase, token_id=''):
        self.serial = serial
        self.clase = clase
        self.token_id = token_id
        self.long_token_id = len(token_id)

    def get_serial(self):
        return self.serial

    def get_clase(self):
        return self.clase

    def to_dict(self):
        data = None
        intentos = 0
        #evitando posibles ruidos en la lectura del tag.
        while intentos < 10 and data is None:
            try:
                tmp_data = {}
                tmp_data['serial'] = self.get_serial()
                tmp_data['clase'] = self.get_clase()
                tmp_data['tipo'] = self.get_tipo()
                datos = self.lee_datos()
                tmp_data['token'] = hexlify(self.tag_leido).upper()
                tmp_data['datos'] = b64encode(datos) if datos is not None else ""
                tmp_data['longitud'] = len(datos) if datos is not None else 0
                tmp_data['reception_level'] = 'N/A'
                tmp_data['read_only'] = self.read_only()
                data = tmp_data
            except TAGError:
                time.sleep(0.1)
            intentos += 1
        return data

