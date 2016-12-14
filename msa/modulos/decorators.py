from msa.modulos import get_sesion


def requiere_mesa_abierta(func):
    def inner(self, *args, **kwargs):
        sesion = get_sesion()
        mesa = sesion.mesa
        if mesa is not None and mesa.clase == "Mesa":
            return func(self, *args, **kwargs)
        else:
            print("Para ejecutar este modulo debe tener abierta una mesa válida.")
            exit(1)
    return inner
