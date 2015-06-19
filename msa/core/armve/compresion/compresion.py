#!/usr/bin/env python
# coding: utf-8

""" Implementación 100% Python del algoritmo de compresión (simil-RLE) de
    trabajos de impresión, útil para pruebas. """

import time

from PIL import Image
from struct import pack, unpack


#def comprimir1B(imagen):
#    """ Recibe una lista de bytes a comprimir, devuelve los bytes comprimidos
#        de a 1 Byte """
#    out = []
#    idx = 0
#    color_ant = imagen[idx] & 128
#    cantidad = 1
#    for idx in xrange(1, len(imagen)):
#        color = imagen[idx] & 128 # Tomo el primer bit, 0 o 1
#        if (color_ant != color) or (cantidad == 127): # Cambió el color o me pasé de 7 bits
#            out.extend([chr(color_ant + cantidad)])
#            color_ant = color
#            cantidad = 1
#        else:
#            cantidad += 1
#    out.append(chr(color_ant + cantidad)) # Acobacho en la salida
#    return ''.join(out)


def comprimir2B(imagen):
    """ Recibe una lista de bytes a comprimir, devuelve los bytes comprimidos
        de a 2 Bytes """
    out = ''
    color_ant = None
    cantidad = 0
    for v in imagen:
        #v = unpack('<B', bv)[0]
        color = (v & 128) << 8 # Tomo el primer bit, 0 o 1 y lo desplazo 8 bits para que quede de 2 Bytes
        if cantidad == 0:
            color_ant = color
            cantidad = 1
        elif (color_ant != color) or (cantidad == 32767): # cambió el color o me pasé de 15 bits
            out += pack('<H', color_ant + cantidad) # Acobacho en la salida
            color_ant = color
            cantidad = 1
        else:
            cantidad += 1
    out += pack('<H', color_ant + cantidad) # Acobacho en la salida
    return out

def descomprimir1B(c_imagen):
    """ Recibe un bytestring comprimido y lo descomprime """
    out = ''
    for bv in c_imagen:
        v = unpack('<B', bv)[0]
        color = v & 128 # Tomo el primer bit, 0 o 1
        cantidad = v & 127 # Tomo el resto de los bits
        if color == 0:
            colstr = '\x00'
        else:
            colstr = '\xff'
        out += colstr * cantidad
    return out

def descomprimir2B(c_imagen):
    """ Recibe un bytestring comprimido y lo descomprime """
    out = ''
    for idx in range(0, len(c_imagen), 2):
        bv = c_imagen[idx:idx+2]
        v = unpack('<H', bv)[0]
        color = v & 32768 # Tomo el primer bit, 0 o 1
        cantidad = v & 32767 # Tomo el resto de los bits
        #print repr(bv), repr(v), cantidad
        #return
        if color == 0:
            colstr = '\x00'
        else:
            colstr = '\xff'
        out += colstr * cantidad
    return out

def comparar(s1, s2):
    if len(s1) != len(s2):
        return False
    i = 0
    for bc1, c2 in zip(s1, s2):
        c1 = pack('<B', bc1)
        if c1 != c2:
            print i, repr(c1), repr(c2)
            return False
        else:
            i += 1
    return True

if __name__ == '__main__':
    import sys
    i = Image.open(sys.argv[1])
    #data = i.tostring()
    data = i.getdata() # Devuelve una lista con el valor de cada pixel, 0 o 255
    t1 = time.time()
    ci1 = comprimir1B(data)
    print 'Tiempo Comprimir1B', time.time()-t1, ' segundos'
    t2 = time.time()
    ci2 = comprimir2B(data)
    print 'Tiempo Comprimir2B', time.time()-t2, ' segundos'
    #print repr(list(data)[:100])
    #print repr(ci1)
    #print repr(ci2)
    di1 = descomprimir1B(ci1)
    di2 = descomprimir2B(ci2)
    #print repr(di1[:100])
    #print len(data), len(ci1), len(ci2), len(di1)
    print len(data), len(ci1), len(ci2), len(di1), len(di2)
    if comparar(data, di1):
        print 'OK 1 Byte'
    else:
        print 'ERR 1 Byte'
    if comparar(data, di2):
        print 'OK 2 Byte'
    else:
        print 'ERR 2 Byte'

