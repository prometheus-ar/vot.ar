# -*- coding: utf-8 -*-
from __future__ import absolute_import
from gettext import translation

from msa.core.i18n.settings import DEFAULT_LOCALE
from msa.core.i18n.constants import NOMBRE_PO_VOTO, PATH_LOCALE_VOTO


_locale_actual = DEFAULT_LOCALE
_po_actual = NOMBRE_PO_VOTO


def levantar_locales():
    reset_locales()


def reset_locales():
    setear_po(NOMBRE_PO_VOTO)
    cambiar_locale(DEFAULT_LOCALE)


def cambiar_locale(locale):
    global _locale_actual
    _locale_actual = locale
    instalar_lenguaje()


def instalar_lenguaje():
    locale = locale_actual()
    nombre_po = po_actual()
    language = translation(nombre_po, PATH_LOCALE_VOTO, [locale])
    language.install()


def locale_actual():
    return _locale_actual


def setear_po(nombre_po):
    global _po_actual
    _po_actual = nombre_po


def cambiar_po(nombre_po):
    setear_po(nombre_po)
    instalar_lenguaje()


def po_actual():
    return _po_actual
