"""Helpers para el modulo Asistida."""
from datetime import datetime

from msa.modulos.asistida.constants import TIMEOUT_BEEP


def ultimo_beep(controlador):
    if controlador.ultima_tecla is not None:
        time_diff = datetime.now() - controlador.ultima_tecla
        if time_diff.total_seconds() > TIMEOUT_BEEP:
            controlador.ultima_tecla = None
            controlador.asistente.recordar()
    return True
