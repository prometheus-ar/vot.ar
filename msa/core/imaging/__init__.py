from base64 import encodestring

from msa.core.config_manager import Config
from msa.core.imaging.helpers import init_jinja, xml2pil
from msa.core.logging import get_logger


logger = get_logger("imaging")
jinja_env = init_jinja()


class Imagen(object):

    """Clase base para las imagenes del modulo."""

    def generate_data(self):
        """Genera la data para enviar al template."""
        raise NotImplementedError("You must implement on subclass")

    def render_template(self):
        self.rendered_template = jinja_env.get_template(self.template)

    def render_svg(self):
        """Renderiza el SVG."""
        data = self.generate_data()
        xml = self.rendered_template.render(**data)
        return xml

    def render_image(self):
        """Renderiza la imagen."""
        xml = self.render_svg()
        return xml2pil(xml, self.data['width'], self.data['height'])

    def _get_img_b64(self, img_path):
        """Devuelve la imagen en base64 formato browser."""
        image = open(img_path, 'rb')
        img_data = image.read()
        img_data = encodestring(img_data)
        image.close()
        img_link = "data:image/png;base64,%s" % img_data.decode()
        return img_link

    def config(self, key, id_ubicacion=None):
        self._config = Config(["imaging"], id_ubicacion)
        value, file_ = self._config.data(key)
        logger.debug("Trayendo config {}: {} desde {}".format(key, value,
                                                              file_))
        return value
