from msa.core.imaging import Imagen


class ImagenReversoBoleta(Imagen):

    """Clase para la imagen del reverso de la boleta."""

    def __init__(self, config):
        self.template = "reverso/base.svg"
        self.render_template()
        self.data = config

    def generate_data(self):
        return self.data
