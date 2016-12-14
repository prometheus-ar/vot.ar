# -*- coding: utf-8 -*-

_tipo_eleccion = None


def get_config(key):
    from msa.core.data import Configuracion
    config = Configuracion.one(key)

    if config is not None:
        config = config.valor

    return config
