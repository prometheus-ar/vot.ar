"""Controlador para el ARMVEService."""
from base64 import b64decode, b64encode
from codecs import encode
from ujson import dumps, loads
from time import sleep

from gi.repository.GObject import timeout_add
from PIL import Image

from msa.core.armve.constants import AUTOFEED_SELECT, BLOQUES_TAG, MSG_ERROR
from msa.core.armve.helpers import array_to_printable_string
from msa.core.crypto import encriptar_voto
from msa.core.documentos.actas import (Apertura, Autoridad, Recuento,
                                       Totalizacion)
from msa.core.documentos.boletas import Seleccion
from msa.core.imaging.imagen_prueba import ImagenPrueba
from msa.core.logging import get_logger
from msa.core.rfid.constants import (CLASE_ICODE2, COD_TAG_DESCONOCIDO,
                                     COD_TAG_RECUENTO, NO_TAG, TAG_ADMIN,
                                     TAG_COLISION, TAG_DATOS, TAG_RECUENTO,
                                     TAG_VACIO, TAG_VOTO, TAGS_ADMIN,
                                     TIPOS_TAGS, TIPOS_TAGS_REV,
                                     COD_TAG_NO_ENTRA)
from msa.core.settings import COMPROBAR_TOKEN, TOKEN
from msa.settings import QUEMA, MODO_DEMO
from six.moves import range


logger = get_logger("armve_controller")


