"""
Clases bases para el manejo del sistema de plugins de la aplicacion.
"""
from importlib import import_module
from inspect import getmembers

from msa.modulos.constants import PATH_MODULOS, MODULOS_PLUGINS
from msa.core.logging import get_logger


logger = get_logger("plugin_manager")
# variable de modulo que contiene los plugins habilitados
_enabled_plugins = {}


class PluginManager():
    """Maneja los plugins de la aplicacion."""
    @classmethod
    def enabled(cls, nombre):
        """Nos dice si un plugin esta habilitado o no.

        Argumentos:
            nombre -- nombre del plugin.
        """
        return nombre in _enabled_plugins

    @classmethod
    def get_plugin(self, nombre):
        """Devuelve la instancia del plugin registrado.

        Argumentos:
            nombre -- nombre del plugin.
        """
        return _enabled_plugins[nombre]

    @classmethod
    def run_if_enabled(cls, nombre_plugin, nombre_metodo, args=None,
                       kwargs=None):
        """
        Corre una funcion de un plugin en caso de que el mismo esté habilitado.

        Argumentos:
            nombre_plugin -- el nombre del plugin.
            nombre_metodo -- el nombre del metodo que se quiere ejecutar.
            args -- los argumentos posicionales que se le pasan al metodo.
            kwargs -- los argumentos con nombre que se le pasan al metodo.
        """
        ret = None
        logger.debug("Intentando ejecutar el metodo {} del plugin {}"
                     .format(nombre_metodo, nombre_plugin))

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        # si el plugin está habilitado
        if cls.enabled(nombre_plugin):
            plugin = cls.get_plugin(nombre_plugin)
            # y el metodo existe
            if hasattr(plugin, nombre_metodo):
                # instanciamos traemos el metodo
                metodo = getattr(plugin, nombre_metodo)
                # y lo llamamos
                logger.debug("Ejecutando metodo")
                ret = metodo(*args, **kwargs)
            else:
                logger.debug("El plugin {} no contiene el metodo {}"
                             .format(nombre_plugin, nombre_metodo))
        else:
            logger.debug("El plugin {} no está habilitado"
                         .format(nombre_plugin))
        return ret

    @classmethod
    def autoregister(cls):
        """Registra todos los plugins que estan presentes."""
        detector = PluginDetector()
        # Traemos todas las clases
        plugins = detector.get_clases()
        for plugin in plugins:
            # instanciamos cada una y la registramos.
            instance = plugin()
            instance.register()


class PluginDetector():

    """Clase para manejar la deteccion automatica de plugins."""

    def get_pkgs(self):
        """Devuelve los paquetes de los plugins de cada modulo."""
        pkgs = []
        for modulo in MODULOS_PLUGINS:
            # quito la coma del submodulo
            nombre = modulo.split(",")[0]
            from os import listdir
            from os.path import join, isdir

            path_plugin = join(PATH_MODULOS, modulo, "plugins")
            try:
                dirs = []
                for file_ in listdir(path_plugin):
                    if isdir(join(path_plugin, file_)):
                        dirs.append(file_)

                for dir_ in dirs:
                    nombre = "msa.modulos.{}.plugins.{}".format(modulo, dir_)
                    try:
                        pkg = import_module(nombre)
                        # si es el submodulo se repite y no queremos tener mas
                        # de una vez cada una de las clases
                        if pkg not in pkgs:
                            pkgs.append(pkg)
                    except ImportError:
                        pass
            except FileNotFoundError:
                pass

        return pkgs

    def get_clases(self):
        """Devuelve las clases de los plugins."""
        # la lista de las clases
        clases = []
        # traemos todos los paquetes que pueden tener plugins
        pkgs = self.get_pkgs()
        # los recorremos y buscamos si tienen plugins
        for pkg in pkgs:
            plugins = self.get_plugins_pkg(pkg)
            # los agregamos a la lista
            clases.extend(plugins)
        return clases

    def get_plugins_pkg(self, package):
        """Devuelve los plugins de cada paquete."""
        hijos = []
        # Traemos todos los miembros del paquete
        items = getmembers(package)
        # Los recorremos y agarramos todos los plugins del paquete
        for item in items:
            try:
                if item[0] != "Plugin" and issubclass(item[1], Plugin):
                    hijos.append(item[1])
            except TypeError:
                pass
        return hijos


class Plugin():
    """Clase base de cada plugin. Sabe hacer lo que saben hacer los plugins."""
    def __init__(self):
        """Constructor del plugin."""
        self.nombre = None

    def register(self):
        """Registra el plugin."""
        if self.nombre is not None:
            _enabled_plugins[self.nombre] = self

    def unregister(self):
        """Desregistra el plugin."""
        if self.enabled(self.nombre):
            del _enabled_plugins[self.nombre]


class PluginDecorator():
    """Decorador base para los decoradores de plugins."""
    def __init__(self, nombre_plugin, nombre_metodo):
        self.nombre_plugin = nombre_plugin
        self.nombre_metodo = nombre_metodo

        self.manager = PluginManager

    def run_plugin(self):
        self.manager.run_if_enabled(self.nombre_plugin, self.nombre_metodo)


class plugin_before(PluginDecorator):

    """Decorador para ejecutar una funcion de un plugin antes de un metodo."""

    def __call__(self, func):
        def _wrapped(*args):
            self.run_plugin()
            func(*args)
        return _wrapped


class plugin_after(PluginDecorator):

    """Decorador para ejecutar una funcion de un plugin despues de un metodo."""

    def __call__(self, func):
        def _wrapped(*args):
            func(*args)
            self.run_plugin()
        return _wrapped
