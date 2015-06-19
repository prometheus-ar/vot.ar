# -*- coding: utf-8 -*-
import os
import shutil
import sys
from datetime import datetime
from random import choice, shuffle

import pyudev
import usb.core

from msa import get_logger
from msa.core.data.settings import PATH_DATOS_JSON
from msa.core.settings import (IMPRESION_USBLP, USB_PRINTER_PRODUCT_ID,
                               USB_PRINTER_VENDOR_ID)
from msa.settings import PATH_CODIGO, PATH_REPO_RECURSOS, PATH_TTS


logger = get_logger("helpers")


def touch(path):
    """
    Crea un archivo vacío
    """
    with open(path, 'a'):
        os.utime(path, None)


def crear_juego(nombre):
    """
    Crea un nuevo juego de datos
    """
    from msa.voto.settings import PATH_FOTOS_ORIGINALES
    archivos_sql = ['adhesiones_cargos.sql', 'adhesiones.sql',
                    'candidaturas.sql',
                    'cargo_candidatura_ubicacion.sql', 'cargos.sql',
                    'configuraciones.sql', 'dhont.sql',
                    'estados.sql',
                    'modulos.sql', 'no_cargo_ubicacion.sql',
                    'passwords.sql', 'permisos.sql',
                    'planillas.sql', 'puntos_de_carga.sql',
                    'ubicaciones.sql', 'usuarios_permisos.sql',
                    'usuarios.sql']
    print("Generando juego de datos %s" % nombre)
    dir_json = os.path.join(PATH_CODIGO, 'datos_json', nombre)
    if os.path.exists(dir_json):
        print(dir_json)
        print("Ya existe un juego de datos con ese nombre")
    else:
        print("Creando carpetas")
        os.mkdir(dir_json)
        dir_sql = os.path.join(PATH_CODIGO, "deploy/database/scripts/dml/",
                               nombre)
        os.mkdir(dir_sql)
        print("Agregando sql vacíos...")
        for archivo in archivos_sql:
            archivo_path = os.path.join(dir_sql, archivo)
            touch(archivo_path)
        dir_fotos = os.path.join(PATH_FOTOS_ORIGINALES, nombre)
        os.mkdir(dir_fotos)
        dir_imgs_base = os.path.join(PATH_REPO_RECURSOS, 'imagenes_base',
                                     nombre)
        os.mkdir(dir_imgs_base)
        dir_datos_base = os.path.join(PATH_REPO_RECURSOS, 'datos', nombre)
        os.mkdir(dir_datos_base)
        dir_tts = os.path.join(PATH_TTS, nombre)
        os.mkdir(dir_tts)

        print("Copiando JSONs desde el juego de datos actual")
        jsons = ("TemplatesImpresion", "TemplatesMap", "Speech")
        for file_ in jsons:
            origen = os.path.join(PATH_DATOS_JSON, "%s.json" % file_)
            destino = dir_json

            shutil.copy(origen, destino)

        print("No olvides cambiar el juego de datos en las settings")


def eliminar_juego(nombre):
    """
    Elimina un juego de datos existente
    """
    from msa.voto.settings import PATH_FOTOS_ORIGINALES
    print("Eliminando juego de datos %s" % nombre)
    dir_json = os.path.join(PATH_CODIGO, 'datos_json', nombre)
    if os.path.exists(dir_json):
        shutil.rmtree(dir_json)
    dir_sql = os.path.join(PATH_CODIGO, "deploy/database/scripts/dml/",
                           nombre)
    if os.path.exists(dir_sql):
        shutil.rmtree(dir_sql)
    dir_fotos = os.path.join(PATH_FOTOS_ORIGINALES, nombre)
    if os.path.exists(dir_fotos):
        shutil.rmtree(dir_fotos)
    dir_tts = os.path.join(PATH_TTS, nombre)
    if os.path.exists(dir_tts):
        shutil.rmtree(dir_tts)
    dir_imgs_base = os.path.join(PATH_REPO_RECURSOS, 'imagenes_base', nombre)
    if os.path.exists(dir_imgs_base):
        shutil.rmtree(dir_imgs_base)
    dir_datos_base = os.path.join(PATH_REPO_RECURSOS, 'datos', nombre)
    if os.path.exists(dir_datos_base):
        shutil.rmtree(dir_datos_base)

    print("Juego {} eliminado").format(nombre)


def smart_title(string):
    """
    Tituliza un string sin tener en cuenta ciertas palabras
    (ex. preposiciones, etc.)
    """
    EXCEPCIONES = ('a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 'del',
                   'durante', 'e', 'en', 'entre', 'hacia', 'hasta', 'mediante', 'y',
                   'para', 'por', 'según', 'segun', 'sin', 'so', 'sobre',
                   'tras', 'versus', 'via', 'la', 'los')
    SIGLAS = ('ti', 'mst', 'pro', '(aps)', '(aupec)', '(mst)',
              'ucr', 'unen', 'ps')
    # Primero titulizamos el string
    titleized = string.title()
    splitted = titleized.split(' ')
    result = []
    # Chequeamos si hay algo que esté en la lista de excepciones
    for t in splitted:
        if t.lower() in EXCEPCIONES and splitted.index(t) != 0:
            result.append(t.lower())
        elif t.lower() in SIGLAS:
            result.append(t.upper())
        else:
            result.append(t)

    return ' '.join(result)


