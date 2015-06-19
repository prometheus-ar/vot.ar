# coding: utf-8
""" Módulo que implementa el manejo del Lector TRF7960 de Texas Instruments """

import binascii
import struct
import time

from msa import get_logger
from msa.core.serial.rfid import LectorRFID, TAGError
from msa.core.serial.rfid.helpers import change_byte_order
from msa.core.serial.rfid.icode import ICODE2
from msa.core.settings import DEBUG_RFID, TOKEN, COMPROBAR_TOKEN
from msa.core.rfid.constants import CLASE_ICODE2

SLOTS = 16

logger = get_logger("core")

class LectorTexas(LectorRFID):
    """ Clase que controla el Lector TRF7960 de Texas Instruments """

    SOF = '01'
    Data_Length = '0000'
    Reader_Type = '03'
    Entity = '04'
    EOF = '0000'
    Base_Length = 7 # Suma de bytes de todos los campos anteriores
    MAX_BUFFER = 1024

    TAG_TEXAS = 0

    def __init__(self, token_id=TOKEN, comprobar_tag=COMPROBAR_TOKEN):
        LectorRFID.__init__(self, token_id, comprobar_tag)
        self.__inicializado = False
        # El timeout minimo que tiene el firmware es 60ms con lo cual no
        # debería ser menor a eso.
        self.timeout = 0.1

    def conectar(self):
        # Abro el puerto
        LectorRFID.conectar(self)
        # Testeo que haya un lector
        if self._ser.isOpen() and self._inicializar():
            self.__inicializado = True
            return self._ser.isOpen()
        return False

    def desconectar(self):
        LectorRFID.desconectar(self)
        self.__inicializado = False

    def _inicializar(self):
        """ Inicializa el lector """
        # 1) FF - Initialization
        # 2) Register Write: 10
        #    00 (Chip Status) = 21 (RF Out Active, +5VDC Operation), 31 (Half
        #    Power)
        #    01 (ISO Control Register) = 02 (Set protocol to ISO15693 High Bit
        #                       Rate, 26.48 Kbps, one subcarrier, 1 out of 4)
        # 3) F0 = ACG Toggle. 00 = AGC OFF.
        # 4) F1 = AM/PM Toggle. FF = AM
        INIT_CMDs = ('FF', '1000310102', 'F000', 'F1FF', 'F7FF')
        for cmd in INIT_CMDs:
            if not self._enviar_comando(cmd):
                return False
            time.sleep(0.01)
        return True

    def get_tag(self):
        """ Devuelve una instancia de TAG
            ICODE2 únicamente soportado por ahora.
        """
        if not self.__inicializado:
            return None
        inventory_cmd = '14260100' # One slot
        res = self._enviar_comando(inventory_cmd)
        if res:
            if res[0] == '{': # Conflicto, dos o más tags en un slot: {00}[z,40]
                self._enviar_comando('F700') # Apago el led
                if DEBUG_RFID:
                    logger.debug('Conflicto: dos o mas tags disponibles')
                return None
            elif res.startswith('0176'): # No hay nada
                self._enviar_comando('F700') # Apago el led
                return None
            else: # Hay un tag, parseo el string [78DF0E34000104E0,75]
                self._enviar_comando('F7FF') # Prendo el led
                return ICODE2(change_byte_order(res[:-4]), self, CLASE_ICODE2,
                              self.token_id)
        else:
            return None

    def get_multitag(self):
        """ Devuelve instancias de TAG en una lista o una lista vacía.
            ICODE2 únicamente soportado por ahora.
        """
        if not self.__inicializado:
            return None
        inventory_cmd = '14060100' # Multi slot
        self._enviar_comando(inventory_cmd, leer_respuesta=False)
        res_tags = []
        nscans = 1
        while nscans:
            for slot in range(SLOTS):
                res = self._leer_respuesta(capturar_colisiones=False)
                if res:
                    if res.startswith('017A'): # Hay conflicto el lector va a ser 2 vueltas de slots
                        nscans += 1
                        if DEBUG_RFID:
                            logger.debug('Conflicto: dos o mas tags disponibles')
                        continue
                    if res.startswith('0176'): # No hay nada
                        continue # voy al siguiente slot
                    else: # Hay un tag, parseo el string
                        res_tags.append(ICODE2(change_byte_order(res[:-4]), self,
                                        CLASE_ICODE2, self.token_id))
            nscans -= 1
        if res_tags:
            self._enviar_comando('F7FF') # Prendo el led
        else:
            self._enviar_comando('F700') # Apago el led
        if DEBUG_RFID:
            logger.debug('encontré: %i tags' % len(res_tags))
        return res_tags
    
