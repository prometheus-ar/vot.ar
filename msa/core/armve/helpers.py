# coding:utf-8
import os.path
import pyudev

from msa.core.armve.settings import SERIAL_PORT
from binascii import unhexlify


def tohex(int_value):
    """Convierte integers a string en formato hex."""
    data_ = format(int_value, 'x')
    result = data_.rjust(6, '0')
    hexed = unhexlify(result)
    return hexed


def array_to_printable_string(array, separator=''):
    """ Convierte un array de ints a un string imprimible con el separador
        que se le pase como parámetro.
        Por ejemplo, en el campo serial de un tag:
        'serial': [224, 4, 1, 0, 126, 33, 9, 63] -> 'e00401007e21093f'
    """
    return separator.join('%02x'.upper() % c for c in array)


def serial_16_to_8(serial):
    return [int(''.join(serial[i:i + 2]), 16) for i in range(0, len(serial),
                                                             2)]


def array_to_string(array):
    """Convierte un array de int a un string."""
    return "".join([chr(char) for char in array])


def string_to_array(string_):
    """Convierte un sting a un array de int"""
    try:
        array = [ord(char) for char in string_]
    except TypeError:
        array = string_

    return array


def get_arm_port():
    port = None

    context = pyudev.Context()
    devices = [device for device in context.list_devices(subsystem='tty',
                                                         ID_VENDOR="MSA_S.A.")]
    if len(devices):
        port = devices[0].device_node

    # Fallback, trato de levantar sin pyudev la constante SERIAL_PORT
    if port is None and os.path.exists(SERIAL_PORT):
        port = SERIAL_PORT

    return port


def is_armve_capable():
    return get_arm_port() is not None
