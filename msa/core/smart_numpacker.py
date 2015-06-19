#-*- coding: utf-8 -*-

""" Módulo para codificar las actas de forma tal que se puedan almacenar en un
chip de 1K

"""

# Es el tamaño máximo en bits que se puede codificar antes de pasar al
# próximo modo
MAXBITS = 832
# Tamaño máximo para la lista de datos
MAXDATOS = 128
# Tamaño en bits de la posición de la parte más significativa
POSBITS = 7
# Offset mesa. Las mesas comienzan en 1001, por lo que se almacena la
# diferencia respecto al offset
OFFSETMESA = 0


def nro2cod(nro, bits_fijos, bits_variables, posicion):
    """ Codifica el nro devolviendo una tupla con la parte fija y la
        variable respectivamente.

        Si hay parte variable, la devuelve con la posicion que se pasa

    Tomo la parte menos significativa haciendo un and bit por bit por la
    mascara.

    Ej: bits_fijos=4 bits_variables=5 nro=173

    masc_menor_signif = 0b000001111 = 2 ** 4 - 1
                  nro = 0b010101101 = 173
    menor_signif      = 0b000001101 = 13


    Aplico en and y divido por 2 ** 4 para sacar la parte menos
    significativa (equivale a mayor_signif >> 4)

    masc_mayor_signif = 0b111110000 = 2 ** 9 - 2 ** 4
                  nro = 0b010101101 = 173
    mayor_signif      = 0b010100000 = 160
                      = 0b010100000 / 0b10000 = 160 / 2 ** 4 = 0b01010
    """
    masc_menor_signif = 2 ** bits_fijos - 1
    masc_mayor_signif = 2 ** (bits_fijos + bits_variables) - 2 ** bits_fijos

    menor_signif = nro & masc_menor_signif
    mayor_signif = (nro & masc_mayor_signif) / 2 ** bits_fijos

    parte_fija = bin(menor_signif)[2:].zfill(bits_fijos)

    parte_variable = None
    if mayor_signif > 0:
        # Agrego la posicion como POSBITS bits
        pos = bin(posicion)[2:].zfill(POSBITS)
        parte_variable = "%s%s" % (pos,
                                   bin(mayor_signif)[2:].zfill(bits_variables))

    return (parte_fija, parte_variable)


def binstr2strbytes(binstr):
    """ Convierte una cadena con binarios en un string de bytes que son
        representados por dicha cadena

        Ej: binstr2strbytes('010000110100101001000100') = 'CJD'
    """
    # Completo el string para que la longitud sea multiplo de 8
    if len(binstr) % 8 != 0:
        binstr = binstr + "0" * (8 - len(binstr) % 8)

    strbytes = ""
    for i in range(0, len(binstr), 8):
        byte = binstr[i:i + 8]
        strbytes = strbytes + chr(int(byte, 2))

    return strbytes


def strbytes2binstr(strbytes):
    """ Convierte un string de bytes en una cadena de binarios

        Ej: strbytes2binstr('PIGU') = ???
    """
    binstr = ""
    for c in strbytes:
        binstr = binstr + bin(ord(c))[2:].zfill(8)

    return binstr


def bitsfijos(modo):
    """ Devuelve la cantidad de bits fijos que tiene cada modo
        El modo puede ser:
            0: 3 bits fijos y 6 para los variables
            1: 4 bits fijos y 5 para los variables
            2: 5 bits fijos y 4 para los variables
            3: 6 bits fijos y 3 para los variables
    """
    if modo == 0:
        return 3
    elif modo == 1:
        return 4
    elif modo == 2:
        return 5
    elif modo == 3:
        return 6
    else:
        msg = "Modo %d no válido. Se admiten solamente los modos 0-4"
        raise NameError(msg % modo)


def bitsvariables(modo):
    """ Devuelve la cantidad de bits variables que tiene cada modo
        El modo puede ser:
            0: 3 bits fijos y 6 para los variables
            1: 4 bits fijos y 5 para los variables
            2: 5 bits fijos y 4 para los variables
            3: 6 bits fijos y 3 para los variables
    """
    if modo == 0:
        return 6
    elif modo == 1:
        return 5
    elif modo == 2:
        return 4
    elif modo == 3:
        return 3
    else:
        msg = "Modo %d no válido. Se admiten solamente los modos 0-4"
        raise NameError(msg % modo)


