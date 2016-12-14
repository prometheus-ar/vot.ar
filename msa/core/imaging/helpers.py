# -*- coding: utf-8 -*-
from io import BytesIO

from jinja2 import Environment, FileSystemBytecodeCache, FileSystemLoader
from PIL import Image

from msa.core.constants import PATH_TEMPLATES_VARS
from msa.core.imaging.constants import DPI_VOTO_ALTA


def get_dpi_boletas():
    """Devuelve el DPI de la boleta segun la calidad configurada."""
    return DPI_VOTO_ALTA


def xml2pil(xml, width, height):
    # No sacar este import a la cabecera (con el resto) por que genera un
    # problema al correrlo en el server via mod_wsgi
    import cairo
    import gi
    gi.require_version('Rsvg', '2.0')
    from gi.repository.Rsvg import Handle
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    context = cairo.Context(surface)
    handle = Handle.new_from_data(xml.encode())
    handle.render_cairo(context)
    file_ = BytesIO()
    surface.write_to_png(file_)
    image = Image.open(file_)

    return image


def init_jinja():
    jinja_cache = FileSystemBytecodeCache()
    jinja_env = Environment(
        loader=FileSystemLoader([PATH_TEMPLATES_VARS]),
        bytecode_cache=jinja_cache)

    return jinja_env
