# coding: utf-8

import struct

from msa.core.serial.rfid import TAG, TAGError


class MIFARE(TAG):
    """
        Clase para controlar las particularidades del TAG Mifare de Philips

        Estructura del TAG MIFARE: Cada bloque tiene 16 bytes
        #TODO: Describir más la estructura
        #TODO: Sólo compatible con LectorMultiISO
    """

    # Constantes
    #BLOQUES_USUARIO = 11 # Cantidad de bloques disponibles para datos de usuario
    BYTES_POR_BLOQUE = 16 # Cantidad de bytes por bloque
    BLOQUES_POR_SECTOR = 4
    MIN_SECTOR = 0
    MAX_SECTOR = 15
    MIN_BLOQUE = 0
    MAX_BLOQUE = 63
    #BLOQUE_WAC = 2 # Bloque de Write Access Condition
    BLOQUE_INFO = 1 # Bloque de información del TAG
    PRIMER_BLOQUE_USUARIO = 4 # Bloque inicial para datos de usuario
    # Cantidad de bytes disponibles para datos de usuario. Le saco un bloque, el de Info
    #MAX_BYTES_DATOS = BLOQUES_USUARIO * BYTES_POR_BLOQUE - 1 * BYTES_POR_BLOQUE

    PREFIJO_INFO = 'MSA'
    # Bloque con info extra a los datos del tag, para que lo use la aplicación
    BLOQUE_INFO_EXTRA = 2

    def __init__(self, serial, lector, clase):
        TAG.__init__(self, serial, clase)
        self.lector = lector
        self.__sector_permitido = None

    def __get_acceso(self, nro_sector):
        """ Obtiene acceso al sector que se pasa por parámetro
            y se actualiza el sector permitido.
            # TODO: Sólo compatible con MultiISO.
        """
        resultado = ''
        nro_sector = int(nro_sector)
        if (nro_sector >= MIFARE.MIN_SECTOR) and (nro_sector <= MIFARE.MAX_SECTOR):
            resultado = self.lector._enviar_comando('l' + chr(nro_sector) + '\xFF\r')
        if resultado == 'L':
            self.__sector_permitido = nro_sector
        else:
            raise TAGError('Error al acceder al sector %i de la tarjeta, cod: %s' \
                            % (nro_sector, resultado))

    def __puedo_acceder(self, nro_bloque):
        """ Devuelve True o False según el acceso que se tenga
            al sector correspondiente del bloque dado
        """
        nro_sector = self._get_nro_sector(nro_bloque)
        return nro_sector == self.__sector_permitido

    def _get_nro_sector(self, nro_bloque):
        """ Devuelve el número de sector que le corresponde al número de bloque """
        return int(nro_bloque) / MIFARE.BLOQUES_POR_SECTOR

    def _bloque_metadatos(self, nro_bloque):
        """ Devuelve True o False según si el número de bloque corresponde
            a uno con metadatos o no. Según la documentación de MiFare standard,
            es el último bloque de cada sector.
        """
        self._check_limite(nro_bloque)
        if ((nro_bloque == 0) or ((nro_bloque % MIFARE.BLOQUES_POR_SECTOR) == \
                                  (MIFARE.BLOQUES_POR_SECTOR-1))):
            return True
        else:
            return False

    def _check_limite(self, nro_bloque):
        """ Devuelve True o False según si el número de bloque está
            dentro del rango mapeable
        """
        if (nro_bloque < MIFARE.MIN_BLOQUE) or (nro_bloque > MIFARE.MAX_BLOQUE):
            raise TAGError('Error al leer el bloque %i del TAG, cod: Fuera de rango' \
                           % (nro_bloque))


    def lee_bloques(self, desde, hasta):
        """ Lee varios bloques del tag a la vez """
        datos=''
        for i in range(desde, hasta+1):
            datos = datos+self.lee_bloque(i)
        return datos


    def lee_bloque(self, nro_bloque):
        """ Lee un bloque del tag """
        self._check_limite(nro_bloque)
        if not self.__puedo_acceder(nro_bloque):
            self.__get_acceso(self._get_nro_sector(nro_bloque))
        datos = self.lector.leer_bloque(self, nro_bloque)
        if len(datos) == MIFARE.BYTES_POR_BLOQUE:
            return datos
        else:
            raise TAGError('Error al leer el bloque %i del TAG, cod: %s ' % \
                           (nro_bloque, datos))


    def escribe_bloque(self, nro_bloque, datos):
        """ Escribe un bloque en el tag. Datos debe ser de BYTES_POR_BLOQUE bytes.
            Luego de hacer una escritura se hace una lectura y se compara lo
            escrito con lo leído. En caso de que difieran devuelve un error.
        """
        self._check_limite(nro_bloque)
        if len(datos) != MIFARE.BYTES_POR_BLOQUE:
            raise TAGError('Debe escribir exactamente %s bytes por bloque' % \
                           str(MIFARE.BYTES_POR_BLOQUE))
        if not self.__puedo_acceder(nro_bloque):
            self.__get_acceso(self._get_nro_sector(nro_bloque))
        escrito = self.lector.escribir_bloque(self, nro_bloque, datos)
        if escrito != datos:
            raise TAGError('Error al escribir el bloque %i del TAG, cod: %s' % \
                           (nro_bloque, escrito))

    def lee_datos(self):
        """ Lee datos de usuario del tag y los devuelve como string """
        # Leo el bloque de tipo e información
        bloque_info = self.lee_bloque(MIFARE.BLOQUE_INFO)
        if bloque_info[:3] != MIFARE.PREFIJO_INFO:
            return ''
        # La longitud la guardo en formato big endian, 2 bytes unsigned
        long_datos = struct.unpack('>H', bloque_info[3:5])[0]
        bloque_actual = MIFARE.PRIMER_BLOQUE_USUARIO
        datos = ''
        for i in range(0, long_datos, MIFARE.BYTES_POR_BLOQUE):
            dato_bloque = self.lee_bloque(bloque_actual)
            datos += dato_bloque
            bloque_actual += 1
            # Me salteo de leer el bloque de metadatos que hay por sector
            if self._bloque_metadatos(bloque_actual):
                bloque_actual += 1
        # Devuelvo datos, truncando a la longitud informada en el TAG
        return datos[:long_datos]

    def escribe_datos(self, datos):
        """ Escribe datos de usuario en el tag.
            Los datos de usuario se guardan a partir del PRIMER_BLOQUE_USUARIO.
            El tipo de tag se almacena aparte, y sirve para clasificar o
            diferenciar tags.
        """
        # TODO: Agregar chequeo de tamaño excedido
        #if len(datos) > MIFARE.MAX_BYTES_DATOS:
        #    raise TAGError('Tamaño excedido para escritura ' +
        #                   str(len(datos)) + '/' + str(ICODE.MAX_BYTES_DATOS))

        # Grabo el bloque de información con ICODE.PREFIJO_INFO + long datos +
        # completo con ceros
        # La longitud la guardo en formato big endian, 2 bytes unsigned
        meta_info = MIFARE.PREFIJO_INFO + struct.pack('>H', len(datos))
        self.escribe_bloque(MIFARE.BLOQUE_INFO, meta_info + '\x00' * \
                            (MIFARE.BYTES_POR_BLOQUE - len(meta_info)))
        bloque_actual = MIFARE.PRIMER_BLOQUE_USUARIO

        # Parto el dato por tamaño de bloque
        for i in range(0, len(datos), MIFARE.BYTES_POR_BLOQUE):
            dato_bloque = datos[i:i + MIFARE.BYTES_POR_BLOQUE]
            # Agrego \0 para llegar a la longitud de bloque
            dato_bloque = dato_bloque + '\x00'*(MIFARE.BYTES_POR_BLOQUE - \
                                                len(dato_bloque))
            self.escribe_bloque(bloque_actual, dato_bloque)
            bloque_actual += 1
            # Me salteo de leer el bloque de metadatos que hay por sector
            if self._bloque_metadatos(bloque_actual):
                bloque_actual += 1

    def lee_datos_extra(self):
        """ Lee el campo de datos extra, se utiliza aparte del campo de datos """
        # La info extra está guardada en un único bloque, cuyo primer byte dice
        # cuál es la longitud de los datos extras
        info_extra = self.lee_bloque(MIFARE.BLOQUE_INFO_EXTRA)
        long_datos = ord(info_extra[0])
        return info_extra[1:long_datos+1]


    def escribe_datos_extra(self, datos):
        """ Escribe el campo de adtos extra, se utiliza aparte del campo de datos """
        max_bytes = MIFARE.BYTES_POR_BLOQUE - 1 # que necesito para el byte de long.
        largo_datos = len(datos)
        if largo_datos > max_bytes:
            raise TAGError('No puedo guardar mas de %i bytes en el campo de datos extra' \
                           % max_bytes)
        else:
            self.escribe_bloque(MIFARE.BLOQUE_INFO_EXTRA, chr(largo_datos) + \
                                 datos + '\x00' * \
                                 (MIFARE.BYTES_POR_BLOQUE - (largo_datos+1)))
