# coding: utf-8
import sys

from gettext import translation

from msa import get_logger
from msa.settings import DEFAULT_LOCALE
try:
    from msa.voto.constants import NOMBRE_PO_VOTO
    from msa.voto.settings import PATH_LOCALE_VOTO
except ImportError:
    # En el caso de correr el armve_service.py para transmisión, en transmisión
    # no incluyo msa/voto y los import a msa.voto explotan.
    import os.path
    from msa.settings import PATH_RECURSOS
    NOMBRE_PO_VOTO = 'voto'
    PATH_LOCALE_VOTO = os.path.join(PATH_RECURSOS, 'voto', 'locale')


logger = get_logger("permisos")
_locale_actual = DEFAULT_LOCALE


def levantar_locales():
    reset_locales()


def reset_locales():
    cambiar_locale(DEFAULT_LOCALE)


def cambiar_locale(locale):
    global _locale_actual
    _locale_actual = locale
    language = translation(NOMBRE_PO_VOTO, PATH_LOCALE_VOTO, [locale])
    language.install()


def locale_actual():
    return _locale_actual


def ver_settings(modulo=None):
    if modulo is None:
        modulos = ["msa", "msa.core", "msa.voto", "msa.core.data"]
    else:
        modulos = [modulo]

    for modulo in modulos:
        print
        print "*" * 20,
        print modulo,
        print "*" * 20
        print
        __import__(modulo)
        get_module_settings(sys.modules[modulo])


def get_module_settings(module):
    if hasattr(module, "settings"):
        settings_keys = []
        for key in dir(module.settings):
            if not key.startswith("__") and type(
                    getattr(module.settings, key)) != type(module):
                settings_keys.append(key)

        #settings_local_keys = dir(module.settings_local)
        max_len = max([len(setting) for setting in settings_keys])
        #max_len_value = max([len(str(getattr(module.settings, setting))) for setting in settings_keys])
        for setting in settings_keys:
            if not setting.startswith("__"):
                attr = getattr(module.settings, setting)
                if not hasattr(attr, "__call__"):
                    print setting.ljust(max_len),
                    if hasattr(module, "settings_local"):
                        print "* " if hasattr(module.settings_local, setting) else "  ",
                    else:
                        print "  ",
                    print attr
    else:
        print "El modulo no tiene settings"

