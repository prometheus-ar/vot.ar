from os.path import join, exists

from msa.core.data.settings import JUEGO_DE_DATOS
from msa.voto.settings import EXT_IMG_VOTO, PATH_TEMPLATES_VOTO


def _image_name(cod_candidato):
    imagen = None
    if cod_candidato is not None:
        imagen = "%s.%s" % (cod_candidato, EXT_IMG_VOTO)
        path_foto = join(PATH_TEMPLATES_VOTO, "imagenes_candidaturas",
                         JUEGO_DE_DATOS, imagen)
        if not exists(path_foto):
            imagen = None
    return imagen
