# -*- coding:utf-8 -*-
import pickle
import urllib


from copy import copy
from os import listdir, path, remove
from re import compile
from sys import argv
from time import sleep
from multiprocessing import Pool, cpu_count
from random import shuffle, randint, random

from msa import get_logger
from msa.core.clases import Recuento
from msa.core.data import Ubicacion
from msa.core.data.candidaturas import Categoria
from msa.core.data.constants import NOMBRE_JSON_MESAS_DEFINITIVO
# no eliminar este import de ICODE2, el pickle lo necesita
from msa.desktop.transmision.core import TransmisionCore
from msa.desktop.transmision.config import Configuracion
from msa.desktop.transmision.settings import (
    UBIC_MODULO, PATH_TEMPLATE_TRANSMISION)
from msa.settings import PATH_CERTS as GLOBAL_PATH_CERTS, PATH_CODIGO
from msa.tools.generadores.voto.obtener_recuentos import obtener_tags
from msa.test import MSADBTest, get_test_connection


logger = get_logger("multi_test")

# Ajustes de timings. Esto varía depende la corrida, la conectividad, etc.
# Hay que ajustarlos de forma artesanal.
TIM_PRE_CONEXION = 1
TIM_POST_CONEXION = 5
TIM_POST_EV_TAG = 5
TIM_POST_CONFIRMACION = 4

PROCESOS = 10


# Modo solo carga
SOLO_CARGA = False


def esperar_evento():
    sleep(0.10)


def worker(data):
    # Agrego un sleep para que no todos los clientes se intenten loguear a la
    # vez y bloqueen el servidor
    sleep(random() * 4)
    id_ubicacion, pkey, cert, ca_cert, passwd, recuentos = data
    transmision = TransmisionCoreTest(id_ubicacion, pkey, cert, ca_cert,
                                      passwd, recuentos)


class TransmisionCoreTest(TransmisionCore):

    def __init__(self, id_ubicacion, pkey, cert, ca_cert, passwd, recuentos):
        TransmisionCore.__init__(self, hw_init=False)
        self._iniciar_configuracion(pkey, cert, ca_cert)
        self._iniciar_tags()
        self.conectar()
        sleep(TIM_POST_CONEXION + 2 * random())

        self._autenticar(id_ubicacion, passwd)
        self.transmitir(recuentos)
        self.desconectar()

    def _autenticar(self, user, passwd):
        datos_loggin = '%s,%s' % (user, passwd)
        logger.debug("Logueando usuario: %s", datos_loggin)
        ubic = path.join(PATH_CODIGO, UBIC_MODULO, "tests/save_transmision_id")
        file_ = open(ubic)
        data = pickle.load(file_)
        file_.close()
        data[1]['datos'] = datos_loggin

        self._evento_tag(*data)

    def _iniciar_configuracion(self, pkey, cert, ca_cert):
        self.config.HOST = 'transmision.local'
        self.config.KEY_FILE = path.join(GLOBAL_PATH_CERTS, pkey)
        self.config.CERT_FILE = path.join(GLOBAL_PATH_CERTS, cert)
        self.config.CA_FILE = path.join(GLOBAL_PATH_CERTS, ca_cert)

    def _iniciar_tags(self):
        ubic = path.join(PATH_CODIGO, UBIC_MODULO,
                         "tests/save_transmision_recuento")
        file_ = open(ubic, 'r')
        self.data_recuento = list(pickle.load(file_))
        file_.close()

    def transmitir(self, recuentos):
        logger.debug("Enviando recuento")
        for recuento in recuentos:
            self.data_recuento[1]['datos'] = recuento
            for i in range(2):
                self._evento_tag(*self.data_recuento)
                sleep(TIM_POST_EV_TAG + 2 * random())
            self.confirmar_recuento(recuento)
            sleep(TIM_POST_CONFIRMACION + 2 * random())

    def cb_actualizacion_mesas(self):
        pass

    def esperando_evento(self, activo, idle=False):
        pass

    def cb_actualizacion_informacion(self, text, idle=False, color=None,
                                     alerta=''):
        """
        """
        logger.debug('%s', text)

    def cb_actualizacion_estado(self, status):
        pass

    def cb_confirmacion(self, datos_tag):
        """
        Callback de confirmación de recuentos
        """
        pass

    def cb_mostrar_acta(self, lista_imagenes, usar_pestana=False):
        """
        Callback para mostrar la/s imagen/es de las actas
        Recibe un listado de actas con la siguiente estructura
        [(cod_categoria, descripcion, idx_categoria, imagen)]
        """
        pass

    def cb_actualizar_opciones(self, lista_botones):
        """
        Callback para interactuar con las acciones disponibles.
        """
        pass

    def cb_perdida_conexion(self):
        """
        Callback llamado unicamente cuando el echo_loop detecta que no hay
        conectividad con el servidor
        """
        print "Se ha perdido la conexión con el servidor"

    def cb_fin_prueba_estados(self, datos_prueba):
        """
        Callback llamado cuando se finaliza una prueba de la pantalla de estado
        """
        pass

    def cb_reiniciar_vista_confirmacion(self):
        """
        Callback llamado cuando se reinicia la vista de confirmación de acta
        """
        pass


