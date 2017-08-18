"""Modulo para encriptacion y firma digital de votos y credenciales."""
from binascii import unhexlify

from construct import Container
from cryptography.hazmat.backends.openssl.backend import Backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import GCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from msa.core.crypto.constants import DERIVACIONES, PADDING_SERIAL
from msa.core.crypto.settings import ENCRIPTAR_VOTO
from msa.core.crypto.structs import (struct_credencial,
                                     struct_credencial_tecnico, struct_voto)


def encriptar(aes_key, init_vector, input_, associated_data=None):
    """Encripta un stream de bytes.

    Argumentos:
        aes_key -- un stream de 16 bytes con la clave de encriptación.
        init_vector -- un stream de 12 bytes con el vector de inicialización.
        input_ --  el stream de bytes que queremos encriptar.
        associated_data -- la data adicional que queremos usar para encriptar.
    """
    # Creamos el cypher
    cipher = Cipher(AES(aes_key), GCM(init_vector), backend=Backend())
    # Obtenemos el encriptador.
    encryptor = cipher.encryptor()
    # Si existe agregamos los datos adicionales de autenticación.
    if associated_data is not None:
        encryptor.authenticate_additional_data(associated_data)
    # Encriptamos la informacion.
    encrypted = encryptor.update(input_) + encryptor.finalize()
    # Devolvemos en GCM tag y la data encriptada.
    return encryptor.tag, encrypted


def desencriptar(aes_key, init_vector, gcm_tag, datos_encriptados,
                 associated_data=None):
    """Encripta un stream de bytes.

    Argumentos:
        aes_key -- un stream de 16 bytes con la clave de encriptación.
        init_vector -- un stream de 12 bytes con el vector de inicialización.
        gcm_tag -- un stream de 16 bytes con el GCM tag
        associated_data -- la data adicional que queremos usar para encriptar.
    """
    # Creamos el cypher
    cipher = Cipher(AES(aes_key), GCM(init_vector, gcm_tag), backend=Backend())
    # Obtenemos el desencriptador.
    decryptor = cipher.decryptor()
    # Si existe agregamos los datos adicionales de autenticación.
    if associated_data is not None:
        decryptor.authenticate_additional_data(associated_data)
    # desencriptamos los datos
    output_ = decryptor.update(datos_encriptados) + decryptor.finalize()
    return output_


def derivar_clave(clave, salt):
    """Deriva una clave.

    Argumentos:
        clave -- la clave que queremos derivar.
        salt -- el salt que usamos para derivar.
    """
    kdf = PBKDF2HMAC(algorithm=SHA256(), length=16, salt=salt,
                     iterations=DERIVACIONES, backend=Backend())
    clave = kdf.derive(clave)
    return clave


def encriptar_voto(aes_key, serial_number, data):
    """Funcion de alto nivel para encriptar un voto.

    Argumentos:
        aes_key -- un stream de 16 bytes con la clave de encriptación.
        serial_number -- un stream de 8 bytes con el serial_number del tag.
        data --  el stream de bytes que queremos encriptar.
    """
    ret = data
    # si no queremos encriptar el voto devolvemos los datos que nos mandaron
    if ENCRIPTAR_VOTO:
        # El vector tiene que tener 12 bytes asi que le agregamos 4 bytes como
        # padding
        init_vector = serial_number + PADDING_SERIAL
        gcm_tag, data_encriptada = encriptar(aes_key, init_vector, data)
        # armamos un container de construct para armar el voto con el formato
        # correcto
        contenedor = Container(gcm_tag=gcm_tag, len_datos=len(data_encriptada),
                               datos=data_encriptada)
        ret = struct_voto.build(contenedor)

    return ret


def desencriptar_voto(aes_key, tag):
    """Funcion de alto nivel para encriptar un voto.

    Argumentos:
        aes_key -- un stream de 16 bytes con la clave de encriptación.
        tag -- un objeto de tipo SoporteDigital que contiene los datos del tag.
    """
    ret = tag.datos
    # si no estamos encriptando devolvemos los mismos datos que mandaron.
    if ENCRIPTAR_VOTO:
        # El vector tiene que tener 12 bytes asi que le agregamos 4 bytes como
        # padding
        init_vector = unhexlify(tag.serial) + PADDING_SERIAL
        datos_tag = struct_voto.parse(tag.datos)

        ret = desencriptar(aes_key, init_vector, datos_tag.gcm_tag,
                           datos_tag.datos)
    return ret


def desencriptar_credencial(mesa, pin, credencial):
    # generamos el vector de inicializacion
    init_vector = unhexlify(credencial.serial) + PADDING_SERIAL
    # parseamos la credencial con construct
    datos = struct_credencial.parse(credencial.datos)
    # derivamos la clave
    clave = derivar_clave(pin, datos.salt)
    # devolvemos la key de la mesa
    key = desencriptar(clave, init_vector, datos.gcm_tag, datos.datos, mesa)
    return key

def desencriptar_credencial_tecnico(credencial):
    # generamos el vector de inicializacion
    init_vector = unhexlify(credencial.serial) + PADDING_SERIAL
    # parseamos la credencial con construct
    datos = struct_credencial_tecnico.parse(credencial.datos)
    # derivamos la clave
    pin = bytes(credencial.serial, "utf8")
    clave = derivar_clave(pin, datos.salt)
    # devolvemos la key de la mesa
    key = desencriptar(clave, init_vector, datos.gcm_tag, datos.datos)
    return key
