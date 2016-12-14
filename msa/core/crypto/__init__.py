from os import urandom

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends.openssl.backend import Backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from msa.core.crypto.constants import RANDOM_LEN


def encriptar(aes_key, input_, init_vector=None):
    if init_vector is None:
        init_vector = generate_random_bytes()
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(init_vector),
                    backend=Backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(input_) + encryptor.finalize()
    encrypted = init_vector + encryptor.tag + encrypted
    return encrypted


def desencriptar(aes_key, input_):
    output_ = None
    init_vector, tag, seleccion_encriptada = split(input_)

    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(init_vector, tag),
                    backend=Backend())
    decryptor = cipher.decryptor()
    output_ = decryptor.update(seleccion_encriptada) + decryptor.finalize()
    return output_


def generate_random_bytes(number=RANDOM_LEN):
    return urandom(number)


def split(input_):
    return (input_[:RANDOM_LEN], input_[RANDOM_LEN:RANDOM_LEN+16],
            input_[RANDOM_LEN+16:])

def derivar_clave(pin, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=salt,
        iterations=1000000,
        backend=Backend()
    )
    clave = kdf.derive(pin)
    return clave
