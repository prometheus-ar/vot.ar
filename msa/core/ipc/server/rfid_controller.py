# -*- coding: utf-8 -*-


import json
import time
import traceback

from base64 import b64decode, b64encode
from msa import get_logger

from msa.core.serial.rfid import get_lector, TAGError, SerialException
from msa.core.rfid.constants import CLASE_ICODE, CLASE_ICODE2, \
    TAGS_ADMIN, TAG_ADMIN, TAG_DATOS, TAG_VACIO, TAG_ERROR, CNX_ERROR, \
    TAG_COLISION, NO_TAG, TAG_INICIO, TAG_ADDENDUM, TAG_RECUENTO, \
    TAG_NO_ENTRA
from msa.core.serial.rfid.helpers import str2hexa2


logger = get_logger("core")


class RFIDController(object):
    """ Modulo que maneja el lector RFID.

        No esta hecho para ser usado directamente, sino para ser usado por los
        modulos que necesiten usar el lector rfid en modo automatico (ie. DBUS)
    """

    # Constantes usadas para consultar el tipo de tag detectado.

    NO_TAG = NO_TAG
    TAG_VACIO = TAG_VACIO
    TAG_DATOS = TAG_DATOS
    TAG_ERROR = TAG_ERROR
    TAG_COLISION = TAG_COLISION
    CNX_ERROR = CNX_ERROR

    def __init__(self, callback):
        """Constructor"""
        self.callback = callback
        self.loop_lector = True
        self.lector = get_lector()
        self._inicializar_lector()
        self.ultimo_tag = None

    def _inicializar_lector(self):
        self.lector = get_lector()
        try:
            # Al conectar hay un chequeo, primero por si no hay nada, y segundo
            # por si hay otro dispositivo
            # Si no hay nada, conectar() lanza la exception y si no está el
            # dispositivo esperado devuelve False
            if not self.lector.conectar():
                self.lector = None
        except SerialException:
            self.lector = None

    def _get_tag(self, obj=False):
        """
        Hace 2 intentos para detectar un TAG en el caso de alguna excepción
        intenta reconectar el lector.
        """
        for i in range(4):
            try:
                tags = self.lector.get_multitag()
                if len(tags) == 0:
                    tag = None
                elif len(tags) == 2:
                    tipos = sorted([tag_.get_tipo() for tag_ in tags])
                    if tipos == [TAG_VACIO, TAG_VACIO]:
                        tag = {"tipo": [0, 0],
                               "datos": '',
                               "clase": CLASE_ICODE2,
                               "serial": tags[0].get_serial()}
                    elif tipos == [TAG_INICIO, TAG_ADDENDUM]:
                        tag = tags[0].to_dict()
                        tag2 = tags[1].to_dict()
                        tag['datos'] = b64encode(b64decode(tag['datos']) +
                                                 b64decode(tag2['datos']))
                        tag['tipo'] = TAG_RECUENTO
                    else:
                        tag = self.lector.get_tag()
                elif tags is not None:
                    tag = tags[0]
                else:
                    tag = None

                if tag is not None and not obj and type(tag) != dict:
                    tag = tag.to_dict()

                return tag
            except Exception, e:
                print e
                try:
                    self._inicializar_lector()
                except:
                    time.sleep(self.lector.get_timeout())
        return None

    def consulta_lector(self, callback):
        """ Callback que es llamado en un intervalo regular.
            Consulta el lector a ver si hay algún tag, si es así
            llama a la función de callback que se registra en el Módulo.
        """
        if self.lector is None or self.loop_lector is False:
            return
        try:
            tag = self._get_tag()
            if tag is None:
                if self.ultimo_tag != tag:
                    callback(self.NO_TAG, json.dumps(tag))
                    self.ultimo_tag = tag
            else:
                try:
                    tag_dict = tag
                    tag_json = json.dumps(tag_dict, encoding='latin-1')
                except TAGError:
                    # Paso silencioso, en la proxima vuelta responderá 'nuevo
                    # tag' o 'sin tag'.
                    tag_json = None
                else:
                    if tag_dict is not None:
                        este_tag = tag_dict['serial']
                        if self.ultimo_tag != este_tag:
                            tipo_tag = tag_dict['tipo']
                            datos_tag = tag_dict['datos']
                            if tipo_tag in TAGS_ADMIN:
                                self.ultimo_tag = este_tag
                                callback(TAG_ADMIN, tag_json)
                            # Valido que tipo_tag no es None para asegurar la
                            # lectura completa
                            elif datos_tag != '' and tipo_tag is not None:
                                self.ultimo_tag = este_tag
                                callback(TAG_DATOS, tag_json)
                            elif tipo_tag == [0, 0]:
                                self.ultimo_tag = este_tag
                                callback(self.TAG_COLISION, tag_json)
                            elif datos_tag == '' and tipo_tag is not None:
                                self.ultimo_tag = este_tag
                                callback(TAG_VACIO, tag_json)
                            else:
                                logger.error(tipo_tag)
                                logger.error(datos_tag)
                                callback(TAG_ERROR)
        except TAGError:
            logger.error("TAGERROR")
            # Si hay un error al leer los datos del tag, llamo al
            # callback y salgo del ciclo.
            callback(self.TAG_COLISION)
        except Exception as e:
            print(traceback.print_exc())
            logger.exception(e)
            callback(CNX_ERROR)

        return self.loop_lector

    def get_tag(self):
        try:
            tag = self._get_tag()
            if tag is None:
                return tag
        except:
            return None
        return json.dumps(tag, encoding='utf-8')

    def get_map(self):
        tag = self._get_tag()
        dmp = []
        if tag:
            if tag.clase == CLASE_ICODE or tag.clase == CLASE_ICODE2:
                bloques = tag.lee_bloques(0, tag.MAX_BLOQUE)
                for i in range(0, tag.MAX_BLOQUE + 1):
                    offset = i * tag.BYTES_POR_BLOQUE
                    bloque = bloques[offset:offset + tag.BYTES_POR_BLOQUE]
                    hexa = str2hexa2(bloque)
                    hexa2 = hexa3 = ''
                    for c in bloque:
                        # Me fijo si es imprimible
                        if ord(c) >= 32 and ord(c) <= 126:
                            hexa2 += c
                        else:
                            hexa2 += '.'
                        hexa3 += str(ord(c)).zfill(3) + ' '
                    dmp.append('Block %02d: %s | %s | %s' % (i, hexa, hexa2,
                                                             hexa3))

        return json.dumps(dmp, encoding='latin-1')

    def write(self, serial, tipo, data, marcar_ro=False):
        try:
            if tipo == TAG_RECUENTO:
                tags = self.lector.get_multitag()
                if len(data) <= 104:
                    tags[0].escribe_datos(data, tipo, marcar_ro)
                else:
                    tags[0].escribe_datos("", TAG_NO_ENTRA, marcar_ro)

                """
                else:
                    if len(tags) == 2:
                        data_chip_1 = data[:104]
                        tags[0].escribe_datos(data_chip_1, TAG_INICIO,
                                              marcar_ro)
                        data_chip_2 = data[104:]
                        tags[1].escribe_datos(data_chip_2, TAG_ADDENDUM,
                                              marcar_ro)
                """
            else:
                tag = self._get_tag(obj=True)
                if tag.get_serial() == serial:
                    tag.escribe_datos(data, tipo, marcar_ro)
        except Exception, e:
            print(traceback.print_exc())
            logger.error(">>>%s" % e)

    def is_read_only(self, serial):
        try:
            tag = self._get_tag()
            if tag.get_serial() == serial:
                return tag.read_only()
        except Exception, e:
            logger.error(">>>%s" % e)

    def set_tipo(self, serial, tipo):
        try:
            tag = self._get_tag()
            if tag.get_serial() == serial:
                return tag.set_tipo(tipo.encode('utf-8'))
        except Exception, e:
            logger.exception(e)

    def get_tag_metadata(self):
        tag_meta = None
        try:
            tag = self._get_tag()
            if tag:
                if type(tag) != dict:
                    tag_meta = tag.to_dict()
                else:
                    tag_meta = tag
        except Exception, e:
            logger.error(">>>%s" % e)
        return tag_meta
