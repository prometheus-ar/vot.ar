# -*- coding: utf-8 -*-

import os
import zbar
import subprocess

from PIL import Image
from tempfile import mkstemp

from msa.core.settings import QR_PIXEL_SIZE, QR_ERROR_LEVEL


def crear_qr(datos):
    '''Genera una imagen con codigo qr de los datos recibidos.'''
    qr = None
    fd, temp_path = mkstemp(suffix='.png', prefix='qr_tmp_')
    tmpl_comando = u'qrencode -o %s -s%s -m0 -l%s "%s"'
    comando = tmpl_comando % (temp_path, unicode(QR_PIXEL_SIZE), QR_ERROR_LEVEL,
                              u''.join(datos))
    try:
        """
        _ = subprocess.Popen([
            'qrencode',
            '-o', temp_path,
            '-s', unicode(QR_PIXEL_SIZE),
            '-m', unicode(0),
            '-l', QR_ERROR_LEVEL,
            ''.join(datos)
        ]).wait()
        """
        os.system(comando)
        qr = Image.open(temp_path)
    except Exception as e:
        #print "EXCEPCION", e
        pass
    finally:
        os.close(fd)
        os.remove(temp_path)
    return qr


def leer_qr(path_imagen):
    '''Lee los datos de una imagen que contenga un codigo qr.'''
    _img = Image.open(path_imagen)
    _img = _img.convert('L')
    width, height = _img.size

    z_img = zbar.Image(width, height, 'Y800', _img.tostring())

    z_scanner = zbar.ImageScanner()
    z_scanner.parse_config('enable')
    z_scanner.scan(z_img)

    data = None
    for symbol in z_img:
        if symbol.QRCODE:
            data = symbol.data
    return data


def leer_barcode(path_imagen, code_type=None):
    '''Lee los datos de una imagen que contenga un codigo de barras.'''
    _img = Image.open(path_imagen)
    _img = _img.convert('L')
    width, height = _img.size

    z_img = zbar.Image(width, height, 'Y800', _img.tostring())

    z_scanner = zbar.ImageScanner()
    z_scanner.parse_config('enable')
    z_scanner.scan(z_img)

    data = None
    for symbol in z_img:
        if symbol:
            data = symbol.data
    return data


def leer_qr_desde_video(callback=lambda s: None, device='/dev/video0'):
    # create a Processor
    proc = zbar.Processor()
    # configure the Processor
    proc.parse_config('enable')
    # initialize the Processor
    proc.init(device)
    # setup a callback

    def my_handler(proc, image, closure):
        # extract results
        for symbol in image:
            if not symbol.count:
                callback(symbol.data)

    proc.set_data_handler(my_handler)
    # enable the preview window
    proc.visible = True
    # initiate scanning
    proc.active = True
    try:
        proc.user_wait()
    except zbar.WindowClosed:
        pass
