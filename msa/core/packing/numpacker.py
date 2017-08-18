#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Módulo para empaquetar valores en un formato uniforme (ancho fijo)"""

from __future__ import absolute_import

from msa.core.packing.settings import CANTIDAD_BITS_PACKER, FAST_PACKING
from six.moves import range


# Ejemplo para 8 listas, voto en blanco, boletas, total, 3 listas especiales:
# secuencia = [5786, 5974, 5884, 5811, 5892, 5954, 5957, 5992, 5822,
#              53072, 54677, 535, 535, 535]
# numero = 2380259842134475468078889251895247614849807353499528915740565897751
# bytes = b'\x16\x9a\x17V\x16\xfc\x16\xb3\x17\x04\x17B\x17E\x17h\x16\xbe\xcf'+
#         b'P\xd5\x95\x02\x17\x02\x17\x02\x17' -> grabado al chip
# configuración: FAST_PACKING = True, CANTIDAD_BITS_PACKER = 16


def num_to_bytes(number):
    """Convierte un valor numérico entero ('long') a una cadena de bytes"""
    r = []
    # convertir parte menos significativa a byte, con desplazamiento de bits:
    while number > 0:
        # nota: no hay overflow, porque el nro puede ser extremadamente grande:
        r.insert(0, ((number & 255).to_bytes(1, "big")))
        number = number >> 8
    return b''.join(r)


def bytes_to_num(string):
    """Convierte una cadena de bytes al valor numérico entero"""
    r = 0
    # convertir bytes y acumular valor entero, con desplazamiento de bits:
    for c in string:
        # nota: en python 3, al recorrer un array de bytes, devuelve int:
        if r == 0:
            r = c
        else:
            r = (r << 8) + c
    return r


def bin_pack_1(seq):
    """Empaqueta una secuencia de enteros en un único valor numérico (largo)"""
    res = 0
    # acumular los valores con desplazamiento según cantidad de bits:
    for v in seq:
        if res == 0:
            res = v
        else:
            if v > (2 ** CANTIDAD_BITS_PACKER - 1):
                raise ValueError("Imposible empaquetar nro=%s" % v)
            res = (res << CANTIDAD_BITS_PACKER) + v
    return res


def bin_unpack_1(r):
    """Des-empaqueta una valor numerico, devuelve una secuencia de enteros"""
    res = []
    # extraer los valores con desplazamiento según cantidad de bits:
    while r > 0:
        res.insert(0, r & (2 ** CANTIDAD_BITS_PACKER - 1))
        r = r >> CANTIDAD_BITS_PACKER
    return res


def pack_slow(lista_valores, bits=CANTIDAD_BITS_PACKER):
    """Empaqueta enteros (via cadena de bits), devuelve cadena de bytes"""
    salida = []
    lista_cadena = []
    # armar la cadena de bits (concatenando la representacion binaria de c/u):
    for valor in lista_valores:
        binario = bin(valor)[2:].rjust(bits, '0')
        if len(binario) > bits:
            raise ValueError("Imposible empaquetar nro=%s" % valor)
        lista_cadena.append(binario)
    cadena = ''.join(lista_cadena)
    # recortar la cadena cada 8 bits y convertir a byte:
    for i in range(0, len(cadena), 8):
        byte = chr(int(cadena[i:i + 8].ljust(8, '0'), 2)).encode()
        salida.append(byte)
    return b''.join(salida)


def unpack_slow(cadena, bits=CANTIDAD_BITS_PACKER):
    """Des-empaqueta una cadena bytes (via cadena de bits), devuelve enteros"""
    salida = []
    cadena = cadena.decode()
    # convertir bytes a cadena de bits:
    tmp = [bin(ord(caracter))[2:].rjust(8, '0') for caracter in cadena]
    tmp = ''.join(tmp)
    # recorrer la cadena de bits y convertir a valor numérico s/ longitud:
    for i in range(0, len(tmp), bits):
        recorte = tmp[i:i + bits]
        if len(recorte) == bits:
            nbyte = int(recorte, 2)
            salida.append(nbyte)
    return salida


def pack_fast(seq):
    """Empaqueta una enteros (via valor 'largo'), devuelve cadena bytes"""
    return num_to_bytes(bin_pack_1(seq))


def unpack_fast(string):
    """Des-empaqueta una cadena bytes (via valor 'largo'), devuelve enteros"""
    return bin_unpack_1(bytes_to_num(string))


def pack(seq):
    """Empaqueta enteros (ver settings), devolviendo una cadena de bytes"""
    if FAST_PACKING:
        return pack_fast(seq)
    else:
        return pack_slow(seq)


def unpack(string):
    """Des-empaqueta una cadena de bytes (ver settings), devolviendo enteros"""
    if FAST_PACKING:
        return unpack_fast(string)
    else:
        return unpack_slow(string)
