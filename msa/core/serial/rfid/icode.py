# coding: utf-8
""" Clase para manejar los TAGs ICODE v1/v2 de Philips """

import struct
from zlib import crc32

from msa import get_logger
from msa.core.serial.rfid import TAG, TAGError
from msa.core.rfid.constants import TAG_VOTO, TAG_USUARIO_MSA,\
    TAG_PRESIDENTE_MESA, TAG_RECUENTO, TAG_APERTURA, TAG_DEMO, TAG_VIRGEN, \
    TAG_VACIO, TAG_DESCONOCIDO, TAG_INICIO, TAG_ADDENDUM, TAG_NO_ENTRA
from msa.core.settings import DEBUG_RFID


logger = get_logger("core")


class ICODE(TAG):
    """ Clase para controlar las particularidades del TAG ICODE v1 de Philips

        Estructura del TAG ICODE: Cada bloque tiene 4 bytes
          Bloque 00: Serial 2/2
          Bloque 01: Serial 1/2
          Bloque 02: Write access condition
          Bloque 03: Special function (EAS) / User data <= no usar
          Bloque 04: Family code identifier <= no usar / User data <= Tipo Tag
          Bloque 05: User data <= Byte 1: 'M'
                               <= Byte 2: 'S'
                               <= Byte 3: 'A'
                               <= Byte 4: Cant Bytes datos grabados (BYTES_QTY)
          Bloque 06: User data <= Comienzo datos usuario
              :       :
          Bloque 15: User data <= Fin datos de usuario
    """

    # Constantes
    # Cantidad de bloques disponibles para datos de usuario
    BLOQUES_USUARIO = 10
    # Cantidad de bytes por bloque
    BYTES_POR_BLOQUE = 4
    # Bloque de Write Access Condition
    BLOQUE_WAC = 2
    # Bloque de información del TAG
    BLOQUE_INFO = 5
    BLOQUE_CRC = 6
    # Bloque inicial para datos de usuario
    PRIMER_BLOQUE_USUARIO = 7
    # Cant bytes disponibles para datos de usuario. Le saco un bloque, el de
    # Info
    MAX_BYTES_DATOS = (BLOQUES_USUARIO * BYTES_POR_BLOQUE) - \
        (1 * BYTES_POR_BLOQUE)

    MIN_BLOQUE = 0
    MAX_BLOQUE = 16

    BLOQUE_TIPO = 4
    OFFSET_TIPO_DESDE = 2
    OFFSET_TIPO_HASTA = 4
    LONG_BYTES_QTY = 1  # 1 Byte del campo de longitud
    PACK_TYPE_QTY = 'B'  # Unsigned Char para ICODE1
    PACK_TYPE_CRC = 'i'  # Signed Integer para ICODE1

    COD_TAG_VACIO = '\x00\x00'
    COD_TAG_VOTO = '\x00\x01'
    COD_TAG_USUARIO_MSA = '\x00\x02'
    COD_TAG_PRESIDENTE_MESA = '\x00\x03'
    COD_TAG_RECUENTO = '\x00\x04'
    COD_TAG_APERTURA = '\x00\x05'
    COD_TAG_DEMO = '\x00\x06'
    COD_TAG_VIRGEN = '\x00\x07'
    COD_TAG_INICIO = '\x00\x7F'
    COD_TAG_ADDENDUM = '\x00\x80'
    COD_TAG_NO_ENTRA = '\x00\x45'
    COD_TAG_DESCONOCIDO = '\xff\xff'

    TIPOS_TAGS = { COD_TAG_VACIO: TAG_VACIO,
                   COD_TAG_VOTO: TAG_VOTO,
                   COD_TAG_USUARIO_MSA: TAG_USUARIO_MSA,
                   COD_TAG_PRESIDENTE_MESA: TAG_PRESIDENTE_MESA,
                   COD_TAG_RECUENTO: TAG_RECUENTO,
                   COD_TAG_APERTURA: TAG_APERTURA,
                   COD_TAG_DEMO: TAG_DEMO,
                   COD_TAG_INICIO: TAG_INICIO,
                   COD_TAG_ADDENDUM: TAG_ADDENDUM,
                   COD_TAG_VIRGEN: TAG_VIRGEN,
                   COD_TAG_DESCONOCIDO: TAG_DESCONOCIDO,
                   COD_TAG_NO_ENTRA : TAG_NO_ENTRA
                  }

    def __init__(self, serial, lector, clase, token_id=''):
        TAG.__init__(self, serial, clase, token_id)
        self.lector = lector

    def lee_bloque(self, nro_bloque):
        """ Lee un bloque del tag """
        datos = self.lector.leer_bloque(self, nro_bloque)
        if datos is None:
            return ''
        if len(datos) == self.BYTES_POR_BLOQUE:
            return datos
        else:
            raise TAGError('Error al leer TAG cod: ' + datos)

    def lee_bloques(self, desde, hasta):
        """ Lee varios bloques del tag a la vez
            Argumentos:
                desde -- bloque inicial (inclusive)
                hasta -- bloque final (inclusive)
        """
        return self.lector.leer_bloques(self, desde, hasta-desde+1)

    def escribe_bloque(self, nro_bloque, datos):
        """ Escribe un bloque en el tag. Datos debe ser de BYTES_POR_BLOQUE
            bytes.
            Luego de hacer una escritura se hace una lectura y se compara lo
            escrito con lo leído.
            En caso de que difieran devuelve un error.
        """
        if len(datos) != self.BYTES_POR_BLOQUE:
            raise TAGError('Debe escribir exactamente ' +
                           str(self.BYTES_POR_BLOQUE) +
                           ' bytes por bloque. Datos: ' + repr(datos))
        escrito = self.lector.escribir_bloque(self, nro_bloque, datos)
        if escrito != datos:
            #print "escribe_bloque: lo leido es distinto a lo escrito" + \
            #       ":> leido: %s escrito: %s" % (datos, escrito)
            raise TAGError('Error al escribir TAG. Cod: %s, Bloque: %i, Datos: %r' \
                           % (escrito, nro_bloque, datos))

    def lee_datos(self):
        """ Lee datos de usuario del tag y los devuelve como string """
        # Leo el bloque de tipo e información
        bloque_info = self.lee_bloque(self.BLOQUE_INFO)
        self.tag_leido = bloque_info[:self.long_token_id]
        if self.lector.comprobar_tag and self.tag_leido != self.token_id:
            return ''
        # Leo el bloque de CRC
        bloque_crc = self.lee_bloque(self.BLOQUE_CRC)

        # La longitud la guardo en formato big endian, 1 o 2 Bytes Unsigned
        long_datos =  \
        struct.unpack(self.PACK_TYPE_QTY, \
            bloque_info[self.BYTES_POR_BLOQUE-self.LONG_BYTES_QTY:])[0]
        bloque_base = self.PRIMER_BLOQUE_USUARIO
        datos = self.lee_bloques(bloque_base, \
            (long_datos / self.BYTES_POR_BLOQUE) + bloque_base)
        # Devuelvo datos, truncando a la longitud informada en el TAG
        if datos is not None:
            # Verifico que el CRC sea correcto
            if crc32(datos[:long_datos]) != struct.unpack(self.PACK_TYPE_CRC, \
                                                          bloque_crc)[0]:
                return ''
            return datos[:long_datos]
        return None

    def escribe_datos(self, datos, tipo_tag, marca_ro=False):
        """ Escribe datos de usuario en el tag.
            Los datos de usuario se guardan a partir del PRIMER_BLOQUE_USUARIO.
            El tipo de tag se almacena aparte, y sirve p/clasificar/diferenciar
            tags.
        """
        # Levanto una excepción si la longitud supera a la capacidad del TAG
        if len(datos) > self.MAX_BYTES_DATOS:
            raise TAGError(u'Tamaño excedido para escritura ' + \
                           str(len(datos)) + '/' + str(self.MAX_BYTES_DATOS))

        # Grabo el bloque de Tipo de Tag
        self.set_tipo(tipo_tag)
        # Grabo el bloque de información con la long de los datos al final
        # (Debo mantener la compatibilidad)
        # BYTES_POR_BLOQUE - LONG_BYTES_QTY es a partir de donde se ubica
        # la longitud de los datos (los últimos N bytes del bloque)
        bloque_info = self.lee_bloque(self.BLOQUE_INFO)
        # Primero escribo el token, luego obtengo el espacio que hay
        # entre el token y el último byte del bloque, luego escribo la longitud
        # (Debo mantener la compatibilidad entre ICODE 1 e ICODE 2).
        self.escribe_bloque(self.BLOQUE_INFO, self.token_id + \
            bloque_info[self.long_token_id:self.BYTES_POR_BLOQUE-self.LONG_BYTES_QTY]
            + struct.pack(self.PACK_TYPE_QTY, len(datos)))

        # Escribo el CRC de los datos
        self.escribe_bloque(self.BLOQUE_CRC, \
                            struct.pack(self.PACK_TYPE_CRC, crc32(datos)))

        bloque_actual = self.PRIMER_BLOQUE_USUARIO

        # Parto el dato por tamaño de bloque
        for i in range(0, len(datos), self.BYTES_POR_BLOQUE):
            dato_bloque = datos[i:i + self.BYTES_POR_BLOQUE]
            # Agrego \0 como padding para llegar a la longitud de bloque
            dato_bloque = dato_bloque + '\x00' * \
                            (self.BYTES_POR_BLOQUE - len(dato_bloque))
            self.escribe_bloque(bloque_actual, dato_bloque)
            bloque_actual += 1

        if marca_ro:
            self.lector.set_read_only(self)

    def read_only(self):
        """ Esta función devuelve True si el tag es de sólo lectura,
            False en caso contrario.
        """
        return self.lector.is_read_only(self)

    def get_tipo(self):
        """ Devuelvo el tipo de Tag, almacenado en el campo Tipo de Tag.
            Bytes 2 y 3 del bloque 4
        """
        try:
            bloque_info = self.lee_bloque(self.BLOQUE_INFO)
            token_err = bloque_info[:self.long_token_id] != self.token_id
            tipo = self.lee_bloque(self.BLOQUE_TIPO)
            if tipo:
                tipo_tag = tipo[self.OFFSET_TIPO_DESDE:self.OFFSET_TIPO_HASTA]
                if self.lector.comprobar_tag and token_err and \
                        (tipo_tag not in (self.COD_TAG_VIRGEN,
                                          self.COD_TAG_VACIO)):
                    return None
                else:
                    return self.TIPOS_TAGS[tipo_tag]
        except TAGError:
            if DEBUG_RFID:
                logger.debug(TAGError)
        return None

    def set_tipo(self, tipo_tag):
        """ Setea en el tag un tipo de Tag válido, dentro de los definidos
            como constante en esta clase: TAG_VOTO, TAG_USUARIO_MSA, etc.
        """

        if tipo_tag not in self.TIPOS_TAGS.values():
            raise TAGError('Tipo de Tag no válido para escribir: %s' \
                           % tipo_tag)
        # Necesito obtener el contenido actual de los bytes 0 y 1, que no debo
        # modificar
        reverse_dict = dict(zip(self.TIPOS_TAGS.values(),
                                self.TIPOS_TAGS.keys()))
        tipo_tag = reverse_dict[tipo_tag]
        bloque_tipo = self.lee_bloque(self.BLOQUE_TIPO)
        if DEBUG_RFID:
            logger.debug('bloque_tipo: ' + repr(bloque_tipo))
        bloque_tipo_nuevo = bloque_tipo[:self.OFFSET_TIPO_DESDE] + tipo_tag + \
                            bloque_tipo[self.OFFSET_TIPO_HASTA:]
        if DEBUG_RFID:
            logger.debug('bloque_tipo_nuevo: ' + repr(bloque_tipo_nuevo))
        self.escribe_bloque(self.BLOQUE_TIPO, bloque_tipo_nuevo)

    def get_datos_and_tipo(self):
        """ Función que en una única llamada lee el tipo de tag y la
            información almacenada.
            Pensado para ir reemplazando a lee_datos() en forma gradual.
            Devuelve una tupla de 2 strings: (tipo, datos)
        """
        tipo = self.get_tipo()
        datos = self.lee_datos()
        return (tipo, datos)


