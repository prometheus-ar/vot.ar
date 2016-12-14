#!/usr/bin/env python3
from msa.modulos.calibrador import Modulo
from msa.modulos.constants import MODULO_CALIBRADOR


def main():
    """Corre el modulo calibrador solamente."""
    modulo = Modulo(MODULO_CALIBRADOR)
    modulo.main()


if __name__ == '__main__':
    main()
