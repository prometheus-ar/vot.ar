from msa.core.imaging import Imagen
from msa.core.imaging.constants import MEDIDAS_ACTA


class ImagenPrueba(Imagen):

    """Clase para la imagen de prueba de impresion."""

    def __init__(self):
        self.template = "test.svg"
        self.render_template()

    def generate_data(self):
        """Genera la data para enviar al template."""
        svg_args = {}
        svg_args['width'] = MEDIDAS_ACTA["ancho"]
        svg_args['height'] = MEDIDAS_ACTA["alto_recuento"]

        self.data = svg_args

        return svg_args


