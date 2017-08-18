from base64 import b64decode, b64encode
from binascii import unhexlify
from ujson import loads

from construct import FieldError

from msa.core.crypto import desencriptar_voto
from msa.core.crypto.constants import PADDING_SERIAL
from msa.core.crypto.structs import (
    struct_credencial, struct_credencial_tecnico)
from msa.core.documentos.credenciales import verificar_firma
from msa.core.documentos.constants import (NOMBRE_KEY_AUTORIDAD,
                                           NOMBRE_KEY_TECNICO)
from msa.core.rfid.constants import (TAG_APERTURA, TAG_CAPACITACION,
                                     TAG_PRESIDENTE_MESA, TAG_RECUENTO,
                                     TAG_USUARIO_MSA, TAG_VACIO, TAG_VOTO,
                                     TAGS_ADMIN, TAG_NO_ENTRA)


class SoporteDigital():

    """Expresa el soporte digital de la BUE."""

    def __init__(self, datos, tipo=None, serial=None, token=None, clase=None,
                 reception_level=None, read_only=None):
        """ Constructor del objeto SoporteDigital

        Argumentos:
            datos -- el contenido del tag.
            serial -- el serial del tag.
            tipo -- el tipo de tag.
            token -- el token del tag.
            clase -- la clase de soporte digital.
            reception_level -- el nivel de recepcion de la lectura.
            read_only -- estado de lectura.
        """
        self.serial = serial
        self.tipo = tipo
        self.datos = datos
        self.token = token
        self.clase = clase
        self.reception_level = reception_level
        self.read_only = read_only

    def __eq__(self, other):
        return (self is not None and other is not None and
                self.serial == other.serial and self.datos == other.datos)

    @classmethod
    def desde_dict(cls, tag_data):
        """Transforma el diccionario del tag en un objeto de SoporteDigital."""
        instancia = None
        if tag_data is not None:
            dict_ = loads(tag_data)
            # La respuesta puede ser None (cuando llegó "null" en el json)
            if dict_ is not None:
                # desencodeamos los datos que llegaron en caso de que existan.
                if dict_.get("datos") is not None:
                    datos = b64decode(dict_['datos'])
                else:
                    datos = None
                # Creamos la instancia que vamos a devolver.
                instancia = cls(datos, dict_.get("tipo"), dict_.get("serial"),
                                dict_.get("token"), dict_.get("clase"),
                                dict_.get("reception_level"),
                                dict_.get("read_only"))
        return instancia

    def a_dict(self):
        # Si hay datos los codifico en base64.
        if self.datos is not None:
            _datos = b64encode(self.datos).decode("utf8")

        dict_ = {
            "serial": self.serial,
            "tipo": self.tipo,
            "datos": _datos,
            "token": self.token,
            "clase": self.clase,
            "reception_level": self.reception_level,
            "read_only": self.read_only
        }

        return dict_

    def es_voto(self):
        return self.tipo == TAG_VOTO

    def es_apertura(self):
        return self.tipo == TAG_APERTURA

    def es_recuento(self):
        return self.tipo == TAG_RECUENTO

    def es_autoridad(self):
        return self.tipo == TAG_PRESIDENTE_MESA

    def es_capacitacion(self):
        return self.tipo == TAG_CAPACITACION

    def es_tag_vacio(self):
        return self.tipo == TAG_VACIO

    def es_tecnico(self):
        return self.tipo == TAG_USUARIO_MSA

    def es_admin(self):
        return self.tipo in TAGS_ADMIN

    def es_no_entra(self):
        return self.tipo == TAG_NO_ENTRA

    @property
    def vacio(self):
        return self.datos == b''

    @property
    def nombre_firma(self):
        if self.es_tecnico():
            nombre = NOMBRE_KEY_TECNICO
        else:
            nombre = NOMBRE_KEY_AUTORIDAD

        return nombre

    def verificar_firma_credencial(self):
        """Verifica la firma de una la credencial."""
        valida = False
        try:
            struct = (struct_credencial if self.tipo == TAG_PRESIDENTE_MESA
                      else struct_credencial_tecnico)
            # padeamos el vector de inicializacion para que tenga 12 bytes
            init_vector = unhexlify(self.serial) + PADDING_SERIAL
            # parseamos los datos de la credencial
            container = struct.parse(self.datos)
            # generamos la lista de datos que usamos para firmar
            datos_firma = [init_vector, bytes(self.token, "utf8"),
                           container.datos]
            # validamos la firma de los datos
            valida = verificar_firma(datos_firma, container.firma,
                                     self.nombre_firma)
        except FieldError:
            pass

        return valida

    def desencriptar_voto(self, aes_key):
        self.datos = desencriptar_voto(aes_key, self)

