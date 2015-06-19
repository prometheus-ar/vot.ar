# -*- coding: utf-8 -*-
#!/usr/bin/env python
# coding: utf-8
#
# Copyright Eric Soroos ({first name}@soroos.net), 2006
# Licensed under BSD style license.
# There are no warranties, expressed or implied. Use at your own risk.
# Share, understand, and enjoy.
#
# Uses python imaging library.

import itertools
import string

#http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52549
# basic curry function


class curry:

    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)


class barcode (object):

    def __init__(self, symbology):
        self.sym = symbology

    def recognize(self, img):
        (w, h) = img.size

        for scan in range(h - 1, 1, -1):
            rle = self.to_rle(self.extract_row(img, scan))

            if len(rle) < self.sym.min_length:
                continue
            if not self.sym.check_len(rle):
                continue

            chunks = self.sym.chunk(self.to_bars(rle))

            if len(self.sym.invalid_chunks(chunks)):
                continue

            try:
                ret = self.sym.extract(self.to_chars(chunks))
                if len(ret) and self.sym.check_ok(ret):
                    return self.sym.get_value(ret)
            except:
                continue

        return None

    def extract_row(self, img, v):
        (w, h) = img.size
        return img.crop((0, v, w, v + 1)).getdata()

    def to_rle(self, row):
        """Returns a list of (len, color) where the first element and the last
        element are black bars. groupby groups by key value, the map gives me
        white/black  even though we're going to a binary later, we're goign to
        leave this in, since it's going to be somewhat helpful debugging things
        """
        mp = {0: 'b', 255: 'w'}
        ret = []
        # Esto esta así por si tenemos una imagen en escalas de grises.
        # Si no es BN le devuelve parcial la información, pero no rompe el rle.
        for k, g in itertools.groupby(row):
            if k in mp.keys():
                ret.append((len(list(g)), mp[k]))
            else:
                break
        return ret[1:-1]

    def to_bars(self, rle):
        return map(curry(lambda x, y: str(int(y[0] > x)),
                         self.sym.threshold(rle)), rle)

    def to_chars(self, chunked):
        return ''.join(map(lambda x: self.sym.bkw[x], chunked))


class C39(object):

    """ Code 39 recognizer"""

    #two end chars, 9 bars ea + one space separator
    min_length = 19

    def threshold(self, rle):
        """ c39 says that for each block, there are 9 bars, and 3 are wide.
            (+ narrow white spacer) Generally, the wide bars are 3x as wide as
            the  narrow ones.
            Therefore we're going to cutoff @ 2x (something).  Total width
            should be n * (7(w) + 3(3w)) == n * 16w where n is the number of
            characters in the barcode """

        n = (len(rle) + 1) / 10
        pxlen = sum(map(lambda x: x[0], rle))

        return 2 * (pxlen / (16 * n))

    def check_len(self, rle):
        """each chunk is 9, with one spacer for 10 for all but the last bar"""
        return len(rle) % 10 == 9

    def _3_wide(self, elt):
        """ all chunks should have 3 wide bars"""
        return sum(map(lambda x: x == '1', elt)) != 3

    def invalid_chunks(self, chunked):
        return filter(self._3_wide, chunked)

    def _iterkey(self, val):
        self._iterstate += 1
        return (self._iterstate - 1) / 10

    def chunk(self, bars):
        self._iterstate = 0
        return [''.join(list(g)[:9]) for k, g in
                itertools.groupby(bars, self._iterkey)]

    def extract(self, chars):
        """Need to filter off the begnning/end * characters, if they don't
           exist, barf some other symbologies will want to check the
           checkdigit.
        """
        if not (chars[0] == '*' and chars[-1] == '*'):
            return ''
        return chars[1:-1]

    # from wikipedia http://en.wikipedia.org/wiki/Code_39
    fwd = {
        '*': 'bWbwBwBwb',
        '-': 'bWbwbwBwB',
        '$': 'bWbWbWbwb',
        '%': 'bwbWbWbWb',
        ' ': 'bWBwbwBwb',
        '.': 'BWbwbwBwb',
        '/': 'bWbWbwbWb',
        '+': 'bWbwbWbWb',
        '0': 'bwbWBwBwb',
        '1': 'BwbWbwbwB',
        '2': 'bwBWbwbwB',
        '3': 'BwBWbwbwb',
        '4': 'bwbWBwbwB',
        '5': 'BwbWBwbwb',
        '6': 'bwBWBwbwb',
        '7': 'bwbWbwBwB',
        '8': 'BwbWbwBwb',
        '9': 'bwBWbwBwb',
        'A': 'BwbwbWbwB',
        'B': 'bwBwbWbwB',
        'C': 'BwBwbWbwb',
        'D': 'bwbwBWbwB',
        'E': 'BwbwBWbwb',
        'F': 'bwBwBWbwb',
        'G': 'bwbwbWBwB',
        'H': 'BwbwbWBwb',
        'I': 'bwBwbWBwb',
        'J': 'bwbwBWBwb',
        'K': 'BwbwbwbWB',
        'L': 'bwBwbwbWB',
        'M': 'BwBwbwbWb',
        'N': 'bwbwBwbWB',
        'O': 'BwbwBwbWb',
        'P': 'bwBwBwbWb',
        'Q': 'bwbwbwBWB',
        'R': 'BwbwbwBWb',
        'S': 'bwBwbwBWb',
        'T': 'bwbwBwBWb',
        'U': 'BWbwbwbwB',
        'V': 'bWBwbwbwB',
        'W': 'BWBwbwbwb',
        'X': 'bWbwBwbwB',
        'Y': 'BWbwBwbwb',
        'Z': 'bWBwBwbwb'}

    bkw = {}

    def letToBin(let):
        r = []
        [r.append(str(int(l in string.uppercase))) for l in let]
        return ''.join(r)
    # using a 'binary' code, since we're going to drop the white black thing,
    # since we know that they alternate
    for (k, v) in fwd.items():
        bkw[letToBin(v)] = k

    #for (k,v) in fwd.items(): bkw[v] = k

    def check_ok(self, value):
        chars = {'0': 0,
                 '1': 1,
                 '2': 2,
                 '3': 3,
                 '4': 4,
                 '5': 5,
                 '6': 6,
                 '7': 7,
                 '8': 8,
                 '9': 9,
                 'A': 10,
                 'B': 11,
                 'C': 12,
                 'D': 13,
                 'E': 14,
                 'F': 15,
                 'G': 16,
                 'H': 17,
                 'I': 18,
                 'J': 19,
                 'K': 20,
                 'L': 21,
                 'M': 22,
                 'N': 23,
                 'O': 24,
                 'P': 25,
                 'Q': 26,
                 'R': 27,
                 'S': 28,
                 'T': 29,
                 'U': 30,
                 'V': 31,
                 'W': 32,
                 'X': 33,
                 'Y': 34,
                 'Z': 35,
                 '-': 36,
                 '.': 37,
                 ' ': 38,
                 '$': 39,
                 '/': 40,
                 '+': 41,
                 '%': 42,
                }

        suma = 0
        for i in value[:-1]:
            suma += chars[i]
        return suma % 43 == chars[value[-1]]

    def get_value(self, value):
        return value[:-1]
