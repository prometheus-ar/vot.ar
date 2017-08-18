from argparse import ArgumentParser

from msa.modulos.base import App
from msa.modulos.constants import MODULO_CALIBRADOR


class DiskRunner():
    """Corre la aplicacion en el contexto del disco."""
    def __init__(self, modulos_startup, modulos_aplicacion, calibracion=True):
        """Constructor del ejecutor de aplicaciones.

        Argumentos:
            modulos_startup -- los modulos a ejecutar al inicio.
            modulos_aplicacion -- los modulos de la aplicacion.
        """
        self.app = None
        self.con_calibracion = calibracion

        self.modulos_startup = modulos_startup
        self.modulos_aplicacion = modulos_aplicacion
        if calibracion:
            self.modulos_aplicacion.append(MODULO_CALIBRADOR)
        self.init_parser()

    def init_parser(self):
        """Inicializa el parseador de argumentos."""
        self.parser = ArgumentParser("run.py")
        self.set_args()
        self.parse_args()

    def set_args(self):
        """Establece los argumentos aceptados por el parser."""
        if self.con_calibracion:
            self.parser.add_argument(
                '-c', '--calibrar', action='store_true', default=False,
                help="Ejecuta el modulo de calibracion en primera instancia.")

    def parse_args(self):
        """Parsea los argumentos y actua en consecuencia."""
        args = self.parser.parse_args()

        if self.con_calibracion and args.calibrar:
            self.modulos_startup.append(MODULO_CALIBRADOR)

        return args

    def init_app(self):
        """Inicializa la aplicacion"""
        self.app = App(self.modulos_startup, self.modulos_aplicacion)

    def run(self):
        """Corre la aplicacion."""
        self.init_app()
        self.app.run()
