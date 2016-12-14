from cryptography.exceptions import InvalidTag

from msa.core.crypto import encriptar, desencriptar
from msa.core.crypto.settings import ENCRIPTAR_TAG


def encriptar_tag(func):
    def _inner(self):
        tag = func(self)
        aes_key = self.mesa.get_aes_key()
        if ENCRIPTAR_TAG and aes_key is not None:
            tag = encriptar(aes_key, tag)
        return tag

    return _inner


def desencriptar_tag(func):
    def _inner(cls, tag, mesa):
        seleccion = None
        aes_key = mesa.get_aes_key()
        try:
            if ENCRIPTAR_TAG and aes_key is not None:
                tag = desencriptar(aes_key, tag)
            seleccion = func(cls, tag, mesa)
        except InvalidTag:
            pass
        return seleccion

    return _inner
