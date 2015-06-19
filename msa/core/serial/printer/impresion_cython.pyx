# -*- coding: utf-8 -*-

def imprimir_image_fast(self, im):

    # =========================================================================
    # definiciones cython (no modificar)
    # -------------------------------------------------------------------------

    cdef int y, x, i, max_x, max_y, last_b, cant_bytes, data
    cdef int b, group_len
    cdef int char
    cdef int shift[8]
    cdef bytes buf = b''

    # =========================================================================
    # codigo pyton (copiar de impresion.py)
    # -------------------------------------------------------------------------

    # recorro pixels, armo buffer de bits para enviar a la impresora
    # obtengo los datos internos de PIL para optimizar
    # comprimo y envio directamente a impresora
    xmax = im.size[0]
    for i in range(8):
        shift[i] = 1 << (7-i)
    i = 0
    x = 0
    b = 0
    saved = 0
    cant_bytes = xmax / 8
    char = -1
    group_len = 0
    for data in im.getdata():
        if data==0: b += shift[i]
        i += 1
        if i == 8:
            x += 8
            if char == -1:
                char = b
            if char == b:
                group_len += 1
            if char != b or x == xmax or group_len == 63:
                while 1:
                    if char < 0xc0 and group_len == 1:
                        # envio el caracter sin comprimir
                        buf += chr(char)
                    elif group_len > 0:
                        # comprimo por RLE en hasta 63 repeticiones por vez
                        # envio cantidad de repeticiones y caracter:
                        buf += chr(0xc0 + group_len)
                        buf += chr(char)
                    if char != b and b >= 0:
                        char = b
                        group_len = 1
                    else:
                        char = -1
                        group_len = 0
                    if x != xmax or b < 0:
                        break
                    else:
                        b = -1
            i = 0
            b = 0
            if x == xmax:
                self.write(b"\x1b\xa5\x62%s\x57" % cant_bytes)
                self.write(buf)
                x = 0
                buf = b''
                char = -1

