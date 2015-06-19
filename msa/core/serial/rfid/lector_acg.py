# coding: utf-8

import time

from msa.core.serial.rfid import LectorRFID, TAGError
from msa.core.serial.rfid.icode import ICODE, ICODE2
from msa.core.serial.rfid.mifare import MIFARE
from msa.core.settings import TOKEN
from msa.core.serial.rfid.constants import CLASE_ICODE, CLASE_ICODE2, \
    CLASE_MIFARE

def msg2bcc(msg):
    """ Calcula la info de paridad utilizada por el lector Multiiso ACG.
        Se utiliza en el protocolo binario de comunicación serial.
    """
    bcc = '\x00'
    for car in msg:
        bcc = chr(ord(bcc) ^ ord(car))
    return bcc

class LectorACG(LectorRFID):
    """ Clase que controla el Lector MultiISO de ACG """

    def __init__(self, token_id=TOKEN, comprobar_tag=True):
        LectorRFID.__init__(self, token_id, comprobar_tag)

    def conectar(self):
        LectorRFID.conectar(self)
        # Testeo que haya un lector
        if self._ser.isOpen():
            if self._enviar_comando('s'):
                # Lo pongo en modo bloqueante, lo cierro y lo abro
                self._ser.close()
                self._ser.open()
                return self._ser.isOpen()
        return False

    def get_tag(self):
        res = self._enviar_comando('s')

        # Según el tipo de tag que me diga el lector en el primer byte,
        # instancio la subclase Tag correspondiente con la data del tag
        # que es el resto de los bytes leídos (El lector multiiso devuelve la
        # info así).
        # Si el comando select ('s') devuelve 'N' no hay Tag presente en el
        # campo
        # if res != 'N':

        if res[0] == 'I':
            self._enviar_comando('dg') # Prendo el led
            return ICODE(res[1:], self, CLASE_ICODE, self.token_id)
        elif res[0] == 'V':
            self._enviar_comando('dg') # Prendo el led
            return ICODE2(res[1:], self, CLASE_ICODE2, self.token_id)
        elif res[0] == 'M':
            self._enviar_comando('dg') # Prendo el led
            return MIFARE(res[1:], self, CLASE_MIFARE)
        else:
            self._enviar_comando('dn') # Apago el led
            return None

    def _enviar_comando(self, comando):
        """ Envía un comando al lector en el protocolo binario.
            Obtiene la respuesta del lector (interpreta el protocolo) y
            devuelve la respuesta como string. Ante cualquier error devuelve
            None.
        """
        sSTX = '\x02'
        sStation_Id = '\x01'
        sETX = '\x03'
        sData_Length = len(comando)
        sVariable = sStation_Id + chr(sData_Length) + comando

        # String a Enviar. Paquete binario MultiISO:
        # StartTX + Station ID + Data Length + command + paridad + EndTX
        request = sSTX + sVariable + msg2bcc(sVariable) + sETX

        # Inicializo el reloj de timeout
        inicio = actual = time.time()
        self._ser.flushInput() # Borro el buffer de entrada
        self._ser.write(request) # Envio el comando

        while self._ser.inWaiting() < 3 and actual < inicio + 1:
            actual = time.time()

        rEncabezado = self._ser.read(3)
        if not rEncabezado: # No leí nada del serial, hay un lector ahí?
            return None
        #rSTX = rEncabezado[0] # Not used
        #rStation_Id = rEncabezado[1] # Not used
        rData_Length = ord(rEncabezado[2])

        # Leer el resto del mensaje que va a ser de rData_Length + 2
        inicio = actual = time.time()
        while self._ser.inWaiting() < rData_Length + 2 and actual < inicio + 1:
            actual = time.time()

        rData = self._ser.read(rData_Length + 2)
        return rData[:-2]

    def leer_bloque(self, tag, nro_bloque):
        """ Envía al lector el comando para leer un bloque del tag y retorna su
            valor como string
        """
        return self._enviar_comando('rb' + chr(nro_bloque))

    def leer_bloques(self, tag, nro_bloque, cantidad):
        """ Envía al lector el comando para leer N bloques del tag y retorna su
            valor como string
        """
        datos=''
        for i in range(nro_bloque, nro_bloque+cantidad):
            datos = datos + self.leer_bloque(tag, i)
        return datos

    def escribir_bloque(self, tag, nro_bloque, valor):
        """ Envía al lector el comando para escribir en un bloque del tag el
            valor que se pasa como parámetro.
        """
        return self._enviar_comando('wb' + chr(nro_bloque) + valor)

    def is_read_only(self, tag):
        """ Chequea que si el tag en cuestión es de sólo lectura o no.
            Devuelve True en caso de que sea sólo lectura, False en caso
            contrario.
        """
        if tag.clase == CLASE_ICODE:
            bloque = self.leer_bloque(tag, tag.BLOQUE_WAC)
            return bloque == '\x00' * tag.BYTES_POR_BLOQUE
        else:
            # TODO: Implementar para ICODE2
            raise TAGError('Funcion no implementada para este chip en este ' \
                           'lector')

    def set_read_only(self, tag):
        """ Setea el tag en cuestión como de sólo lectura """
        if tag.clase == CLASE_ICODE:
            # Escribe el bloque 02 con \x00 cada byte para poner el TAG en read
            # only si marca=read only
            self.escribir_bloque(tag.BLOQUE_WAC, '\x00' * tag.BYTES_POR_BLOQUE)
            return True
        else:
            # TODO: Implementar para ICODE2
            raise TAGError('Función no implementada para este chip en este ' \
                           'lector')
