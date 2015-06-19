# -*- coding: utf-8 -*-
"""Algunas funciones útiles y variadas.
"""
import time

from msa.voto.sesion import get_sesion
from msa.settings import DEBUG


def analize(funcion):
    """ Funcion usada para tomar el tiempo de ejecucion de funciones.

        Para usarla, se debe importar utiles y agregar a la funcion a analizar
        el decorador @analize
    """
    sesion = get_sesion()

    def time_it(*lista_args):
        if DEBUG:
            tiempo1 = time.time()
            valor = funcion(*lista_args)
            tiempo2 = time.time()
            delta = tiempo2 - tiempo1
            params = (funcion.func_name, delta, valor)
            msg = "'%s()' ejecutada en %s seg. Retorna %s" % params
            if delta > 0.005:
                sesion.logger.debug(msg)
            else:
                sesion.logger.debug("tiempo de ejecucion despreciable: %s" %
                                    funcion)
        else:
            valor = funcion(*lista_args)
        return valor

    return time_it


def check_mod10(numero):
    """ Verifica el digito verificador usando el algoritmo de Luhn (mod10).

    (ver http://en.wikipedia.org/wiki/Luhn_formula)

    """

    numero = str(numero)
    # invierto el orden de los digitos
    numero = numero[::-1]

    remplazo = [0, 2, 4, 5, 8, 1, 3, 5, 7, 9]

    suma = 0
    par = False
    for digito in numero:
        digito = int(digito)
        if par:
            digito = remplazo[digito]
        suma += digito
        par = not par

    return (suma % 10) == 0


def valida_pin(pin):
    """ Valida el dígito verificador de un pin.

    Esta función es un wrapper que llama a la que realmente hace el cálculo. De
    esta forma es fácil cambiar el algoritmo sin tener que tocar todos los
    programas.

    """
    try:
        nro = int(pin)
        return check_mod10(nro) or nro == 1
    except:
        return False
