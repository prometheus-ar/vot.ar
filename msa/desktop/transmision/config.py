#-*- coding:utf-8 -*-

from ConfigParser import SafeConfigParser

from msa import get_logger
from msa.desktop.transmision import settings


logger = get_logger("config-transmision")


class Configuracion(SafeConfigParser):

    DEFAULT_CONFIG = {'timeout': '60',
                      'host': 'transmision.comicio.com.ar',
                      'host_certs': 'operaciones.comicio.com.ar',
                      'debug': 'true',
                      'usar_lock': 'true',
                      'glade_file': 'TransmisionApp.glade',
                      'key_file': '.',
                      'cert_file': '.',
                      'ca_file': '.',
                      'validar_datos': 'false'}

    DEFAULT_SECTION = 'DEFAULT'

    def __init__(self, config_file=None):
        if config_file is None:
            config_file = settings.CONFIG_FILE
        logger.debug("levantando la config %s", config_file)

        SafeConfigParser.__init__(self, Configuracion.DEFAULT_CONFIG)
        self.config_file = config_file
        self.section = Configuracion.DEFAULT_SECTION
        self.reload_options()

    def reload_options(self):
        self.read(self.config_file)
        self.DEBUG = self.getboolean(self.section, 'debug')
        self.GLADE_FILE = self.get_option('glade_file')
        self.HOST = self.get_option('host')
        self.HOST_CERTS = self.get_option('host_certs')
        self.TIMEOUT = self.get_option('timeout')
        self.USAR_LOCK = self.get_option('usar_lock')
        self.KEY_FILE = self.get_option('key_file')
        self.CERT_FILE = self.get_option('cert_file')
        self.CA_FILE = self.get_option('ca_file')
        self.VALIDAR_DATOS = self.get_option('validar_datos')

    def get_option(self, option):
        return self.get(self.section, option)

    def set_option(self, option, value):
        self.set(self.section, option, value)

    def write_options(self):
        with open(self.config_file, 'wb') as configfile:
            self.write(configfile)
        self.reload_options()