def get_active_ports():
    """ Devuelve una lista con los dispositivos FTDIs conectados """

    cnxt = pyudev.Context()
    l = cnxt.list_devices(subsystem='tty', ID_VENDOR='FTDI')
    return sorted(l, key=lambda device: device.sys_number)


def detect_printer_port():
    """ Devuelve el puerto al cual esta conectada la impresora.
        Puerto ALTO (sys_number=01)
    """
    _printer_port = get_usb_printer_port() if IMPRESION_USBLP else None

    if _printer_port is None:
        devices = get_active_ports()
        _printer_port = devices[-1].device_node if devices else None

    return _printer_port


def get_usb_printer_port():
    """ Devuelve el puerto usb al cual esta conectada la impresora.
        Sino devuelve None
    """

    return usb.core.find(idVendor=USB_PRINTER_VENDOR_ID,
                         idProduct=USB_PRINTER_PRODUCT_ID)


def get_timestamp(hora=None):
    """ Devuelve un string con un datetime.

    Argumentos:
        - hora: un objeto datetime.datetime con la hora a convertir
            (default=None)

    Devuelve:
        Un string con el timestamp correspondiente a la hora recibida. Si el
        parámetro es None, devuelve la hora actual.

    """

    if hora is None:
        hora = datetime.now()

    hora_str = hora.isoformat(' ')
    # Elimino los microsegundos
    if '.' in hora_str:
        hora_str = hora_str.split('.')[0]

    return hora_str


def get_timeversion(utc=True):
    """
    Devuelve un string en formato: 20140925172209
    con el timestamp actual. Se usa UTC por default,
    puede devolver el timezone actual
    """
    if utc:
        timestamp = datetime.utcnow()
    else:
        timestamp = datetime.now()

    timeversion = timestamp.strftime('%Y%m%d%H%M%S')

    return timeversion


def parse_timeversion(timeversion):
    """
    Parse un timeversion y devuelve un objeto
    datetime
    """
    now = datetime.strptime(timeversion, '%Y%m%d%H%M%S')

    return now


def lock(lock_file):
    """ Genera un lockeo de proceso usando un archivo.

    Si el archivo cuyo nombre se recibió por parametro existe, termina la
    ejecución porque significa que hay otro proceso ejecutando. Si no existe lo
    crea, y de esta forma lockea al próximo proceso que quiera ejecutarse
    (siempre y cuando tengan el mismo nombre de archivo de lockeo)

    Argumentos:
        lock_file - Nombre del archivo de lockeo

    """

    # Verifico que no haya otro receptor corriendo
    if os.path.exists(lock_file):
        logger.info("Hay otro proceso lockeado...")
        sys.exit(1)

    # Genero elarchivo de lockeo
    lock = open(lock_file, 'w')
    lock.write('corriendo...')
    lock.close()


def unlock(lock_file):
    """Elimina el archivo de lockeo.

    En base al parámetro recibido, elimina el archivo de lockeo.

    TODO: que maneje las excepciones si no existe el archivo, no se peude
    borrar, etc.

    Argumentos:
        lock_file - Nombre del archivo de lockeo a eliminar.

    """

    os.remove(lock_file)


def valida_nro_planilla(nro_planilla):
    """ Valida el dígito verificador del nro de planilla.

    Esta función es un wrapper que llama a la que realmente hace el cálculo. De
    esta forma es fácil cambiar el algoritmo sin tener que tocar todos los
    programas.

    """
    try:
        nro = int(nro_planilla)
        return check_mod10(nro)
    except:
        return False


def check_mod10(numero):
    """ Verifica el digito verificador usando el algoritmo de Luhn (mod10).

    (ver http://en.wikipedia.org/wiki/Luhn_formula)

    """

    numero = str(numero)
    numero = numero[::-1]  # invierto el orden de los digitos

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


def get_lista_mod10(digitos=4, cant=None):
    """Genera una lista con números mod10 válidos.

    Argumentos:
     digitos - la cantidad de digitos de los números generados (default=2)

    Devuelve:
     Una lista de códigos mod10 válidos. No devuelve números sino strings, con
     ceros a la izquierda hasta completar el largo de codigo pedido.

    """
    lista = []
    temp = '%%0%dd' % digitos
    if digitos >= 2:
        for n in range(1, 10 ** digitos):
            if check_mod10(n):
                lista.append(temp % n)
    shuffle(lista)

    return lista[:cant] if cant is not None else lista


def generar_pin():
    letras = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'P', 'Q', 'R',
              'S', 'T', 'U', 'W', 'X', 'Z']
    numeros = range(1, 10)
    pin = "%s%s%s%d%d%d" % (choice(letras), choice(letras), choice(letras),
                            choice(numeros), choice(numeros), choice(numeros))
    return pin


def generar_pines(cantidad=10):
    pines = []
    for i in xrange(cantidad):
        pin = generar_pin()
        pines.append(pin)
    return pines
