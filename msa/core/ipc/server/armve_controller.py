"""Controlador para el ARMVEService."""
from base64 import b64decode, b64encode
from codecs import encode
from json import dumps, loads
from time import sleep

from gi.repository.GObject import timeout_add
from PIL import Image

from msa.core.armve.constants import AUTOFEED_SELECT, BLOQUES_TAG, MSG_ERROR
from msa.core.armve.helpers import array_to_printable_string
from msa.core.documentos.actas import Apertura, Autoridad, Recuento
from msa.core.documentos.boletas import Seleccion
from msa.core.imaging.imagen_prueba import ImagenPrueba
from msa.core.logging import get_logger
from msa.core.rfid.constants import (NO_TAG, TAGS_ADMIN, TAG_ADMIN, TAG_DATOS,
                                     TAG_COLISION, TAG_VACIO, CLASE_ICODE2,
                                     TIPOS_TAGS, TIPOS_TAGS_REV,
                                     COD_TAG_DESCONOCIDO, TAG_VOTO,
                                     TAG_RECUENTO, COD_TAG_RECUENTO,
                                     COD_TAG_INICIO, COD_TAG_ADDENDUM)
from msa.core.settings import TOKEN, COMPROBAR_TOKEN
from msa.settings import QUEMA
from six.moves import range


logger = get_logger("armve_controller")


