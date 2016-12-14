# -*- coding: utf-8 -*-
from __future__ import absolute_import

# VOLUMEN_GENERAL = -1 no hace cambios en el volumen
VOLUMEN_GENERAL = 5  # el indice de VALORES_VOLUMEN
VOLUMEN_ESCRUTINIO_P2 = 0  # nivel de volumen que usamos para P2 en el
# escrutinio, ya que los parlantes de las P2 saturan

# Pausa entre frases de votacion asistida, en segundos
SPEECH_PAUSE = 3

try:
    from msa.core.audio.settings_local import *
except ImportError as e:
    pass