def pack(mesa, datos, modo=0, max_bits=MAXBITS):
    """ Codifica los datos enviados como lista de enteros

        Va a codificar los valores enteros con un ancho fijo dado por el
        modo. Los valores que necesiten mas digitos binarios se agregan al
        final con el formato id (POSBITS bits, es el orden en la lista) +los
        digitos mas significativos que requiere.
    """
    # Obtiene la cantidad de bits por modo
    bits_fijos = bitsfijos(modo)
    bits_var = bitsvariables(modo)

    binmesa = bin(mesa - OFFSETMESA)[2:].zfill(12)
    binmodo = bin(modo)[2:].zfill(2)
    bincantdatos = bin(len(datos))[2:].zfill(POSBITS)

    prefijo = "%s%s%s" % (binmesa, binmodo, bincantdatos)
    parte_fija = ""
    parte_variable = ""

    pos = 0
    for nro in datos:
        nrocod = nro2cod(nro, bits_fijos, bits_var, pos)
        parte_fija = parte_fija + nrocod[0]

        # Agrego a la parte variable si tiene parte variable
        if nrocod[1] is not None:
            parte_variable = parte_variable + nrocod[1]
        pos += 1

    strbytes = binstr2strbytes(prefijo + parte_fija + parte_variable)

    # Si la longitud del string generado es mayor al soportado prueba con
    # el siguiente modo. Si el modo supera 3, devuelve una excepción
    if len(strbytes) * 8 > max_bits:
        if modo < 3:
            return pack(mesa, datos, modo + 1, max_bits)
        else:
        # Si se probaron todos los modos levanta una excepción ya que
        # no va a entrar en el chip
            msg = "La codif en todos los modos superan la long max de %d bits"
            raise NameError(msg % max_bits)
    else:
        return strbytes


def unpack(strbytes):
    """ Decodifica los datos enviados como string de bytes

        Va a devolver una tupla con el número de mesa y la lista de valores
    """

    binstr = strbytes2binstr(strbytes)

    # La mesa ocupa los primeros 12 bits. Tiene un offset de OFFSETMESA por lo
    # que se le suman

    mesa = int(binstr[0:12], 2) + OFFSETMESA
    # El modo ocupa los bits 13 y 14
    modo = int(binstr[12:14], 2)
    # La cantidad de datos ocupa los bits 15-21
    cant_datos = int(binstr[14:21], 2)

    # Obtiene la cantidad de bits segun el modo
    bits_fijos = bitsfijos(modo)
    bits_var = bitsvariables(modo)

    # Los datos ocupan los bits 22-(22 + cant_datos * bits_fijos - 1)
    bindatos = binstr[21:21 + cant_datos * bits_fijos]

    datos = []
    for i in range(0, len(bindatos), bits_fijos):
        bindato = bindatos[i:i + bits_fijos]
        datos.append(int(bindato, 2))

    # A partir de eso vienen los datos variables es decir la direccion mas
    # los bits significativos de aquellos que los requieren
    bindatosvariables = binstr[21 + cant_datos * bits_fijos:]
    # Omito los 0 que se agregaron para completar el byte
    longitud_ajustada = len(bindatosvariables) / (POSBITS + bits_var) * \
        (POSBITS + bits_var)
    bindatosvariables = bindatosvariables[:longitud_ajustada]

    for i in range(0, len(bindatosvariables), POSBITS + bits_var):
        bindatovariable = bindatosvariables[i:i + POSBITS + bits_var]
        pos = int(bindatovariable[0:POSBITS], 2)
        valor = int(bindatovariable[POSBITS:], 2) * (2 ** bits_fijos)
        datos[pos] = datos[pos] + valor

    return (mesa, datos)


if __name__ == "__main__":
        import random
        # Pruebo generar varias actas para analizar la longitud y verificar que
        # funcione la codificacion y decodificacion
        for i in range(10):
            lista = []

            # Uso 3 cargos
            for cargo in range(3):
                acum = 0
                # Al primer candidato le pongo un random cuanto más
                # grande este random más desparejos van a ser los datos
                nro = random.randint(0, 150)
                lista.append(nro)
                acum += nro
                for votos in range(32):
                    # Al resto de los candidatos le asigno un
                    # aleatorio que sea a lo sumo 1/3 de lo que
                    # queda para llegar a 350 votos. Se puede jugar
                    # con el 1/3 para ver distintos tipos de
                    # distribuciones
                    nro = random.randint(0, (350 - acum) / 3)
                    lista.append(nro)
                    acum += nro

            strcod = pack(1234, lista)
            print "Lista: %s" % lista
            print "Lenght lista: %s" % len(lista)
            print "Longitud generada: %d bits \n" % (len(strcod) * 8)

            mesa, lista2 = unpack(strcod)
            if cmp(lista, lista2) != 0:
                msg = "No coinciden la original y la codificada y luego " \
                "decodificada"
                print msg
