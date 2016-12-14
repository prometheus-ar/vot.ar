# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Settings para numpacker
FAST_PACKING = False  # Indica si se usan las funciones rápidas para
                      # pack|unpack
SMART_PACKING = True  # Indica si se usan las funciones de smart packing

CANTIDAD_BITS_PACKER = 9  # Cantidad de bits por numero en numpacker

try:
    from msa.core.packing.settings_local import *
except ImportError:
    pass
