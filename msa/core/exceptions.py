class MesaIncorrecta(Exception):

    """Mesa incorrecta."""
    pass


class MesaNoEncontrada(Exception):

    """Mesa no encontrada."""
    pass


class TipoQrErroneo(Exception):

    """Qr con tipo erroneo (diferente al esperado)."""
    pass


class QRMalformado(Exception):

    """Tag mal formado."""
    pass


class TagMalformado(Exception):

    """Qr mal formado."""
    pass


class SerialRepetido(Exception):

    """Serial repetido dentro del recuento."""
    pass
