# coding: utf-8

from json import dumps, loads
from base64 import b64encode, b64decode
from PIL import Image
from time import sleep

from msa import get_logger
from msa.core.armve.constants import MSG_ERROR, AUTOFEED_SELECT
from msa.core.armve.settings import FALLBACK_2K
from msa.core.armve.helpers import array_to_string, array_to_printable_string
from msa.core.clases import Seleccion, Apertura, Autoridad, Recuento
from msa.core.imaging import ImagenPrueba
from msa.core.rfid.constants import NO_TAG, TAGS_ADMIN, TAG_ADMIN, TAG_DATOS, \
    TAG_COLISION, TAG_VACIO, CLASE_ICODE2, TIPOS_TAGS, TIPOS_TAGS_REV, \
    COD_TAG_DESCONOCIDO, TAG_VOTO, TAG_RECUENTO, COD_TAG_RECUENTO, \
    COD_TAG_INICIO, COD_TAG_ADDENDUM
from msa.core.settings import TOKEN, COMPROBAR_TOKEN
from msa.settings import QUEMA


logger = get_logger("armve_controller")


class ARMVEController(object):
    def __init__(self, parent):
        self.parent = parent
        self._getting_tag_data = False
        self._buffering = False
        self._print_on_finish = False

    def tag_leido(self, response):
        self.parent.encender_monitor()
        tipo, tag = self.get_tag(response)
        return tipo, dumps(tag)

    def _get_tag_response(self, response, index=0, multi=False):
        tag = None
        tipo = NO_TAG
        serial = response['serial_number'][index]
        if multi:
            data = self.parent.rfid.get_multitag_data()
        else:
            func = self.parent.rfid.get_tag_data
            data = func(array_to_string(serial),
                        comprobar_token=COMPROBAR_TOKEN)

        if data is not None:
            if data['tipo_tag'] in TIPOS_TAGS:
                tipo_tag = TIPOS_TAGS[data['tipo_tag']]
            else:
                tipo_tag = TIPOS_TAGS[COD_TAG_DESCONOCIDO]

            if tipo_tag in TAGS_ADMIN:
                tipo = TAG_ADMIN
            else:
                if data['user_data'] == "":
                    tipo = TAG_VACIO
                else:
                    tipo = TAG_DATOS
            tag = {"serial": self._get_normalized_serial(serial),
                   "token": self._get_normalized_token(data['token']),
                   "datos": b64encode(data['user_data']),
                   "tipo": tipo_tag,
                   "clase": CLASE_ICODE2,
                   "reception_level": response['reception_level'][index][0]
                   }
        return tipo, tag

    def get_tag(self, response=None):
        tipo = NO_TAG
        tag = None
        if response is None and hasattr(self.parent, "rfid"):
            response = self.parent.rfid.get_tags()
            if response is not None:
                response = response[0]
        if response is not None:
            if response['number'] == 1:
                tipo, tag = self._get_tag_response(response)
            elif response['number'] > 1:
                tipo = TAG_COLISION
                tipos_tags = self.parent.rfid.get_tipos_tags(response)
                tipos = [tipo_[0] for tipo_ in tipos_tags]
                tag = {"tipo": tipos,
                       "datos": ''}
                if COD_TAG_RECUENTO in tipos:
                    for index, datos_tag in enumerate(tipos_tags):
                        tipo_, tag_ = self._get_tag_response(response, index)
                        if tipo_ == TAG_DATOS and tag_['tipo'] == TAG_RECUENTO:
                            tipo = tipo_
                            tag = tag_
                            break
                        else:
                            sleep(0.1)
                elif len(tipos) == 2:
                    tipos = sorted(tipos)
                    if tipos == [COD_TAG_INICIO, COD_TAG_ADDENDUM]:
                        tipo, tag = self._get_tag_response(response,
                                                           multi=True)
        return tipo, tag

    def get_tag_metadata(self):
        tag_meta = None
        tags = self.parent.rfid.get_tags()
        if tags is not None:
            tags = tags[0]
        if tags:
            if tags['number'] == 1:
                serial = tags['serial_number'][0]
                data = self.parent.rfid.read_block(array_to_string(serial), 0)
                if data:
                    data = list(data[0]['bytes'])
                    if data[1] in TIPOS_TAGS:
                        tipo_tag = TIPOS_TAGS[data[1]]
                    else:
                        tipo_tag = TIPOS_TAGS[COD_TAG_DESCONOCIDO]

                    tag_meta = {'serial': self._get_normalized_serial(serial),
                                'token': self._get_normalized_token(data[0]),
                                'tipo': tipo_tag,
                                'longitud': data[2:],
                                'clase': CLASE_ICODE2,
                                'reception_level':
                                tags['reception_level'][0][0]
                                }
        return tag_meta

    def _get_normalized_serial(self, serial):
        """ Dado un numero de serie de chip en un lista de decimales,
        devuelve el mismo en string formateado.
            In:  [224, 4, 1, 0, 126, 33, 8, 141]
            Out: "E00401007E21088D"
        """
        #return "".join([hex(x)[2:].zfill(2).upper() for x in serial])
        return array_to_printable_string(serial)

    def _get_normalized_token(self, token):
        """ Dado un token tipo string en hexa lo formatea y lo deja en
        mayúscula
        """
        return hex(token)[2:].upper()

    def _check_data(self, serial, data, tipo, multi_tag=False):
        sleep(0.1)
        if multi_tag:
            written_data = self.parent.rfid.get_multitag_data()
        else:
            written_data = self.parent.rfid.get_tag_data(serial)

        ret = written_data is not None and (
              data == written_data['user_data'] or
              (written_data['user_data'] == "" and not FALLBACK_2K))
        return ret

    def write(self, serial, tipo, data, marcar_ro):
        success = False
        serial = array_to_string(serial)
        tipo = TIPOS_TAGS_REV[tipo]
        header_data = self.parent.rfid.read_block(serial, 0)
        if header_data is not None and header_data[3] != MSG_ERROR:
            retries_left = 3
            while not success and retries_left:
                multi_tag = self.parent.rfid.write_tag(serial, tipo, TOKEN,
                                                       data)
                success = self._check_data(serial, data, tipo, multi_tag)
                retries_left -= 1
            if success and marcar_ro:
                if multi_tag:
                    tags = self.parent.rfid.get_tags()[0]['serial_number']
                    for serial in tags:
                        self.parent.rfid.quemar_tag(serial)
                else:
                    self.parent.rfid.quemar_tag(serial)
        return success

    def con_tarjeta(self, response):
        # esto tiene que devolver una lista
        self.parent.encender_monitor()
        #status = self.parent.printer.has_paper()
        return [response ]

    def insertando_papel(self, response):
        return [response]

    def autofeed_end(self, response):
        return [response]

    def print_image(self, filepath, mode, size, transpose, only_buffer):
        # TODO: Eliminar este método
        self._buffering = True
        self.parent.printing = True
        image_file = open(filepath)
        data = image_file.read()
        image = Image.fromstring(mode, size, data)
        if transpose:
            image = image.transpose(Image.ROTATE_90)

        data = image.getdata()
        self.parent.printer.load_buffer_compressed(
            data, self.parent._free_page_mem,
            print_immediately=not only_buffer)
        self._buffering = False

    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer=False,
                             extra_data=None):
        self._buffering = True
        if tipo_tag == "Seleccion":
            if type(tag) == Seleccion:
                boleta = tag
            else:
                boleta = Seleccion.desde_string(tag)
            image = boleta.a_imagen()
        elif tipo_tag == "Apertura":
            boleta = Apertura.desde_tag(b64decode(tag))
            image = boleta.a_imagen()
        elif tipo_tag == "Recuento":
            boleta = Recuento.desde_tag(b64decode(tag))
            extra_data = loads(extra_data)
            autoridades = extra_data.get('autoridades')
            if autoridades is not None and len(autoridades):
                boleta.autoridades = [Autoridad.desde_dict(aut) for aut
                                      in autoridades]
            boleta.hora = extra_data['hora']
            image = boleta.a_imagen(extra_data['tipo_acta'])
        elif tipo_tag == "Prueba":
            image = ImagenPrueba(hd=True).render_image()

        image = image.convert('L')
        if transpose:
            image = image.transpose(Image.ROTATE_270)
        if only_buffer:
            self.parent.printer.register_load_buffer_compressed()
        else:
            self.parent.printer.register_print_finished()
        data = image.getdata()
        self.parent.printer.load_buffer_compressed(
            data, self.parent._free_page_mem,
            print_immediately=not only_buffer)

    def registrar(self, tag):
        ret = {"status": "OK"}
        marcar_ro = QUEMA

        tag_guardado = self.guardar_tag(TAG_VOTO, tag, marcar_ro)
        if tag_guardado:
            seleccion = Seleccion.desde_string(tag)
            self.imprimir_serializado("Seleccion", seleccion, True)
        else:
            ret['status'] = "TAG_NO_GUARDADO"

        return dumps(ret)

    def do_print(self):
        if self._buffering:
            self._print_on_finish = True
        else:
            self.parent.printing = True
            self.parent.printer.register_print_finished()
            sleep(0.1)
            self.parent.printer.do_print()

    def buffer_loaded(self, response):
        self._buffering = False
        if self._print_on_finish:
            self.do_print()

        self._print_on_finish = False

    def boleta_expulsada(self, response):
        self.parent.printer.clear_buffer()
        status = {"paper_out_1": 0, "paper_out_2": 0}
        self.parent.con_tarjeta(status)
        self.parent.printing = False
        return []

    def guardar_tag(self, tipo_tag, data, marcar_ro):
        guardado = False
        try:
            if self.parent.printer.has_paper():
                tags = self.parent.rfid.get_tags()
                if tags is not None and tags[0] is not None and \
                        ((tipo_tag != TAG_RECUENTO and tags[0]["number"] == 1)
                         or tipo_tag == TAG_RECUENTO):
                    serial_number = tags[0]["serial_number"][0]
                    guardado = self.write(serial_number, tipo_tag, data,
                                          marcar_ro)
        except Exception, e:
            logger.exception(e)
        return guardado

    def pir_detected_cb(self, response):
        if response:
            self.parent.encender_monitor()

    def pir_not_detected_cb(self, response):
        if response:
            self.parent.reset_off_counter()

    def set_tipo(self, serial, tipo):
        if tipo not in TIPOS_TAGS_REV:
            return
        serial = array_to_string(serial)
        tipo = TIPOS_TAGS_REV[tipo]
        metadata = list(self.parent.rfid.read_block(serial, 0)[0]['bytes'])
        metadata[1] = tipo
        self.parent.rfid.write_block(serial, 0, metadata)

    def get_map(self):
        response = self.parent.rfid.get_tags()[0]
        dmp = []
        if response is not None and response['number'] == 1:
            serial = array_to_string(response['serial_number'][0])
            retries = 5
            bloques = []
            while retries > 0:
                rfid_data = self.parent.rfid.read_blocks(serial, 0, 27)
                if rfid_data is None or rfid_data[3] == MSG_ERROR:
                    retries -= 1
                    continue
                retries = 0
                for block in rfid_data[0]:
                    bloques.extend(block['bytes'])
                for i in range(0, 28):
                    offset = i * 4
                    bloque = bloques[offset:offset + 4]
                    hexa = array_to_printable_string(bloque, ' ')
                    hexa2 = hexa3 = ''
                    for c in bloque:
                        # Me fijo si es imprimible
                        if c >= 32 and c <= 126:
                            hexa2 += chr(c)
                        else:
                            hexa2 += '.'
                        hexa3 += str(c).zfill(3) + ' '
                    dmp.append('Block %02d: %s | %s | %s' % (i, hexa, hexa2,
                                                             hexa3))
        return dumps(dmp, encoding='latin-1')

    def set_fan_auto_mode(self, value):
        self.parent._fan_auto_mode = value
        if value:
            self.parent._last_speed = -1

    def set_pir_mode(self, mode):
        self.parent._usa_pir = mode
        self.parent.reset_off_counter()

    def get_power_source_cb(self, response):
        self.parent._ac_power_source = not response['byte']

    def power_source_change(self, value):
        #True = AC, False = baterias
        self._ac_power_source = value
        if self._ac_power_source:
            self.parent.encender_monitor()
        else:
            self.parent.reset_off_counter()

    def manual_feed(self, value):
        self.parent.printer.move(-120)

    def set_autofeed_mode(self, mode):
        if mode == AUTOFEED_SELECT:
            self.parent._set_autofeed()
        else:
            self.parent.printer.set_autofeed(mode)

    def reset_device(self, data):
        return [data['byte']]
