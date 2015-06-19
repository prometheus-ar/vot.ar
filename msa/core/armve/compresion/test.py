#!/usr/bin/env python
# coding: utf-8

import sys
import time
import platform

from PIL import Image


def main():
    if platform.architecture()[0] == '64bit':
        print 'Usando compresión nativa de 64 bits'
        from x86_64.compresion import comprimir1B
    else:
        print 'Usando compresión nativa de 32 bits'
        from i686.compresion import comprimir1B

    from compresion import comprimir1B as pycomprimir1B

    def run_test1(stream):
        cstream1 = comprimir1B(stream)

    def run_test2(stream):
        cstream2 = pycomprimir1B(stream)

    if __name__ == '__main__':
        img = Image.open(sys.argv[1])
        i = img.convert('L')
        d = i.getdata()
        t0 = time.time()
        run_test1(d)
        print 'tiempo de ejecución binaria', time.time()-t0, 'segundos'
        t0 = time.time()
        run_test2(d)
        print 'tiempo de ejecución python', time.time()-t0, 'segundos'

if __name__ == "__main__":
    main()
