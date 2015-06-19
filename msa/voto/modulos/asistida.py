from msa.voto.constants import E_VOTANDO
from msa.voto.controllers.asistida import ControllerAsistida
from msa.voto.modulos.voto import ModuloVoto


class ModuloAsistida(ModuloVoto):
    def __init__(self, *args, **kwargs):
        ModuloVoto.__init__(self, *args, **kwargs)
        self.inicializar_locutor()
        # piso el tiempo de verificacion para que termine de hablar
        self.tiempo_verificacion = 25000

    def inicializar_locutor(self):
        if self.sesion.locutor is None:
            self.sesion.inicializar_locutor()
        if not self.sesion.locutor.is_alive():
            self.sesion.locutor.start()

    def set_controller(self):
        self.controller = ControllerAsistida(self)

    def _inicio(self, *args, **kwargs):
        ModuloVoto._inicio(self, *args, **kwargs)
        if self.estado == E_VOTANDO:
            self.controller.send_command("mostrar_teclado")

