# coding: utf-8
""" Módulo que implementa el manejo del Lector TRF7960 de Texas Instruments """

from msa import get_logger
from msa.core.settings import TOKEN


logger = get_logger("core")


class LectorDummy(object):
    """ Clase que controla el Lector TRF7960 de Texas Instruments """

    SOF = '01'
    Data_Length = '0000'
    Reader_Type = '03'
    Entity = '04'
    EOF = '0000'
    Base_Length = 7 # Suma de bytes de todos los campos anteriores
    MAX_BUFFER = 1024

    TAG_TEXAS = 0

    def __init__(self, token_id=TOKEN, comprobar_tag=True):
        # El timeout minimo que tiene el firmware es 60ms con lo cual no
        # debería ser menor a eso.
        self.timeout = 0.1

    def _configurar_puerto(self):
        pass

    def conectar(self):
        return True

    def desconectar(self):
        pass

    def _inicializar(self):
        return True

    def get_tag(self):
        pass

    def _enviar_comando(self, comando):
        pass

    def leer_bloque(self, tag, nro_bloque):
        pass

    def leer_bloques(self, tag, nro_bloque, cantidad):
        pass

    def escribir_bloque(self, tag, nro_bloque, valor):
        pass

    def is_read_only(self, tag):
        return False

    def _set_read_only(self, tag, nro_bloque):
        return True

    def set_read_only(self, tag):
        return True
