from msa.core.data.constants import TIPO_DOC


class Autoridad(object):

    """Autoridad de mesa."""

    def __init__(self, apellido='', nombre='', tipo_documento=None,
                 nro_documento=''):
        self.apellido = apellido
        self.nombre = nombre
        if tipo_documento is None:
            tipo_documento = 0
        self.tipo_documento = TIPO_DOC[int(tipo_documento)]
        self.nro_documento = nro_documento

    def a_dict(self):
        return {"nombre": self.nombre,
                "apellido": self.apellido,
                "tipo_documento": TIPO_DOC.index(self.tipo_documento),
                "nro_documento": self.nro_documento}

    @classmethod
    def desde_dict(cls, data):
        return cls(data['apellido'], data['nombre'], data["tipo_documento"],
                   data['nro_documento'])

    def __str__(self):
        return "%s, %s" % (self.apellido, self.nombre)

    def __repr__(self):
        return "%s, %s, %s, %s" % (self.apellido, self.nombre,
                                   self.tipo_documento, self.nro_documento)
