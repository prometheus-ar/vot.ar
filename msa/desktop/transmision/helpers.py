# -*- coding:utf-8 -*-
import os
import tarfile
import urllib2

from base64 import b64decode
from hashlib import sha256
from tarfile import open as opentar

from msa.desktop.transmision.settings import DEBUG


def bloqueante(method):
    """ Decorador para funciones mutex que activan bloqueo (lock) -hilos
        padre-
    """
    def locking_method(self, *args, **kwargs):
        if self.lock and not self.lock.acquire(0):
            if DEBUG:
                print(("%s: no puedo adquirir lock (thread pendiente!)" %
                      method.__name__))
            return
        try:
            return method(self, *args, **kwargs)
        except Exception, e:
            if self.lock:
                if DEBUG:
                    print("%s: libero lock por excepción!" % method.__name__)
                try:
                    self.lock.release()
                except:
                    pass
                raise e
    return locking_method


def desbloqueante(method):
    """ Decorardor para funciones mutex que desactivan bloqueo (lock)-hilos
        hijos-
    """
    def unlocking_method(self, *args, **kwargs):
        if DEBUG and self.lock:
            print("%s: inicio thread!, estado locked: %s" %
                  (method.func_name, self.lock.locked()))
        try:
            return method(self, *args, **kwargs)
        finally:
            # liberar lock
            if self.lock:
                if DEBUG:
                    print ("%s: libero lock por fin thread" %
                           method.func_name)
                try:
                    self.lock.release()
                except:
                    pass
    return unlocking_method


def download(url_base, file_name, user, pwd):
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url_base, user, pwd)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    opener = urllib2.build_opener(handler)

    urllib2.install_opener(opener)
    req = urllib2.Request(url_base + file_name)
    response = urllib2.urlopen(req)
    file_content = response.read()
    name_parts = file_name.split("/")
    real_name = name_parts[-1]
    path_destino = os.path.join(get_desktop_path(), real_name)
    file_ = open(path_destino, "w")
    file_.write(file_content)
    file_.close()
    return path_destino


def importar_claves(tar_filename, config):
    tar = tarfile.open(tar_filename, mode='r:*')
    # Hago una verificación basica para validar que los archivos existen y
    # los nombres estas dentro de un patron

    checksum_filename = 'files_checksum'

    files_pedidos = {'CA': ('CA/CA_', '.cert', 'ca_file'),
                     'certs': ('certs/', '.cert', 'cert_file'),
                     'keys': ('keys/', '.pkey', 'key_file')}

    archivos_validados = []
    for tarinfo in tar:
        if tarinfo.isreg():
            key, fname = os.path.split(tarinfo.name)
            value = files_pedidos.get(key, None)
            if value:
                fstart, fend, config_key = value
                name = tarinfo.name
                if name.startswith(fstart) and name.endswith(fend):
                    files_pedidos.pop(key)
                    archivos_validados.append((config_key, name))

    # Como por cada archivo que encuentro borro el patron del diccionario,
    # pregunto si faltan archivos mirando si el diccionario esta vacio
    faltan_archivos = bool(files_pedidos)
    if not faltan_archivos:
        tar.extractall()
        with open(checksum_filename, 'r') as checksum_file:
            checksum = checksum_file.read()
            checksum = checksum.split('\n')[:-1]
            files_checksum = {}
            for line in checksum:
                file, checksum = line.split(' ')
                files_checksum[file] = checksum
            checksum_file.close()

        archivos_danados = False
        for config_key, name in archivos_validados:
            with open(name) as file:
                data = file.read()
                local_checksum = sha256(data).hexdigest()
                if local_checksum != files_checksum[name]:
                    archivos_danados = True
                    break

        if not archivos_danados:
            for config_key, name in archivos_validados:
                config.set_option(config_key, name)
            config.write_options()
    tar.close()
    return faltan_archivos, archivos_danados


def get_desktop_path():
    """ Devuelve el path del Escritorio del usuario.
        En Linux intenta con 'Escritorio', sino con 'Desktop' y sino, devuelve
        el Home.
    """
    # TODO: Modificar esto si hay que soportar Windows
    #if os.name == 'nt':
    #    from winshell import winshell
    #    export_path = os.path.join(winshell.desktop(), dir_name)

    #
    export_path = os.path.join(os.path.expanduser('~'), 'Escritorio')
    if not os.path.exists(export_path):
        export_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        if not os.path.exists(export_path):
            export_path = os.path.expanduser('~')
    return export_path


def actualizar_datos(ubicacion, archivo, destino, destino_temp):
    nombre_archivo = os.path.join(destino_temp, '{}.tar.gz'.format(ubicacion))

    with open(nombre_archivo, 'wb') as file_out:
        file_out.write(b64decode(archivo))

    if not os.path.exists(destino):
        os.makedirs(destino)

    with opentar(nombre_archivo) as tar_file:
        tar_file.extractall(path=destino)


def mostrar_espera(method):
    """
        Decorador para funciones donde se debe mostrar una actividad al
        usuario, o cursor de espera, etc.
    """
    def run_method(self, *args, **kwargs):
        self.esperando_evento(True)
        try:
            return method(self, *args, **kwargs)
        except Exception:
            if DEBUG:
                print("%s: Excepción en metodo:" % method.__name__)
        finally:
            self.esperando_evento(False)
    return run_method


def estados_mesas_dict(estados_mesa):
    """
    Función que traduce los datos enviados por el servidor y que se recupera
    de la db
    """
    estados = {}
    desglosada = False
    for mesa in estados_mesa:
        cargos = {}
        datos = mesa[0]
        if datos[1] in ('Espera', 'En Proceso'):
            for cargo in mesa[1:]:
                cargos[cargo[0]] = {'descripcion': cargo[1],
                                    'nro_orden': cargo[2],
                                    'estado': 0}
        if not desglosada and len(cargos) > 0:
            desglosada = True

        estados[datos[4]] = {'id_planilla': datos[0],
                             'estado': datos[1],
                             'numero': datos[2],
                             'sexo': datos[3],
                             'cargos': cargos}

    return desglosada, estados


def status_for_url(url):
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = response.read()
        estado = "OK"
    except urllib2.HTTPError:
        estado = "HTTPError"
    except urllib2.URLError as e:
        estado = "URLError"
        print e
        #print response

    return estado

