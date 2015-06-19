# -*- coding: utf-8 -*-
""" Modulo para el manejo de la conexión a la DB via psycopg2
"""

import psycopg2
from psycopg2.extras import NamedTupleCursor

from msa.core.clases import Jerarquia
from msa.core.data.settings import JUEGO_DE_DATOS
from msa.core.settings import DEFAULT_DB_NAME, CLUSTERS, DB_USER, DB_PWD, \
    DEFAULT_CLUSTER


def _get_ltree_oid(cursor):
    """
    Devuelve el OID del tipo ltree correspondiente a la DB
    """
    sql = """SELECT pg_type.oid
                FROM pg_type JOIN pg_namespace
                ON typnamespace = pg_namespace.oid
                WHERE typname = 'ltree'"""
    cursor.execute(sql)

    return cursor.fetchone()[0]


def _cast_ltree(value, cur):
    """
    Castea un valor ltree traido de la DB a una instancia de la clase Jerarquia
    Nota: el segundo parámetro psycopg2 lo pasa siempre, dejar como está.
    """
    if value is None:
        return None

    return Jerarquia(value)


def get_connection(host=None, port=None, db=None,
                   user=DB_USER, pwd=DB_PWD, use_namedtuples=False):
    """
    Devuelve una conexión a la DB usando psycopg2. Si se pasa
    use_namedtuples en True, los cursores que se abran usando esta
    conexión devolverán NamedTuples en lugar de tuplas comunes.
    Además la conexión que se devuelve incluye el casteo del tipo ltree a
    instancias de la clase Jerarquía
    """

    cluster_data = _get_cluster_data(DEFAULT_CLUSTER)
    if host is None:
        host = cluster_data['host']
    if port is None:
        port = cluster_data['port']
    if db is None:
        db = cluster_data['db_name']

    if use_namedtuples:
        connection = psycopg2.connect(database=db, host=host, port=port,
                                      user=user, password=pwd,
                                      cursor_factory=NamedTupleCursor)
    else:
        connection = psycopg2.connect(database=db, host=host, port=port,
                                      user=user, password=pwd)

    cur = connection.cursor()
    # Seteamos el search_path al juego de datos seteado
    cur.execute("SET search_path TO %s, public" % JUEGO_DE_DATOS)

    # Registramos un tipo de datos custom
    oid = _get_ltree_oid(cur)
    ltree = psycopg2.extensions.new_type((oid,), "ltree", _cast_ltree)
    psycopg2.extensions.register_type(ltree)

    cur.close()

    return connection


def _get_cluster_data(name):
    cluster_data = None
    if name in CLUSTERS:
        cluster_data = CLUSTERS[name]
        if "db_name" not in cluster_data:
            cluster_data['db_name'] = DEFAULT_DB_NAME

    return cluster_data


def get_cluster_conn(name, user, password, use_namedtuples=False):
    data = _get_cluster_data(name)
    return get_connection(host=data['host'], port=data['port'],
                          db=data["db_name"], user=user, pwd=password,
                          use_namedtuples=use_namedtuples)