class ARMVEController(object):

    """Controlador para el ARMVEService."""

    def __init__(self, parent):
        """Constructor para el Controlador.

        Argumentos:
            parent -- el servicio.
        """
        self.parent = parent
        self._getting_tag_data = False
        self._buffering = False
        self._print_on_finish = False

    def tag_leido(self, response):
        """Devuelve el tag leido.

        Argumentos:
            response -- respuesta recibida del evento.
        """
        self.parent.encender_monitor()
        tipo, tag = self.get_tag(response)
        return tipo, dumps(tag)

    def _get_tag_response(self, response, index=0, multi=False):
        """Obtiene y formatea la respuesta del tag.

        Argumentos:
            response -- respuesta.
            index -- qué numero de tag queremos leer en la lista.
            multi -- Si queremos leer un "miltitag"
        """
        tag = None
        tipo = NO_TAG
        serial = response['serial_number'][index]
        if multi:
            data = self.parent.rfid.get_multitag_data()
        else:
            func = self.parent.rfid.get_tag_data
            data = func(serial,
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

            if len(data["user_data"]) == 0:
                data["user_data"] = ""

            if data["user_data"] == "":
                _tag_data = ""
            else:
                _tag_data = b64encode(data['user_data']).decode()

            tag = {"serial": self._get_normalized_serial(serial),
                   "token": self._get_normalized_token(data['token']),
                   "datos": _tag_data,
                   "tipo": tipo_tag,
                   "clase": CLASE_ICODE2,
                   "reception_level": response['reception_level'][index][0]
                   }
        return tipo, tag

    def get_tag(self, response=None):
        """Obtiene el contenido del tag.

        Argumentos:
        response -- respuesta del RFID.
        """
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
        """Obtiene la metadata del tag."""
        tag_meta = None
        tags = self.parent.rfid.get_tags()
        if tags is not None:
            tags = tags[0]
        if tags:
            if tags['number'] == 1:
                serial = tags['serial_number'][0]
                data = self.parent.rfid.read_block(serial, 0)
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
        """Dado un numero de serie de chip en un lista de decimales.

        Argumentos:
            serial - el numero de serie
        Devuelve el mismo en string formateado.
            In:  [224, 4, 1, 0, 126, 33, 8, 141]
            Out: "E00401007E21088D"
        """
        return encode(serial, "hex_codec").decode()

    def _get_normalized_token(self, token):
        """
        Dado un token tipo string en hexa lo formatea y lo deja en mayúscula.
        """
        return hex(token)[2:].upper()

    def _check_data(self, serial, data, tipo, multi_tag=False):
        """Chequea que el tag esté correctamente escrito."""
        # Tengo que esperar un poco por que es lo que tarda en responder el ARM
        sleep(0.1)
        # si tengo FALLBACK_2K en un recuento voy a leer mas de un tag, no es
        # lo usual
        if multi_tag:
            written_data = self.parent.rfid.get_multitag_data()
        else:
            written_data = self.parent.rfid.get_tag_data(serial)

        # Comparo que ell tag sea valido y que la data que estoy queriendo
        # guardar es igual a la que leí
        ret = written_data is not None and data == written_data['user_data']
        return ret

    def write(self, serial, tipo, data, marcar_ro):
        """Escribe un tag.

        Argumentos:
            serial -- el numero de serioe del tag.
            tipo -- tipo de tag a guardar
            data -- datos que queremos guardar en el tag.
            marcar_ro -- un booleano que expresa si queremos quemar el tag.
        """
        success = False
        rfid = self.parent.rfid
        # transformamos el tipo de tag en su version binaria
        tipo = TIPOS_TAGS_REV[tipo]
        # comprobamos que ningun sector del chip no esté quemado
        readonly = self._tag_readonly(serial)
        if not readonly:
            # traemos el header
            header_data = rfid.read_block(serial, 0)
            # nos aseguramos de que el tag esté presente y que no hubo ningún
            # error de lectura
            if header_data is not None and header_data[3] != MSG_ERROR:
                # vamos a intentar grabar el tag tres veces, sino asumimos que
                # no se puede grabar
                retries_left = 3
                while not success and retries_left:
                    # Grabo el tag
                    multi_tag = rfid.write_tag(serial, tipo, TOKEN, data)
                    # Chequeo la data a ver si se grabó bien. Si la data que
                    # quise grabar es diferente intento de nuevo
                    success = self._check_data(serial, data, tipo, multi_tag)
                    retries_left -= 1
                # si la grabacion fue un exito voy a quermarlo
                if success and marcar_ro:
                    # si lo grabé con el fallback de los 2 chips de 1k quemo
                    # todos los tags. Esto no pasa en elecciones normales.
                    if multi_tag:
                        tags = rfid.get_tags()[0]['serial_number']
                        # Quemo cada uno de los tags
                        for serial in tags:
                            rfid.quemar_tag(serial)
                    else:
                        # Quemo el tag
                        rfid.quemar_tag(serial)
        return success

    def _tag_readonly(self, serial):
        """
        Indica si ninguno de los bloques del tag es readonly.

        Argumentos:
            serial -- el serial del tag del cual quiero averiguar el estado.
        """
        data = self.parent.rfid.is_read_only(serial, 0, BLOQUES_TAG - 1)
        if data is not None and data[3] != MSG_ERROR:
            for element in data[0]:
                if element['byte']:
                    return True
        return False

    def con_tarjeta(self, response):
        """Formatea el output de tarjeta (papel) nueva."""
        # esto tiene que devolver una lista
        self.parent.encender_monitor()
        return [response]

    def insertando_papel(self, response):
        """Formatea el output de insertando papel."""
        return [response]

    def autofeed_end(self, response):
        """Formatea el output de autofeed end."""
        return [response]

    def print_image(self, filepath, mode, size, transpose, only_buffer):
        """Imprime una imagen.

        Argumentos:
        filepath -- path de la imagen a imprimir.
        mode -- modo de la imagen.
        size -- tamaño.
        transpose -- si damos vuelta o no.
        only_buffer -- booleano. si es True no imprime la imagen, solo buferea.
        """
        self._buffering = True
        self.parent.printing = True
        image_file = open(filepath, "rb")
        data = image_file.read()
        image = Image.frombytes(mode, size, data)
        if transpose:
            image = image.transpose(Image.ROTATE_90)

        data = image.convert("L").getdata()
        if self.parent.impresion_v2:
            width, height = image.size
            self.parent.printer.load_buffer_compressed_full(
                data, self.parent._free_page_mem, width, height,
                print_immediately=not only_buffer)
        else:
            self.parent.printer.load_buffer_compressed(
                data, self.parent._free_page_mem,
                print_immediately=not only_buffer)
        self._buffering = False

    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer=False,
                             extra_data=None):
        """Registra un documento que fue enviado serializado via d-bus.

        Argumentos:
            tipo_tag -- el tipo de documento que queremos registrar. Puede ser:
                (Seleccion, Apertura, Recuento o Prueba)
            tag -- Contenido del tag serializado.
            transpose -- transpone la imagen.
            only_buffer -- Solo guarda en el buffer, no imprime.
            extra_data -- datos extra que queremos imprimir pero que no se
            guardan en el chip.
        """
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
            image = ImagenPrueba().render_image()

        image = image.convert('L')
        if transpose:
            image = image.transpose(Image.ROTATE_270)
        if only_buffer:
            if self.parent.impresion_v2:
                self.parent.printer.register_load_buffer_compressed_full()
            else:
                self.parent.printer.register_load_buffer_compressed()
        else:
            self.parent.printer.register_print_finished()
        data = image.getdata()
        if self.parent.impresion_v2:
            width, height = image.size
            self.parent.printer.load_buffer_compressed_full(
                data, self.parent._free_page_mem, width, height,
                print_immediately=not only_buffer)
        else:
            self.parent.printer.load_buffer_compressed(
                data, self.parent._free_page_mem,
                print_immediately=not only_buffer)

    def registrar(self, tag, solo_impimir=False, crypto_tag=None):
        """Registra un voto.

        Argumentos:
            tag -- el voto a registrar serializado como tag.
            solo_impimir -- no guarda el tag, solo imprime.
        """
        ret = {"status": "OK"}
        marcar_ro = QUEMA

        if solo_impimir:
            tag_guardado = True
        else:
            if crypto_tag is None:
                crypto_tag = tag

            tag_guardado = self.guardar_tag(TAG_VOTO, crypto_tag, marcar_ro)

        if tag_guardado:
            def _inner():
                seleccion = Seleccion.desde_string(tag)
                self.imprimir_serializado("Seleccion", seleccion, True)
            timeout_add(10, _inner)
        else:
            ret['status'] = "TAG_NO_GUARDADO"

        return dumps(ret)

    def do_print(self):
        """Ejecuta la impresion propiamente dicha.

        Llama al comando do_print del protocolo armve.
        """
        if self._buffering:
            self._print_on_finish = True
        else:
            self.parent.printing = True
            self.parent.printer.register_print_finished()
            sleep(0.1)
            self.parent.printer.do_print()

    def buffer_loaded(self, response):
        """Se ejecuta cuando se terminó de cargar el buffer."""
        self._buffering = False
        if self._print_on_finish:
            self.do_print()

        self._print_on_finish = False

    def boleta_expulsada(self, response):
        """Respuesta al evento de boleta expulsada."""
        self.parent.printer.clear_buffer()
        status = {
            "sensor_1": 0,
            "sensor_2": 0,
            "sensor_3": 0
        }
        self.parent.con_tarjeta(status)
        self.parent.printing = False
        return []

    def guardar_tag(self, tipo_tag, data, marcar_ro):
        """Guarda un tag.

        Argumentos:
            tipo_tag -- el tipo de tag a guuardar.
            data -- el contenido del tag a guardar.
            marcar_ro -- quema el tag.
        """
        guardado = False
        try:
            if self.parent.printer.is_paper_ready():
                tags = self.parent.rfid.get_tags()
                if tags is not None and tags[0] is not None and \
                        ((tipo_tag != TAG_RECUENTO and tags[0]["number"] == 1)
                         or tipo_tag == TAG_RECUENTO):
                    serial_number = tags[0]["serial_number"][0]
                    guardado = self.write(serial_number, tipo_tag, data,
                                          marcar_ro)
        except Exception as e:
            logger.exception(e)
        return guardado

    def pir_detected_cb(self, response):
        """Se lanza cuando se recibe el evento de pir detectado."""
        if response:
            self.parent.encender_monitor()

    def pir_not_detected_cb(self, response):
        """Se lanza cuando se recibe el evento de pir no detectado."""
        if response:
            self.parent.reset_off_counter()

    def set_tipo(self, serial, tipo):
        """Cambia el tipo de tag del espacion de usuario del tag."""
        if tipo not in TIPOS_TAGS_REV:
            return
        tipo = TIPOS_TAGS_REV[tipo]
        metadata = self.parent.rfid.read_block(serial, 0)
        metadata_array = bytearray(metadata[0]['bytes'])
        metadata_array[1] = tipo
        self.parent.rfid.write_block(serial, 0, metadata_array)

    def get_map(self):
        """Devuelve el mapa completo del tag."""
        response = self.parent.rfid.get_tags()[0]
        dmp = []
        if response is not None and response['number'] == 1:
            serial = response['serial_number'][0]
            retries = 5
            bloques = []
            while retries > 0:
                rfid_data = self.parent.rfid.read_blocks(serial, 0,
                                                         BLOQUES_TAG-1)
                if rfid_data is None or rfid_data[3] == MSG_ERROR:
                    retries -= 1
                    continue
                retries = 0
                for block in rfid_data[0]:
                    bloques.extend(block['bytes'])
                for i in range(0, BLOQUES_TAG):
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
        return dumps(dmp)

    def set_fan_auto_mode(self, value):
        """Establece el automodo de los fans."""
        self.parent._fan_auto_mode = value
        if value:
            self.parent._last_speed = -1

    def set_pir_mode(self, mode):
        """Establece el modo del pir."""
        self.parent._usa_pir = mode
        self.parent.reset_off_counter()

    def get_power_source_cb(self, response):
        """Se ejecuta cuando se refibe el evento de power source."""
        self.parent._ac_power_source = not response['byte']

    def power_source_change(self, value):
        """Se ejecuta cuando cambia la fuente de energia.

        Argumentos:
            value -- True para AC, False para baterias
        """
        self._ac_power_source = value
        if self._ac_power_source:
            self.parent.encender_monitor()
        else:
            self.parent.reset_off_counter()

    def set_autofeed_mode(self, mode):
        """Establece el modo de autofeed."""
        if mode == AUTOFEED_SELECT:
            self.parent._set_autofeed()
        else:
            self.parent.printer.set_autofeed(mode)

    def reset_device(self, data):
        """Callback cuando se resetea un dispositivo."""
        return [data['byte']]
