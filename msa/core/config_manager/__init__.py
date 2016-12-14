from os.path import join, exists

from yaml import load

from msa.constants import PATH_CONFIGS
from msa.core.config_manager.constants import (DEFAULT_FILE, EXTENSION,
                                               OVERRIDE_FILE)
from msa.core.config_manager.settings import NIVELES_CONFIG
from msa.core.data import Ubicacion


class Config():

    """Maneja la carga de configuraciones para modulos y ubicación."""

    def __init__(self, modulos, id_ubicacion=None):
        """Constructor.

        Argumentos:
            modulos -- una lista de modulos
            id_ubicacion -- la ubicacion de la mesa de la que traemos las
                settings
        """
        self._data_dict = {}
        self.modulos = modulos
        self.id_ubicacion = id_ubicacion
        self.cargar_datos()

    def data(self, key):
        config = None
        file_ = None

        value = self._data_dict.get(key)
        if value is not None:
            config, file_ = value

        return config, file_

    def val(self, key):
        """Devuelve el valor de una key del diccionario de settings."""
        value, file_ = self.data(key)
        return value

    def from_file(self, key):
        """Devuelve el valor de una key del diccionario de settings."""
        value, file_ = self.data(key)
        return file_

    def _load_file(self, modulo, file_name):
        """Devuelve las settings de un archivo en especifico.

        Argumentos:
            file_data -- una tupla que contiene el nombre del modulo y el
            nombre del archivo
        """
        settings = None
        path = join(PATH_CONFIGS, modulo, file_name)
        if exists(path):
            with open(path, 'r') as file_:
                temp_settings = load(file_.read())
                settings = {}
                for key, value in temp_settings.items():
                    settings[key] = (value, file_name)

        return settings

    def cargar_datos(self):
        """Carga los datos en el diccionario."""
        data_dict = {}
        archivos = self.generar_lista_archivos()
        for modulo in self.modulos:
            dict_modulo = {}
            for archivo in archivos:
                local_dict = self._load_file(modulo, archivo)
                if local_dict is not None:
                    dict_modulo.update(local_dict)

            # si la key existe en otro modulo más prioritario no la agregamos.
            for key in dict_modulo.keys():
                if key not in data_dict:
                    data_dict[key] = dict_modulo[key]
        self._data_dict = data_dict

    def generar_lista_archivos(self):
        """Genera la lista de archivos de los cuales puede sacar settings."""
        files = []
        default = self._generar_nombre(DEFAULT_FILE)
        files.append(default)

        ubic_files = []
        # Configuraciones por ubicacion.
        ubicacion = Ubicacion.one(codigo=self.id_ubicacion)
        while ubicacion is not None:
            if ubicacion.clase in NIVELES_CONFIG:
                file_ = self._generar_nombre(ubicacion.codigo)
                ubic_files.append(file_)
            ubicacion = ubicacion.parent

        ubic_files.reverse()
        files += ubic_files

        local = self._generar_nombre(OVERRIDE_FILE)
        files.append(local)

        return files

    def _generar_nombre(self, nombre):
        """Genera el nombre del archivo."""
        filename = "{}.{}".format(nombre, EXTENSION)
        return filename
