"""Contiene los decoradores del modulo base."""
rampa_corriendo = False


def semaforo(func):
    """Decorador que hace que no se puedan hacer 2 cosas al mismo tiempo.

    La idea es evitar las race conditions que teniamos con la rampa anterior.
    """
    def _inner(self, *args, **kwargs):
        global rampa_corriendo
        if not rampa_corriendo:
            rampa_corriendo = True
            func(self, *args, **kwargs)
            rampa_corriendo = False
    return _inner

def si_tiene_conexion(func):
    def _inner(self, *args, **kwargs):
        if self.tiene_conexion:
            return func(self, *args, **kwargs)
    return _inner
