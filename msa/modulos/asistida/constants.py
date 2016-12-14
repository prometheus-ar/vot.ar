"""Constantes para el modulo Asistida."""
from os.path import join

from msa.modulos.constants import PATH_SONIDOS_VOTO


PATH_TONOS = join(PATH_SONIDOS_VOTO, 'tonos')

TIMEOUT_BEEP = 4  # En segundos. tiempo que tarda en recordar apretar numeral
TIEMPO_ITER_TIMEOUT = 1  # En segundos. tiempo del timeout de chequeo del recordador