class ARMVEController(object):

    """Controlador para el ARMVEService."""

    def __init__(self, parent):
        """Constructor para el Controlador.

        Argumentos:
            parent -- el servicio que interfacéa con el ARMVEController.
        """
        self.parent = parent
        # Guardamos el estado de "cargando buffer"
        self._buffering = False
        # Guardamos el estado de "imprimir cuando terminemos de cargar"
        self._print_on_finish = False

    def tag_leido(self, response):
        """Devuelve el tag leido.

        Argumentos:
            response -- respuesta recibida del evento.
        """
        # encendemos el monitor si estamos en modo ahorro de energía
        self.parent.encender_monitor()
        # Devolvemos el tag y el tipo de tag.
        tipo, tag = self.get_tag(response)
        return tipo, dumps(tag)

    def _get_tag_response(self, response, index=0):
        """Obtiene y formatea la respuesta del tag.

        Argumentos:
            response -- respuesta.
            index -- qué numero de tag queremos leer en la lista.
        """
        # por defecto no leímos ningun tag.
        tag = None
        # y el tipo es "no hay tag"
        tipo = NO_TAG
        # obtenemos el numero de serie del tag que vamos a leer
        serial = response['serial_number'][index]
        # leemos el tag y recibimos la data.
        data = self.parent.rfid.get_tag_data(serial,
                                             comprobar_token=COMPROBAR_TOKEN)
        # comprobamos que siga habiendo tag, porque entre que recibimos la
        # señal de que tenemos tag y que lo leemos el usuario lo puede quitar
        # es lo que pasa cuando un tag está menos de 150ms en el lector
        if data is not None:
            # filtramos algun tipo raro en el input del tag
            if data['tipo_tag'] in TIPOS_TAGS:
                tipo_tag = TIPOS_TAGS[data['tipo_tag']]
            else:
                tipo_tag = TIPOS_TAGS[COD_TAG_DESCONOCIDO]

            # si el tag es de tipo ADMIN le cambiamos el tipo para manejarlos
            # todos juntos
            if tipo_tag in TAGS_ADMIN:
                tipo = TAG_ADMIN
            else:
                # tambien nos fijamos si está vacío y lo marcamos como tal.
                if data['user_data'] == "":
                    tipo = TAG_VACIO
                else:
                    tipo = TAG_DATOS

            # si el contenido del tag es de largo cero le asigamos un string
            # vacío.
            if len(data["user_data"]) == 0:
                data["user_data"] = ""

            # encodeamos en base 64 el contenido del tag si tiene datos.
            if data["user_data"] == "":
                _tag_data = ""
            else:
                _tag_data = b64encode(data['user_data']).decode()

            # armamos el diccionario con el contenido del tag para devolver.
            # limpiamos un poco el serial y el token para que tengan el formato
            # que usamos a alto nivel.
            tag = {
                "serial": self._get_normalized_serial(serial),
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
        # Por defecto no tenemos tag.
        tipo = NO_TAG
        tag = None

        # si la respuesta del RFID no vino en la llamada vamos a traer el
        # primer tag que encontremos
        if response is None and hasattr(self.parent, "rfid"):
            response = self.parent.rfid.get_tags()
            if response is not None:
                response = response[0]

        # si tenemos un tag presente
        if response is not None:
            # si hay un tag traemos la respuesta
            if response['number'] == 1:
                tipo, tag = self._get_tag_response(response)
                # el tipo del tag tiene que ser distinto de vacío, esto lo
                # agregamos por que puede pasar que cuando parseamos el tag que
                # queremos leer quizas el tag no está mas presente, por lo cual
                # cancelamos todo el proceso.
                assert tipo != NO_TAG
            elif response['number'] > 1:
                # si tenemos mas de un tag disparamos una colisión
                tipo = TAG_COLISION
                # pero devolvemos los tipos de tags que estan colicionando.
                # Esto nos sirve en la aplicacion cliente para saber qué es lo
                # que está pasando, no es lo mismo un voto y una credencial que
                # dos votos, por ejemplo.
                tipos_tags = self.parent.rfid.get_tipos_tags(response)
                tipos = [tipo_[0] for tipo_ in tipos_tags]
                tag = {"tipo": tipos,
                       "datos": ''}
                # esto no tiene mucho sentido en "voto" pero en transmision
                # puede pasar que apoyen mas de un acta de transmision y
                # entonces agarramos el primero que enontremos y lo devolvemos.
                if COD_TAG_RECUENTO in tipos:
                    for index, datos_tag in enumerate(tipos_tags):
                        tipo_, tag_ = self._get_tag_response(response, index)
                        if tipo_ == TAG_DATOS and tag_['tipo'] == TAG_RECUENTO:
                            tipo = tipo_
                            tag = tag_
                            break
                        else:
                            sleep(0.1)
        return tipo, tag

    def get_tag_metadata(self):
        """Obtiene la metadata del tag."""
        tag_meta = None

        tags = self.parent.rfid.get_tags()
        # agarramos solo la informacion de los tags, no nos importan el resto
        # de las cosas de estado del protocolo.
        if tags is not None:
            tags = tags[0]

        # si tenemos mas de un tag no devolvemos metadata.
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

                    # preparamos el diccionario que devolvemos con los datos
                    # con el formato amigable que usan las apps que consumen
                    # este servicio.
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
        """Dado un numero de serie de chip en un lista de decimales
        lo devuelve en hexa.

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

    def _check_data(self, serial, data, tipo):
        """Chequea que el tag esté correctamente escrito."""
        # Tengo que esperar un poco porque es lo que tarda en responder el ARM
        sleep(0.1)
        written_data = self.parent.rfid.get_tag_data(serial)

        # Comparo que el tag sea valido y que la data que estoy queriendo
        # guardar es igual a la que lei (o que no me entró el escrutinio en el
        # tag y estoy guardando ese tag especial)
        ret = written_data is not None and \
            (data == written_data['user_data'] or
             written_data['tipo_tag'] == COD_TAG_NO_ENTRA)
        return ret

    def write(self, serial, tipo, data, marcar_ro):
        """Escribe un tag.

        Argumentos:
            serial -- el numero de serie del tag.
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
                    rfid.write_tag(serial, tipo, TOKEN, data)
                    # Chequeo la data a ver si se grabó bien. Si la data que
                    # quise grabar es diferente intento de nuevo
                    success = self._check_data(serial, data, tipo)
                    retries_left -= 1
                # si la grabacion fue un exito voy a quermarlo
                if success and marcar_ro:
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
        # si tenemos respuesta y no tenemos un error de lectura
        if data is not None and data[3] != MSG_ERROR:
            for element in data[0]:
                # Si hay algún bloque quemado asumimos que todos lo están. Esto
                # lo hacemos por que si hay un bloque quemado no queremos
                # escribir nada en esta boleta, aunque no todos lo estén.
                if element['byte']:
                    return True
        return False

    def con_tarjeta(self, response):
        """Formatea el output de tarjeta (papel) nueva."""
        # encendemos el monitor si estamos en modo ahorro de energía
        self.parent.encender_monitor()
        return [response]

    def insertando_papel(self, response):
        """Formatea el output de insertando papel."""
        return [response]

    def autofeed_end(self, response):
        """Formatea el output de autofeed end."""
        return [response]

    def print_image(self, filepath, mode, size, transpose, only_buffer):
        """Imprime una imagen desde un path.

        Argumentos:
        filepath -- path de la imagen a imprimir.
        mode -- modo de la imagen.
        size -- tamaño.
        transpose -- si damos vuelta o no.
        only_buffer -- booleano. si es True no imprime la imagen, solo buferea.
        """
        # establecemos que estamos cargando el buffer de impresion.
        self._buffering = True
        # y que estamos escribiendo.
        self.parent.printing = True
        # llemos la imagen y la preparamos para imprimir.
        image_file = open(filepath, "rb")
        data = image_file.read()
        image = Image.frombytes(mode, size, data)
        if transpose:
            image = image.transpose(Image.ROTATE_90)

        data = image.convert("L").getdata()
        # Diferenciamos entre la version nueva del protocolo de impresión y la
        # anterior ya que los parametros que necesitan ambas son diferentes.
        if self.parent.impresion_v2:
            width, height = image.size
            self.parent.printer.load_buffer_compressed_full(
                data, self.parent._free_page_mem, width, height,
                print_immediately=not only_buffer)
        else:
            self.parent.printer.load_buffer_compressed(
                data, self.parent._free_page_mem,
                print_immediately=not only_buffer)
        # establecemos que no estamos mas cargando el buffer.
        self._buffering = False

    def imprimir_serializado(self, tipo_tag, tag, transpose, only_buffer=False,
                             extra_data=None):
        """Registra un documento que fue enviado serializado via d-bus.

        Argumentos:
            tipo_tag -- el tipo de documento que queremos registrar. Puede ser:
                (Seleccion, Apertura, Recuento/Totalizacion o Prueba)
            tag -- Contenido del tag serializado.
            transpose -- transpone la imagen.
            only_buffer -- Solo guarda en el buffer, no imprime.
            extra_data -- datos extra que queremos imprimir pero que no se
            guardan en el chip.
        """
        self._buffering = True
        if tipo_tag == "Seleccion":
            # pueden venir tanto un objeto seleccion armado como un string con
            # el contenido del tag.
            if type(tag) == Seleccion:
                boleta = tag
            else:
                boleta = Seleccion.desde_string(tag)
            # si estamos en modo demo mostramos "demostracion - uso no oficial"
            mostrar = {"watermark": MODO_DEMO}
            image = boleta.a_imagen(mostrar)
        elif tipo_tag == "Apertura":
            apertura = Apertura.desde_tag(b64decode(tag))
            image = apertura.a_imagen()
        elif tipo_tag == "Recuento":
            # desencodeamos el recuento y lo agregamos los datos extras que
            # mandamos que no estan encodeados en el tag pero queremos que
            # aparezcan en la impresion, como los datos de las autoridades, el
            # tipo de acta que vamos a imprimir y el horario del acta.
            # determino que (sub)clase instanciar (Recuento predeterminado)
            extra_data = loads(extra_data)
            for cls in Totalizacion, Recuento:
                if cls.clase_acta == extra_data.get("clase_acta"):
                    break
            recuento = cls.desde_tag(b64decode(tag),
                                     con_dnis=extra_data.get('con_dni'))
            autoridades = extra_data.get('autoridades')
            if autoridades is not None and len(autoridades):
                recuento.autoridades = [Autoridad.desde_dict(aut) for aut
                                        in autoridades]
            recuento.hora = extra_data['hora']
            image = recuento.a_imagen(tipo=extra_data['tipo_acta'])
        elif tipo_tag == "Prueba":
            image = ImagenPrueba().render_image()

        # convertimos el acta a blanco y negro.
        image = image.convert('L')
        # Si es necesario transponer la imagen la rotamos.
        if transpose:
            image = image.transpose(Image.ROTATE_270)
        # Registramos el evento efimero de carga de buffer
        if self.parent.impresion_v2:
            self.parent.printer.register_load_buffer_compressed_full()
        else:
            ack = self.parent.printer.register_load_buffer_compressed()
            logger.debug("Respuesta suscripcion carga buffer: %s", ack)
        # Registramos el evento efimero del fin de impresion
        for retries in range(3):
            ack = self.parent.printer.register_print_finished()
            logger.debug("Respuesta suscripcion impresión: %s", ack)
            if ack:
                break

        # extraemos la data de la imagen
        data = image.getdata()

        # Cargamos el buffer e imprimimimos en caso de querer imprimir.
        if self.parent.impresion_v2:
            width, height = image.size
            self.parent.printer.load_buffer_compressed_full(
                data, self.parent._free_page_mem, width, height,
                print_immediately=not only_buffer)
        else:
            self.parent.printer.load_buffer_compressed(
                data, self.parent._free_page_mem,
                print_immediately=not only_buffer,
                callback_error=self.parent.error_impresion)

    def registrar(self, tag, solo_impimir=False, aes_key=False):
        """Registra un voto.

        Argumentos:
            tag -- el voto a registrar serializado como tag.
            solo_impimir -- no guarda el tag, solo imprime.
            aes_key -- la clave con la que vamos a encriptar.
        """
        tag_guardado = False
        marcar_ro = QUEMA

        # Cargo el objeto seleccion, si viene None no es valido y lanzamos el
        # error de grabación.
        seleccion = Seleccion.desde_tag(tag)
        if seleccion is not None:
            # si la seleccion es válida guardamos el tag (en caso de que sea
            #  necesario)
            if solo_impimir:
                tag_guardado = True
            else:
                tag_guardado = self.guardar_tag(TAG_VOTO, tag, marcar_ro,
                                                aes_key)

        if tag_guardado:
            def _inner():
                self.imprimir_serializado("Seleccion", seleccion,
                                          transpose=True)
            # Lo desatachamos, para que devuelva el control a la UI mientras
            # imprime.
            timeout_add(10, _inner)

        return tag_guardado

    def do_print(self):
        """Ejecuta la impresion cuando el buffer fue cargado anteriormente.

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
        self.parent.ipc.con_tarjeta(status)
        self.parent.printing = False
        return []

    def guardar_tag(self, tipo_tag, data, marcar_ro, aes_key=False):
        """Guarda un tag.

        Argumentos:
            tipo_tag -- el tipo de tag a guardar.
            data -- el contenido del tag a guardar.
            marcar_ro -- quema el tag.
        """
        guardado = False
        try:
            # si el estado del papel tiene todas las condiciones requeridas
            # para guardar el tag.
            if self.parent.printer.is_paper_ready():
                # traigo los tags
                tags = self.parent.rfid.get_tags()
                # si tengo un solo tag y puedo guardar.
                if (tags is not None and tags[0] is not None and
                    tags[0]["number"] == 1):

                    serial_number = tags[0]["serial_number"][0]

                    # si es un voto y tengo la key de encriptacion lo encripto
                    if tipo_tag == TAG_VOTO and aes_key:
                        data = encriptar_voto(aes_key, serial_number, data)
                    # guardamos el tag y obtenemos el estado de grabación.
                    guardado = self.write(serial_number, tipo_tag, data,
                                          marcar_ro)
        except Exception as e:
            logger.exception(e)
        return guardado

    def pir_detected_cb(self, response):
        """Se lanza cuando se recibe el evento de pir detectado."""
        if response:
            # encendemos el monitor si estamos en modo ahorro de energía
            self.parent.encender_monitor()

    def pir_not_detected_cb(self, response):
        """Se lanza cuando se recibe el evento de pir no detectado."""
        if response:
            self.parent.reset_off_counter()

    def set_tipo(self, serial, tipo):
        """Cambia el tipo de tag del espacio de usuario del tag."""
        # solo escribimos un tag de tipo válido.
        if tipo in TIPOS_TAGS_REV:
            # Obtenemos el valor numerico del tipo que queremos guardar.
            tipo = TIPOS_TAGS_REV[tipo]
            # obtenemos la metadata y establecemos el tipo
            metadata = self.parent.rfid.read_block(serial, 0)
            metadata_array = bytearray(metadata[0]['bytes'])
            metadata_array[1] = tipo
            self.parent.rfid.write_block(serial, 0, metadata_array)

    def get_map(self):
        """Devuelve el mapa completo del tag."""
        response = self.parent.rfid.get_tags()[0]
        dmp = []
        # solo si tenemos un tag.
        if response is not None and response['number'] == 1:
            serial = response['serial_number'][0]
            retries = 5
            bloques = []
            while retries > 0:
                # leemos todos los bloques.
                rfid_data = self.parent.rfid.read_blocks(serial, 0,
                                                         BLOQUES_TAG-1)
                # a veces leyendo todos los bloques del tag podemos tener algun
                # error asi que reintentemos la lectura algunas veces.
                if rfid_data is None or rfid_data[3] == MSG_ERROR:
                    retries -= 1
                    continue

                # si no hay error de lectura cortamos el loop en la proxima
                # iteración
                retries = 0
                # recorremos todos los bolques y los juntamos.
                for block in rfid_data[0]:
                    bloques.extend(block['bytes'])
                # Formateo los bloques en el formato de tagtools.
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
        return dmp

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
        """Callback que ejecuta cuando se refibe el evento de power source."""
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
