"""Controlador del modulo inicio"""
from msa.modulos.base.actions import BaseActionController
from msa.modulos.base.controlador import ControladorBase
from msa.modulos.inicio.constants import TEXTOS


class Controlador(ControladorBase):

    """Controller para el modulo inicio."""

    def __init__(self, modulo):
        """Constructir de el controlador inicio."""
        super(Controlador, self).__init__(modulo)
        self.set_actions(BaseActionController(self))
        self.textos = TEXTOS

    def document_ready(self, data):
        """Callback que se llama en el document.ready del browser."""
        self.modulo._inicio()
        self.modulo._pantalla_principal()
