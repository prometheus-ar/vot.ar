class MesaIncorrecta(Exception):

    """Mesa incorrecta."""
    pass


class MesaNoEncontrada(Exception):

    """Mesa no encontrada."""
    pass


class TemplateNoEncontrado(Exception):

    """Template no encontrado."""
    pass


class TipoQrErroneo(Exception):

    """Qr con tipo erroneo (diferente al esperado)."""
    pass


class QRMalformado(Exception):

    """Qr mal formado."""
    pass


class SerialRepetido(Exception):

    """Serial repetido dentro del recuento."""
    pass
