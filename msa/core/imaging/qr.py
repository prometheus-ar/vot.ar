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
                 .replace("/", "") \
                 .replace("Ñ", "N")
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
