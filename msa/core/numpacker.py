#!/usr/bin/env python
# -*- coding: utf-8 -*-

from msa.core.settings import CANTIDAD_BITS_PACKER, FAST_PACKING


def num_to_char(number):
    r = []
    while number > 0:
        r.insert(0, (chr(number & 255)))
        number = number >> 8
    return ''.join(r)


def char_to_num(string):
    r = 0
    for c in string:
        if r == 0:
            r = ord(c)
        else:
            r = (r << 8) + ord(c)
    return r


def bin_pack_1(seq):
    res = 0
    for v in seq:
        if res == 0:
            res = v
        else:
            res = (res << CANTIDAD_BITS_PACKER) + v
    return res


def bin_unpack_1(r):
    res = []
    while r > 0:
        res.insert(0, r & (2 ** CANTIDAD_BITS_PACKER - 1))
        r = r >> CANTIDAD_BITS_PACKER
    return res


def pack_slow(lista_valores, bits=CANTIDAD_BITS_PACKER):
    salida = []
    lista_cadena = []
    for valor in lista_valores:
        lista_cadena.append(bin(valor)[2:].rjust(bits, '0'))
    cadena = ''.join(lista_cadena)
    for i in range(0, len(cadena), 8):
        byte = chr(int(cadena[i:i + 8].ljust(8, '0'), 2))
        salida.append(byte)
    return ''.join(salida)


def unpack_slow(cadena, bits=CANTIDAD_BITS_PACKER):
    salida = []
    tmp = [bin(ord(caracter))[2:].rjust(8, '0') for caracter in cadena]
    tmp = ''.join(tmp)
    for i in range(0, len(tmp), bits):
        recorte = tmp[i:i + bits]
        if len(recorte) == bits:
            nbyte = int(recorte, 2)
            salida.append(nbyte)
    return salida


def pack_fast(seq):
    return num_to_char(bin_pack_1(seq))


def unpack_fast(string):
    return bin_unpack_1(char_to_num(string))


def pack(seq):
    if FAST_PACKING:
        return pack_fast(seq)
    else:
        return pack_slow(seq)


def unpack(string):
    if FAST_PACKING:
        return unpack_fast(string)
    else:
        return unpack_slow(string)


def test(f_unpack, f_pack, l):
    l2 = f_unpack(f_pack(l))
    if l != l2:
        raise Exception('Mismatch')


def test_slow(l):
    test(unpack_slow, pack_slow, l)


def test_fast(l):
    test(unpack_fast, pack_fast, l)


if __name__ == '__main__':
    import random
    from timeit import Timer

    random.seed()

    # Valores que puede la cantidad de votos a un candidato/cargo/partido
    POBLACION = 350

    # Valores que puede contener el Chip/Tag
    MUESTRAS = [16, 21, 44, 77]

    for muestra in MUESTRAS:
        l = random.sample(xrange(0, POBLACION), muestra)
        print("Prueba de numpacker con una muestra de %i elementos" % (muestra))
        for f in ["test_fast", "test_slow"]:
            try:
                t = Timer("%s(%s)" % (f, l), "from __main__ import %s" % f)
                print('%s demora %7.2f usec/pas' %
                    (f, 1000000 * t.timeit(1000) / 1000))
            except Exception, e:
                print("%s ha fallado: %s" % (f, e))
        print
