def comprimir1B(imagen):
    """ Recibe una lista de bytes a comprimir, devuelve los bytes comprimidos
        de a 1 Byte """
    out = []
    cdef short color_ant = imagen[0] & 128
    cdef short cantidad = 1
    cdef short color = 0
    cdef int largo_imagen = len(imagen)
    cdef int idx = 0
    for idx in xrange(1, largo_imagen):
        color = imagen[idx] & 128 # Tomo el primer bit, 0 o 1
        if (color_ant != color) or (cantidad == 127): # Cambió el color o me pasé de 7 bits
            out.extend([chr(color_ant + cantidad)])
            color_ant = color
            cantidad = 1
        else:
            cantidad += 1
    out.append(chr(color_ant + cantidad)) # Acobacho en la salida
    return ''.join(out)
