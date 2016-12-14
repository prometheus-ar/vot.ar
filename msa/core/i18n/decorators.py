# -*- coding: utf-8 -*-
from __future__ import absolute_import
from msa.core.i18n import (reset_locales, cambiar_locale, locale_actual,
                           po_actual, setear_po)


def forzar_idioma(locale):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            locale = locale_actual()
            po = po_actual()
            reset_locales()

            response = f(*args, **kwargs)
            cambiar_locale(locale)
            setear_po(po)
            return response

        return wrapped_f
    return wrap
