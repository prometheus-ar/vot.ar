# coding: utf-8

from msa.core.helpers import get_active_ports


def detect_rfid_port():
    """ Devuelve el puerto al cual esta conectado el lector RFID.
        Puerto BAJO (sys_number=00)
    """
    devices = get_active_ports()
    return devices[0].device_node if devices else None

def change_byte_order(s):
    """ Invierte de a pares el orden de un string con bytes.
        Esta función cumple que: s == f(f(s))
        Ejemplo:
            In [114]: id
            Out[114]: '78DF0E34000104E0'

            In [115]: change_byte_order(id)
            Out[115]: 'E0040100340EDF78'
    """
    out = ''
    for i in xrange(len(s), 0, -2):
        out += s[i-2:i]
    return out

def str2hexa(cadena):
    """ Función utilizada para debug, dada una cadena devuelve
        su representación en hexadecimal con el '0x' delante.
        Ejemplo:
            In [5]: multiiso.str2hexa('abc\n')
            Out[5]: '0x61 0x62 0x63 0x0A'
    """
    hexa=''
    for car in cadena:
        hexa += '0x%02x' % ord(car) + ' '
    return hexa.rstrip()


def str2hexa2(cadena):
    """ Función utilizada para debug, dada una cadena devuelve
        su representación en hexadecimal sin el '0x' delante.
        Ejemplo:
            In [5]: multiiso.str2hexa2('abc\n')
            Out[5]: '61 62 63 0A'
    """
    hexa=''
    for car in cadena:
        hexa += car.encode('hex').upper() + ' '
    return hexa.rstrip()
