# coding: utf-8

_tipo_eleccion = None


def get_config(key):
    from msa.core.data import Configuracion
    config = Configuracion.one(key)

    if config is not None:
        config = config.valor

    return config


def get_tipo_elec(key):
    global _tipo_eleccion

    if _tipo_eleccion is None:
        _tipo_eleccion = get_config("tipo_eleccion")

    return _tipo_eleccion[key]

