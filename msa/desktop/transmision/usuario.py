# -*- coding: utf-8 -*-
from ojota import Ojota


class Usuario(Ojota):

    pk_field = 'nombre_usuario'
    default_order = 'nombre_usuario'
    required_fields = ('nombre_usuario', 'clave', 'ubicacion')

    def __repr__(self):
        return self.nombre_usuario

