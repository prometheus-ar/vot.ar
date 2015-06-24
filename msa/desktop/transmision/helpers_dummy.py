#-*- coding:utf-8 -*-

from ojota import current_data_code
from random import randint
from shutil import copy
from time import sleep

from msa.core.constants import CIERRE_TRANSMISION
from msa.core.clases import Recuento
from msa.core.data import Ubicacion
from msa.core.data.candidaturas import Categoria
from msa.desktop.transmision.usuario import Usuario


###
#   Helpers para la clase de conexión dummy
###
def get_usuario(nombre_usuario):
    return Usuario.one(nombre_usuario=nombre_usuario)


def get_estado_mesas(id_ubicacion, acta_desglosada=False):
    """
        Recibe un id_ubicación de un establecimiento y devuelve los datos
        en el formato del server.
        [id_planilla, estado, numero_mesa, sexo, codigo_ubicacion]
        @TODO: Ver actas desglosadas.
    """
    mesas = []
    for u in Ubicacion.many(clase='Mesa',
                            codigo__startswith=id_ubicacion + '.'):
        datos_mesa = [[u.id_planilla, "Espera", u.numero, None, u.codigo]]
        if acta_desglosada:
            current_data_code(u.cod_datos)
            for c in Categoria.all():
                datos_mesa.append([c.codigo, c.nombre, c.posicion])
        mesas.append(datos_mesa)
    return mesas


def generar_recuento(datos_tag):
    return Recuento.desde_tag(datos_tag)


def guardar_recuento(estados, id_ubicacion, cod_categoria, cod_datos):
    """
        Esta funcion devuelve un codigo según el estado de la mesa
            0: La mesa no es válida para la carga.
            1: La mesa no fue ingresada al servidor y se va a proceder a
               cargarla
            2: La mesa ya fue ingresada al servidor y se va a proceder a
               confirmarla
            3: La mesa ya fue ingresada y confirmada
    """
    if id_ubicacion not in estados:
        return 0
    elif id_ubicacion in estados and estados[id_ubicacion]['estado'] == 'OK':
        return 6

    if cod_categoria is None:
        if id_ubicacion in estados and estados[id_ubicacion]['estado'] \
                == 'Espera':
            return 1
        elif id_ubicacion in estados and estados[id_ubicacion]['estado'] \
                == 'En Proceso':
            return 2
    else:
        cargos = estados[id_ubicacion]['cargos'].keys()
        cargos_actas = [c for c in cargos
                        if estados[id_ubicacion]['cargos'][c]['estado'] == 1]
        cargos_actas += [cod_categoria]
        if all(cargo in cargos_actas for cargo in cargos):
            if id_ubicacion in estados and estados[id_ubicacion]['estado'] \
                    == 'Espera':
                return 4
            elif id_ubicacion in estados and estados[id_ubicacion]['estado'] \
                    == 'En Proceso':
                return 5
        else:
            return 3


def generar_imagen_recuento_definitivo(recuento):
    img = recuento.a_imagen()
    dst = '/tmp/%s_Mesa_%s.png' % (
        recuento.mesa.departamento.replace(' ', '_'), recuento.mesa.numero)
    img.save(dst)


def generar_acta_svg(recuento, definitiva=False, categorias=None,
                     acta_desglosada=False):
    """ Genera un acta en svg, en el caso de que no se utilize acta desglosada
        en caso contrario, devuelve una lista de tuplas con la siguiente
        estructura:
        [(cod_categoria, descripcion, idx, svg_recuento_categoria),
        ]
    """

    svg = []
    if acta_desglosada and categorias is not None:
        for categoria in categorias:
            svg_categ = recuento.a_imagen(svg=True, tipo=(CIERRE_TRANSMISION,
                                                          categoria[0]),
                                          de_muestra=not definitiva)
            svg.append(categoria + (svg_categ, ))
    else:
        svg.append((None, None, None,
                    recuento.a_imagen(svg=True, de_muestra=not definitiva)))
    return svg


def descargar_recuento(filename, destino):
    copy('/tmp/%s' % filename, destino)


def simular_delay_conexion(rtt_min=10, rtt_max=200):
    # Simulando un rtt variable entre 10 y 200ms
    rtt = float(randint(rtt_min, rtt_max)) / 1000
    sleep(rtt)


def get_categorias(cod_datos, desglosada):
    if desglosada:
        current_data_code(cod_datos)
        categorias = [(c.codigo, c.nombre, c.posicion) for c in
                      Categoria.many(sorted="posicion")]
    else:
        categorias = None

    return categorias


def generar_recuento_total(actas):
    actas = [Recuento.desde_tag(datos_tag) for datos_tag in actas]
    recuento = Recuento(actas[0].mesa)

    campos_especiales = ['boletas_contadas', 'listas_especiales',
                         'campos_extra']

    for campo in campos_especiales:
        if hasattr(actas[0], campo):
            setattr(recuento, campo, getattr(actas[0], campo))
    for acta in actas:
        for key, value in acta._resultados.items():
            recuento._resultados[key] += value

    return recuento
