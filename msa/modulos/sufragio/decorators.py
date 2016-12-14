"""Decoradores del modulo sufragio."""
from msa.modulos.constants import E_VOTANDO


def solo_votando(func):
    """Decorador para que solo puedan hacer cosas cuando esta votanto."""
    def _inner(self, *args, **kwargs):
        if self.modulo.estado == E_VOTANDO:
            return func(self, *args, **kwargs)
        else:
            self.modulo.rampa.maestro()
    return _inner
