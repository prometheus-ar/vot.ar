# -*- coding:utf-8 -*-
import pickle
import urllib
import thread

from copy import copy
from os import path, remove
from time import sleep


from msa import get_logger
from msa.core import get_config
from msa.core.clases import Recuento
from msa.core.data import Ubicacion
from msa.core.data.candidaturas import Categoria
from msa.core.data.constants import NOMBRE_JSON_MESAS_DEFINITIVO
# no eliminar este import de ICODE2, el pickle lo necesita
from msa.desktop.transmision.transmision_web import TransmisionApp, Ventana
from msa.desktop.transmision.config import Configuracion
from msa.desktop.transmision.settings import (
    UBIC_MODULO, PATH_TEMPLATE_TRANSMISION)
from msa.settings import PATH_CERTS as GLOBAL_PATH_CERTS, PATH_CODIGO
from msa.tools.generadores.voto.genera_pickes_recuentos import generar
from msa.test import MSADBTest, get_test_connection


logger = get_logger("multi_test")


def esperar_evento():
    sleep(0.10)


class MockLector():
    def __init__(self, *args, **kwargs):
        pass

    def conectar(self, *args, **kwargs):
        return True

    def conectar_lector(self, *args, **kwargs):
        return True

    def add_to_loop(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def desconectar_lector(self, *args, **kwargs):
        pass


class MultipleTransmisionTest(MSADBTest):
    def setUp(self):
        # MSADBTest.setUp(self)

        self.config_original = copy(Configuracion.DEFAULT_CONFIG['glade_file'])
        Configuracion.DEFAULT_CONFIG['glade_file'] = \
            path.join(PATH_CODIGO, UBIC_MODULO,
                      Configuracion.DEFAULT_CONFIG['glade_file'])
        Configuracion.DEFAULT_CONFIG['host'] = "transmision.local"

    def arrancar(self, pkey, cert, ca_cert):
        Configuracion.DEFAULT_CONFIG['key_file'] = \
            path.join(GLOBAL_PATH_CERTS, pkey)
        Configuracion.DEFAULT_CONFIG['cert_file'] = \
            path.join(GLOBAL_PATH_CERTS, cert)
        Configuracion.DEFAULT_CONFIG['ca_file'] = path.join(GLOBAL_PATH_CERTS,
                                                            ca_cert)

        thread.start_new_thread(self.iniciar_app, ())
        sleep(1)

    def iniciar_app(self):
        configs = [
            ['enable-universal-access-from-file-uris', True]
        ]
        uri = 'file://' + urllib.pathname2url(PATH_TEMPLATE_TRANSMISION)
        controller = TransmisionApp()
        controller.add_processor("transmision")
        controller.multi_test = True
        self.app = Ventana(uri, controller)
        configs = [
            ['enable-universal-access-from-file-uris', True]
        ]
        self.app.run(configs, on_close=controller.web_salir, debug=False)

    def crear_recuentos(self, numeros):
        output = path.join(PATH_CODIGO, UBIC_MODULO, "tests/recuentos.txt")
        generar(output, numeros)

    def tearDown(self):
        # MSADBTest.tearDown(self)
        Configuracion.DEFAULT_CONFIG['glade_file'] = self.config_original
        self.app = None

        output = path.join(PATH_CODIGO, UBIC_MODULO, "tests/recuentos.txt")
        try:
            #remove(output)
            pass
        except OSError:
            pass

    def _test_usuario_una_mesa(self):
        pkey = "EJ.01.01.01-ESCUELA_PRIMARIA_N_23.pkey"
        cert = "EJ.01.01.01-ESCUELA_PRIMARIA_N_23.cert"
        ca_cert = "CA_Elecciones_Ejemplo.2015.cert"
        self.crear_recuentos([1])
        self.arrancar(pkey, cert, ca_cert)
        self._test_multi()

    def _test_usuario(self):
        pkey = "EJ.01.01.01-ESCUELA_PRIMARIA_N_23.pkey"
        cert = "EJ.01.01.01-ESCUELA_PRIMARIA_N_23.cert"
        ca_cert = "CA_Elecciones_Ejemplo.2015.cert"
        self.crear_recuentos(range(1, 9))
        self.arrancar(pkey, cert, ca_cert)
        self._test_multi()

    def test_todos(self):
        conn = get_test_connection()
        cur = conn.cursor()
        sql = """
            UPDATE puntos_de_carga
            SET promiscuo = 'SI',
                certificado = 'MSAWC01'
            WHERE id_punto_de_carga = 'CABA'
        """
        cur.execute(sql)
        conn.commit()
        cur.close()

        pkey = "MSAWC01-Wildcard_1.pkey"
        cert = "MSAWC01-Wildcard_1.cert"
        ca_cert = "CA_Elecciones_CABA_05.07.2015.cert"
        self.crear_recuentos(range(1000, 1010))
        self.arrancar(pkey, cert, ca_cert)
        self._test_multi()

    def _test_multi(self):
        Ubicacion.plural_name = NOMBRE_JSON_MESAS_DEFINITIVO
        logger.debug("Conectando")
        self.app.controller.conectar()
        logger.debug("Conectado")

        # while self.app.controller.valid_tags is None:
        #     logger.debug("esperando evento")
        #     esperar_evento()
        sleep(5)

        logger.debug("<" * 5 + "CONECTANDO" + ">" * 5)

        ubic = path.join(PATH_CODIGO, UBIC_MODULO, "tests/save_transmision_id")
        file_ = open(ubic)
        data = pickle.load(file_)

        self.app.controller._evento_tag(*data)
        file_.close()
        esperar_evento()
        ubic = path.join(PATH_CODIGO, UBIC_MODULO,
                         "tests/save_transmision_recuento")
        file_ = open(ubic)
        data_recuento = list(pickle.load(file_))
        file_.close()

        file_ = open(path.join(PATH_CODIGO, UBIC_MODULO,
                               "tests/recuentos.txt"))
        recuentos = list(pickle.load(file_))
        file_.close()
        print len(recuentos), "RECUENTOS"
        sleep(4)
        for i, recuento in enumerate(recuentos, 1):
            logger.info("\n<<<<<" + "ENVIANDO RECUENTO %s>>>>>", i)
            data_recuento[1]["datos"] = recuento
            for j in range(2):
                self.app.controller._evento_tag(*data_recuento)
                sleep(1)

            sleep(1.5)
            self.app.controller.send_command("click_si")
            sleep(3)
            obj_recuento = Recuento.desde_tag(recuento)
            en_db = self.get_db_for_mesa(obj_recuento.mesa)
            for categoria in Categoria.all():
                obj_recuento._resultados[(categoria.codigo, "BLC.BLC")] = \
                    obj_recuento._resultados[(categoria.codigo, "%s_BLC" %
                                              categoria.codigo)]
                del obj_recuento._resultados[(categoria.codigo, "%s_BLC" %
                                              categoria.codigo)]

                obj_recuento._resultados[(categoria.codigo, "NUL.NUL")] = \
                    obj_recuento.listas_especiales["NUL"]
                obj_recuento._resultados[(categoria.codigo, "REC.REC")] = \
                    obj_recuento.listas_especiales["REC"]
                obj_recuento._resultados[(categoria.codigo, "IMP.IMP")] = \
                    obj_recuento.listas_especiales["IMP"]
                obj_recuento._resultados[(categoria.codigo, "TEC.TEC")] = \
                    obj_recuento.listas_especiales["TEC"]
            self.iguales(obj_recuento._resultados, en_db)
        try:
            self.app.controller._salir_definitivo()
        except RuntimeError:
            pass

    def iguales(self, expected, result):
        def _cmp(obj_a, obj_b):
            return cmp(obj_a[1], obj_b[1])
        # from pprint import pprint
        # pprint(sorted(expected.keys(), cmp=_cmp))
        # pprint(sorted(result.keys(), cmp=_cmp))

        self.assertEqual(len(expected.keys()), len(result.keys()))
        for key in expected.keys():
            dest_key = list(key)
            self.assertEquals(expected[tuple(key)],
                              result[tuple(dest_key)])

    def get_db_for_mesa(self, mesa):
        try:
            conn = get_test_connection()
            cur = conn.cursor()
            sql = """SELECT id_cargo,
                            id_candidatura,
                            votos_definitivos
                     FROM planillas_det
                     WHERE id_planilla = %s
                           AND id_candidatura NOT IN %s
            """
            cur.execute(sql, (mesa.id_planilla,
                              tuple(get_config("listas_especiales"))))
            data = cur.fetchall()
            result_dict = {}
            for datum in data:
                key = str(datum[1] if datum[1] != -1 else "%s_BLC" % datum[0])
                key = key.rjust(3, "0")
                result_dict[(unicode(datum[0]), unicode(key))] = datum[2]
        except Exception, e:
            logger.debug(e)
        return result_dict