class ICODE2(ICODE):
    """
        Clase para controlar las particularidades del TAG ICODE 2
        (aka SLI/ICS 20) de Philips/NXP

        Estructura del TAG ICODE: Cada bloque tiene 4 bytes
            Bloque -4: Serial 2/2
            Bloque -3: Serial 1/2
            Bloque -2: Special functions EAS, AFI, DSFID <= no usar
            Bloque -1: Write access condition
            Bloque 00: User data <= Byte   1: '\x7E' - Token de ID de version
                                 <= Byte 2: Tipo de Tag
                                 <= Byte 3-4: Cant Bytes datos grabados,
                                 BYTES_QTY)
            Bloque 01: User data <= Comienzo datos usuario
                :       :
            Bloque 27: User data <= Fin datos de usuario

        Estructura del UID:
            E0: Definido por el estandar ISO15693
            04: Vendedor (NXP)
            01: Identificador del chip SL2 ICS20 (1K)
    """

    # Constantes
    # Identificador del chip ICS20 (1K)
    IDENTIFICADOR = 01
    # Cantidad de bloques disponibles para datos de usuario
    BLOQUES_USUARIO = 27
    # Cantidad de bytes por bloque
    BYTES_POR_BLOQUE = 4
    # Bloque de Write Access Condition
    BLOQUE_WAC = -1
    # Bloque de información del TAG
    BLOQUE_INFO = 0
    # Bloque de información del TAG
    BLOQUE_CRC = 1
    # Bloque inicial para datos de usuario
    PRIMER_BLOQUE_USUARIO = 2
    # Cant bytes disponibles para datos de usuario. Le saco un bloque, el de
    # Info
    MAX_BYTES_DATOS = BLOQUES_USUARIO * BYTES_POR_BLOQUE - 1 * BYTES_POR_BLOQUE
    # Debería ser -4, pero no hay acceso directo...
    MIN_BLOQUE = 1
    # Ultimo bloque direccionable, no inclusive
    MAX_BLOQUE = BLOQUES_USUARIO
    # Bloque con la información de tipo de tag
    BLOQUE_TIPO = 0
    OFFSET_TIPO_DESDE = 1
    OFFSET_TIPO_HASTA = 2
    # Campo Longitud - Cantidad de Bytes que Ocupa
    LONG_BYTES_QTY = 2
    # Unsigned Short para ICODE2 (2 Bytes)
    PACK_TYPE_QTY = '>H'
    # Signed Integer para ICODE2 (2 Bytes)
    PACK_TYPE_CRC = 'i'

    # Tengo que redefinir los tipos de chip porque voy a usar un solo Byte
    COD_TAG_VACIO = '\x00'
    COD_TAG_VOTO = '\x01'
    COD_TAG_USUARIO_MSA = '\x02'
    COD_TAG_PRESIDENTE_MESA = '\x03'
    COD_TAG_RECUENTO = '\x04'
    COD_TAG_APERTURA = '\x05'
    COD_TAG_DEMO = '\x06'
    COD_TAG_VIRGEN = '\x07'
    COD_TAG_INICIO = '\x7F'
    COD_TAG_ADDENDUM = '\x80'
    COD_TAG_DESCONOCIDO = '\xff'
    COD_TAG_NO_ENTRA = '\x45'

    TIPOS_TAGS = { COD_TAG_VACIO: TAG_VACIO,
                   COD_TAG_VOTO: TAG_VOTO,
                   COD_TAG_USUARIO_MSA: TAG_USUARIO_MSA,
                   COD_TAG_PRESIDENTE_MESA: TAG_PRESIDENTE_MESA,
                   COD_TAG_RECUENTO: TAG_RECUENTO,
                   COD_TAG_APERTURA: TAG_APERTURA,
                   COD_TAG_DEMO: TAG_DEMO,
                   COD_TAG_VIRGEN: TAG_VIRGEN,
                   COD_TAG_INICIO: TAG_INICIO,
                   COD_TAG_ADDENDUM: TAG_ADDENDUM,
                   COD_TAG_NO_ENTRA : TAG_NO_ENTRA,
                   COD_TAG_DESCONOCIDO: TAG_DESCONOCIDO}

