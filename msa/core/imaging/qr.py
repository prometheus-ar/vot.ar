# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
from tempfile import mkstemp

import six
from PIL import Image

from msa.core.imaging.constants import QR_ERROR_LEVEL, QR_PIXEL_SIZE


def crear_qr(datos):
    '''Genera una imagen con codigo qr de los datos recibidos.'''
    qr = None
    fd, temp_path = mkstemp(suffix='.png', prefix='qr_tmp_')
    tmpl_comando = u'qrencode -o %s -s%s -m0 -l%s "%s"'
    # validacion extra, aun cuando esto fue validado anteriormente
    datos = datos.replace("&", "") \
                 .replace('"', "") \
                 .replace("\"", "") \
                 .replace("/", "")
    comando = tmpl_comando % (temp_path, six.text_type(QR_PIXEL_SIZE),
                              QR_ERROR_LEVEL, datos)
    try:
        os.system(comando)
        qr = Image.open(temp_path)
    except Exception as e:
        pass
    finally:
        os.close(fd)
        os.remove(temp_path)
    return qr


def leer_qr(path_imagen):
    '''Lee los datos de una imagen que contenga un codigo qr.'''
    from zbarlight import scan_codes
    ret = ""

    with open(path_imagen, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    codes = scan_codes('qrcode', image)
    if codes is not None and len(codes):
        ret = codes[0].decode("utf8")
    return ret


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
