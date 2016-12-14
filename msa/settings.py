# -*- coding:utf-8 -*-

DEBUG = False
MODO_DEMO = False
QUEMA = True

try:
    from msa.settings_local import *
except ImportError:
    pass