class MultipleTransmisionTest(MSADBTest):
    def setUp(self):
        # MSADBTest.setUp(self)
        self.rango_escuelas = (None, None)
        self.rango_mesas = None
        self.escuela_actual = 0
        for arg in argv:
            if arg.startswith('rango'):
                rango = arg.split('=')[-1]
                rango = rango.split('-')
                rango_min = int(rango[0])
                self.escuela_actual = rango_min
                if len(rango) > 1:
                    try:
                        rango_max = int(rango[1])
                    except:
                        rango_max = None
                else:
                    rango_max = None
                self.rango_escuelas = (rango_min, rango_max)
            elif arg.startswith('mesas'):
                self.rango_mesas = int(arg.split('=')[-1])

        self.config_original = copy(Configuracion.DEFAULT_CONFIG['glade_file'])
        Configuracion.DEFAULT_CONFIG['glade_file'] = \
            path.join(PATH_CODIGO, UBIC_MODULO,
                      Configuracion.DEFAULT_CONFIG['glade_file'])
        Configuracion.DEFAULT_CONFIG['host'] = "transmision.local"

    def tearDown(self):
        # MSADBTest.tearDown(self)
        Configuracion.DEFAULT_CONFIG['glade_file'] = self.config_original
        self.app = None

        output = path.join(PATH_CODIGO, UBIC_MODULO, "tests/recuentos.txt")
        try:
            remove(output)
        except OSError:
            pass

    def _get_certs(self):
        regex = compile('(\w{2}[\.\d]+).+\.(\w{3,4})')

        dict_files = {'CA': {'cert': 'CA_Elecciones_Ejemplo.2015.cert'}}

        for filename in listdir(GLOBAL_PATH_CERTS):
            match = regex.match(filename)

            if match is not None:
                groups = match.groups()
                ubicacion = groups[0]
                tipo = groups[1]

                if ubicacion not in dict_files:
                    dict_files[ubicacion] = {}

                dict_files[ubicacion][tipo] = filename

        return dict_files

    def _get_escuelas(self):
        conn = get_test_connection()
        cur = conn.cursor()
        q_get_escuelas = """SELECT id_ubicacion
                            FROM ubicaciones
                            WHERE clase = 'Establecimiento'"""
        cur.execute(q_get_escuelas)
        escuelas = cur.fetchall()
        cur.close()

        return [e[0] for e in escuelas]

    def _get_nro_mesas(self, id_ubicacion):
        conn = get_test_connection()
        cur = conn.cursor()
        q_get_mesas = """SELECT descripcion
                         FROM ubicaciones
                         WHERE clase = 'Mesa'
                         AND id_ubicacion <@ %s"""
        cur.execute(q_get_mesas, (id_ubicacion, ))
        mesas = cur.fetchall()
        cur.close()

        return [m[0] for m in mesas]

    def _get_usr_claves(self):
        path_archivo_claves = '/opt/eleccion_recursos/datos/' \
                              'ejemplo2015/claves_tx_produccion.csv'
        dict_users = {}

        with open(path_archivo_claves, 'r') as csv_file:
            csv_data = csv_file.read()[:-1].split('\n')

        for data in csv_data:
            user, passwd = data.split('|')
            dict_users[user] = passwd[:5]

        return dict_users

    def _get_recuentos(self, mesas):
        return [r[1] for r in obtener_tags(mesas)]

    def test_todos(self):
        r_min, r_max = self.rango_escuelas
        lista_escuelas = self._get_escuelas()[r_min:r_max]
        dict_certs = self._get_certs()
        dict_users = self._get_usr_claves()
        Ubicacion.plural_name = NOMBRE_JSON_MESAS_DEFINITIVO

        j = []
        for id_ubicacion in lista_escuelas[:]:
            j.append(self._get_data_tests(id_ubicacion, dict_certs,
                     dict_users))

        pool = Pool(PROCESOS)

        pool.map(worker, j)

    def _get_data_tests(self, id_ubicacion, dict_certs, dict_users):
        pkey = dict_certs[id_ubicacion]['pkey']
        cert = dict_certs[id_ubicacion]['cert']
        ca_cert = dict_certs['CA']['cert']

        mesas = self._get_nro_mesas(id_ubicacion)[:self.rango_mesas]

        recuentos = self._get_recuentos(mesas)

        return (id_ubicacion, pkey, cert, ca_cert, dict_users[id_ubicacion],
                recuentos)

    def iguales(self, expected, result):
        def _cmp(obj_a, obj_b):
            return cmp(obj_a[1], obj_b[1])

        self.assertEqual(len(expected.keys()), len(result.keys()))
        for key in expected.keys():
            dest_key = list(key)
            self.assertEquals(expected[tuple(key)],
                              result[tuple(dest_key)])

    def get_db_for_mesa(self, mesa):
        conn = get_test_connection()
        cur = conn.cursor()
        sql = """SELECT id_cargo,
                        id_candidatura,
                        votos_definitivos
                    FROM planillas_det
                    WHERE id_planilla = %s
        """
        cur.execute(sql, (mesa.id_planilla, ))
        data = cur.fetchall()
        result_dict = {}
        for datum in data:
            key = str(datum[1] if datum[1] != "BLC.BLC.BLC.BLC" else "%s_BLC"
                      % datum[0])
            key = key.rjust(3, "0")
            result_dict[(unicode(datum[0]), unicode(key))] = datum[2]

        return result_dict
