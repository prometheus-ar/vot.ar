#!/usr/bin/env python
# -*- coding: utf-8 -*-
import optparse

from base64 import b64decode
from json import loads
from PIL import Image

from msa import get_logger
from msa.core.clases import Seleccion, Apertura, Recuento, Autoridad
from msa.core.constants import DPI_VOTO_ALTA, DPI_VOTO_BAJA
from msa.core.imaging import get_dpi_boletas, ImagenPrueba
from msa.core.ipc.server.daemon import Daemon
from msa.core.serial.printer import obtener_impresora
from msa.core.settings import IMPRESION_HD_APERTURA, IMPRESION_HD_CIERRE
from msa.helpers import levantar_locales


logger = get_logger("print_or_cache")
levantar_locales()


def run(args):
    printer = obtener_impresora()
    if args.serialized is None or not args.serialized:
        logger.debug("Corriendo proceso de impresion o cache de impresion")
        logger.debug(args)
        image_file = open(args.filepath)
        data = image_file.read()
        size = [int(num) for num in args.size.split(",")]
        dpi = tuple([int(num) for num in args.dpi.split(",")])
        image = Image.fromstring(args.mode, size, data)
        printer.imprimir_image(image, dpi, args.transpose, args.compress,
                               args.only_buffer)
    else:
        extra_data = loads(b64decode(args.extra_data))
        if args.tipo_tag == "Seleccion":
            boleta = Seleccion.desde_string(args.tag)
            image = boleta.a_imagen()
            dpi = get_dpi_boletas()
        elif args.tipo_tag == "Apertura":
            boleta = Apertura.desde_tag(b64decode(args.tag))
            autoridades = boleta.autoridades
            image = boleta.a_imagen()
            dpi = DPI_VOTO_ALTA if IMPRESION_HD_APERTURA else DPI_VOTO_BAJA
        elif args.tipo_tag == "Recuento":
            boleta = Recuento.desde_tag(b64decode(args.tag))
            autoridades = extra_data.get('autoridades')
            if autoridades is not None:
                for autoridad in autoridades:
                    boleta.autoridades.append(Autoridad.desde_dict(autoridad))
            boleta.hora = extra_data['hora']
            image = boleta.a_imagen(extra_data['tipo_acta'])
            dpi = DPI_VOTO_ALTA if IMPRESION_HD_CIERRE else DPI_VOTO_BAJA
        elif args.tipo_tag == "Prueba":
            dpi = DPI_VOTO_ALTA
            image = ImagenPrueba(hd=True).render_image()

    printer.imprimir_image(image, dpi, args.transpose, args.compress,
                           args.only_buffer)

def main(args):
    daemon = Daemon('/tmp/print-pseudodaemon.pid')
    daemon.run = run
    daemon.start(args)
    logger.info("finished for good")

if __name__ == "__main__":
    parser = optparse.OptionParser(
        description='Imprime las imagenes directo a la impresora.')

    parser.add_option('--filepath', dest='filepath', help='Ruta de la imagen')
    parser.add_option('--mode', dest='mode', help='Modo de la imagen')
    parser.add_option('--dpi', dest='dpi', help='Resolucion en dpi')
    parser.add_option('--size', dest='size', help='Tamaño de la imagen')
    parser.add_option('--transpose', dest='transpose', action='store_true',
                        help='Transpone la imagen' )
    parser.add_option('--compress', dest='compress', action='store_true',
                        help='Comprime la imagen' )
    parser.add_option('--only_buffer', dest='only_buffer', action='store_true',
                        help='Solo carga la imagen en el buffer, no imprime')
    parser.add_option('--no_spawn', dest='no_spawn', action='store_true',
                        help='No demoniza el proceso')

    parser.add_option('--serialized', dest='serialized', action='store_true',
                        help='proceso de impresion serializado')
    parser.add_option('--tipo_tag', dest='tipo_tag', help='Tipo de tag')
    parser.add_option('--tag', dest='tag', help='datos del tag')
    parser.add_option('--extra_data', dest='extra_data',
                      help='data extra para la impresion')

    (options, args) = parser.parse_args()

    if options.no_spawn:
        run(options)
    else:
        main(options)
