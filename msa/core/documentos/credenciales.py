from os.path import join

from cryptography.hazmat.backends.openssl.backend import Backend
from cryptography.hazmat.primitives.asymmetric.ec import ECDSA
from cryptography.hazmat.primitives.asymmetric.utils import \
    encode_dss_signature
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from msa.core.documentos.constants import PATH_KEYS


def sizeof(key):
    """Calcular tamaño (en bytes) de los parámetros (r,s) segun bits de la
    curva."""
    # obtener la curva desde la clave y calcular los bytes (con redondeo)
    # para curvas K/B hay un pequeño desperdicio (hasta 1 byte para la firma)
    # se podría usar struct y/o convertir directamente a binario (numpacker?)
    curve = key.curve
    size = curve.key_size // 8 + (1 if curve.key_size % 8 else 0)
    assert int(size) == float(size)
    return int(size)


def leer_clave_publica(nombre_clave):
    """Cargar una clave publica para poder verificar una firma.

    Argumentos:
        nombre_clave -- el nombre d ela clave que queremos leer.
    """
    path_key = join(PATH_KEYS, "{}.pub".format(nombre_clave))
    with open(path_key, "rb") as f:
        return load_pem_public_key(f.read(), backend=Backend())


def verificar_firma(data, raw_signature, nombre_clave):
    """Comprobar los datos procesando la firma cruda -raw- (r, s).

    Argumentos:
        data -- datos que queremos validar.
        raw_signature -- la firma que queremos leer.
    """
    valida = False
    public_key = leer_clave_publica(nombre_clave)

    # rearmar la firma y encodearla en DER (RFC3279):
    size = sizeof(public_key)
    r = int.from_bytes(raw_signature[:size], byteorder="big")
    s = int.from_bytes(raw_signature[size:], byteorder="big")
    signature = encode_dss_signature(r, s)

    # verificarla:
    verifier = public_key.verifier(signature, ECDSA(SHA256()))
    for d in data:
        verifier.update(d)
    try:
        verifier.verify()               # lanza InvalidSignature si no concuerda
        valida = True
    except Exception:
        pass

    return valida