#    def analize(funcion):
#        def time_it(*lista_args):
#            if DEBUG_RFID:
#                tiempo1 = time.time()
#                valor = funcion(*lista_args)
#                tiempo2 = time.time()
#                delta = tiempo2 - tiempo1
#                params = (funcion.func_name, delta, valor)
#                msg = "'%s()' ejecutada en %s seg.\nRetorna %s" % params
#            else:
#                valor = funcion(*lista_args)
#            return valor
#
#        return time_it
#
#    @analize
    def _enviar_comando(self, comando, leer_respuesta=True):
        """ Envía un comando al lector en el protocolo que maneja.
            Obtiene la respuesta del lector (interpreta el protocolo) y
            devuelve la última línea de la respuesta (lo útil) como string.
            Ante cualquier error (hay un chequeo del eco del comando), devuelve
            None
            El comando y sus parámetros deben ser bytes pero en ascii, es
            por eso que el comando debe ser un string con cantidad par de
            elementos.
        """
        cmd_len = len(comando)
        cmd_len_bytes = cmd_len / 2
        if cmd_len % 2 != 0:
            raise TAGError('Longitud de comando impar: %r' % comando)
        # Calculo primero en binario y convierto a ascii
        lendata = binascii.b2a_hex(struct.pack('<H', self.Base_Length +
                                               cmd_len_bytes))
        # String a Enviar. Paquete binario Texas (ASCII):
        # SoF (1B) + Data Length (2B-LSB) + Reader Type + Entity + Command +
        # Params + EoF (2B)
        SOF = self.SOF
        EOF = self.EOF

        request = SOF + lendata + self.Reader_Type + self.Entity + comando + EOF
        request = request.upper()
        if DEBUG_RFID:
            logger.debug('\n>> %s' % request)

        self._ser.flushInput() # Borro el buffer de entrada
        self._ser.flushOutput() # Borro el buffer de salida
        self._ser.write(request) # Envio el comando
        
        if leer_respuesta:
            return self._leer_respuesta()

    def _leer_respuesta(self, capturar_colisiones=True):
        rEncabezado = self._ser.read(4)
        rEncabezado = rEncabezado.strip()
        if DEBUG_RFID:
            logger.debug(rEncabezado)

        if not rEncabezado: # No leí nada del serial, hay un lector ahí?
            if DEBUG_RFID:
                logger.debug("mensaje sin encabezado, RESTARTING...")
            self._ser.flushInput() # Borro el buffer de entrada
            self._ser.flushOutput() # Borro el buffer de salida
            self._ser.write('010C00030410003101020000')
            time.sleep(1)
            return None
        if len(rEncabezado) != 4: # Leí 4 y no vinieron 4 Bytes, error.
            logger.error("Paquete malformado: %s %s" % (rEncabezado))
        
        rData = ''
        #Tengo el inicio de trama y el largo
        if rEncabezado[:2] == '01':
            rlendata = int(rEncabezado[2:], 16)
            if DEBUG_RFID:
                logger.debug("Encabezado: %s; quedan por leer %s" % \
                             (rEncabezado, rlendata))
            # Leer el resto del mensaje que va a ser de rlendata - 2 (por
            # los dos leidos)
            rData = self._ser.read((rlendata * 2) - 4)
            if DEBUG_RFID:
                logger.debug('<< %s%s' % (rEncabezado, rData))
            if rData[-2:] == '04':
                rData = rData[:-2]
                error = ''
                if rData == '010F':
                    error = "Unknown error. Cod: %s" % rData
                elif rData == '0100':
                    error = "Error de lectura? Colision. Cod: %s" % rData
                elif rData == '0107':
                    error = "Error de seteo. Cod: %s"%rData

                elif rData == '017A' and capturar_colisiones:
                    error = "Colision?. Cod: %s"%rData
                #elif rData == '0176':
                #    error = "Sin TAG?. Cod: %s"%rData
                elif rData == '0174':
                    error = \
                    "El micro no obtuvo respuesta del lector. Cod: %s"%rData
                elif rData == '0104':
                    error = \
                    "Mala comunicación lector-micro. Cod: %s"%rData
                elif rData == '0101':
                    error = "Comando desconocido. Cod: %s"%rData
                if error:
                    if DEBUG_RFID:
                        logger.debug(error)
                    raise TAGError(error)
                else:
                    return rData

    def leer_bloque(self, tag, nro_bloque):
        """ Envía al lector el comando para leer un bloque del tag y retorna su
            valor como string
        """
        if not self.__inicializado:
            return None
        # Habilito el Flag Option
        read_cmd = '186220' if self.TAG_TEXAS else '182220'
        read_cmd = read_cmd + change_byte_order(tag.serial).upper() + \
                    '%02x' % nro_bloque
        res = self._enviar_comando(read_cmd)
        if res:
            # TODO: Parsear 00 => OK, errores
            limite = 4 if self.TAG_TEXAS else 2
            # TODO: Verificar realmente los errores!!!
            if res[:2] == '00':
                try:
                    return binascii.a2b_hex(res[limite:])
                except Exception, e:
                    logger.error(e)
                    return None
        else:
            return None

    def leer_bloques(self, tag, nro_bloque, cantidad):
        """ Envía al lector el comando para leer N bloques del tag y retorna su
            valor como string.
            Si cantidad = 0, devuelve None
            Ejemplo:
            In [10]: l.leer_bloques(t, 0, 1)
            Out[10]: '~\x01\x00\x06'
        """
        if not self.__inicializado or cantidad <=0:
            return None
        # Habilito el Flag Option
        readn_cmd = '186223' if self.TAG_TEXAS else '182223'
        readn_cmd = readn_cmd + change_byte_order(tag.serial).upper() + \
                    '%02x%02x' % (nro_bloque, cantidad-1)
        res = self._enviar_comando(readn_cmd)
        if res is not None:
            # TODO: Parsear 00 => OK, errores
            # TODO: Verificar realmente los errores!!!
            if res[:2] == '00':
                try:
                    if self.TAG_TEXAS:
                        datos = res[2:]
                        ret = ''
                        while datos:
                            datos = datos.partition('00')[2]
                            ret += binascii.a2b_hex(datos[:8])
                        return ret
                    else:
                        return binascii.a2b_hex(res[2:])
                except:
                    return None
            else:
                logger.error("Respuesta de RFID no especificada %s" % res)
        else:
            return None

    def escribir_bloque(self, tag, nro_bloque, valor):
        """ Envía al lector el comando para escribir en un bloque del tag el
            valor que se pasa como parámetro.
            Retorna el mismo string de bytes escrito en caso de éxito, sino un
            string vacío.
        """
        if not self.__inicializado:
            return None
        # Habilito Flag Option
        write_cmd = '186221' if self.TAG_TEXAS else '182221'
        write_cmd = write_cmd + change_byte_order(tag.serial).upper() + \
                    '%02x' % nro_bloque + valor.encode('hex')
        res = self._enviar_comando(write_cmd)
        if DEBUG_RFID:
            logger.debug("devuelve: >%s<" % res)
        if res is not None:
            # TODO: Parsear 00 => OK, errores
            if res == '00':
                return valor
        return None

    def is_read_only(self, tag):
        """ Chequea que si el tag en cuestión es de sólo lectura o no.
            Devuelve True en caso de que sea sólo lectura, False en caso
            contrario
        """
        if not self.__inicializado:
            return None
        security_status_cmd = '18222C' + change_byte_order(tag.serial) + \
                              '%02x%02x' % (0, tag.MAX_BLOQUE)
        res = self._enviar_comando(security_status_cmd)
        if res:
            # Devuelve un string de 0 o 1 según sea read only o no.
            try:
                return bool(int(res))
            except ValueError:
                pass
        return False

    def _set_read_only(self, tag, nro_bloque):
        """ Setea un bloque del tag como de sólo lectura. """
        lock_cmd = '182022' + change_byte_order(tag.serial).upper() + \
                    '%02x' % nro_bloque
        res = self._enviar_comando(lock_cmd)
        if res:
            # TODO: Parsear 00 => OK, errores
            if res == '00':
                return True
        return None

    def set_read_only(self, tag):
        """ Setea el tag en cuestión como de sólo lectura. """
        if not self.__inicializado:
            return None
        for nro_bloque in range(tag.MAX_BLOQUE):
            if not self._set_read_only(tag, nro_bloque):
                return False # TODO: Validar errores
        return True
