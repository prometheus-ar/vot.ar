#!/usr/bin/env python3
"""Script de inicio del sistema.

Corre los modulos, maneja la calibracion, la navegacion entre modulos y el
Apagado de la maquina.
"""
from msa.modulos.base.disk_runner import DiskRunner
from msa.modulos.constants import MODULO_INICIO
from msa.modulos.sufragio.constants import MODULOS_APLICACION


def main():
    """Funcion de entrada del sistema de la BUE. Bienvenidos."""
    modulos_startup = [MODULO_INICIO]

    runner = DiskRunner(modulos_startup, MODULOS_APLICACION)
    runner.run()

if __name__ == '__main__':
    main()
