# coding:utf-8
""" Esta librería establece una conexión SSL contra un servidor
    y permite enviar y recibir bytes por la misma.
"""

import json
import urllib
import cookielib
import https_auth_handler
import time
import socket
import dns.rdataclass
import dns.resolver

from base64 import b64encode
from urllib2 import HTTPHandler, HTTPCookieProcessor, Request, HTTPError, \
    URLError, build_opener
from https_auth_handler import HTTPSClientAuthHandler
from ssl import SSLError

from msa import get_logger


logger = get_logger("trasmision-conexion")


class Respuesta(object):
    """ Esta clase es un wrapper para convertir la respuesta del servidor (un
        string) a un diccionario de claves y valores.
        Por ejemplo, si el server devuelve: 'OK',clave1=valor1&clave2=valor2,
        esta clase lo interpreta y brinda una funcion server_ok() y la
        respuesta en sí se la puede acceder usando una instancia de esta clase
        como diccionario (ej.: resp['mensaje'])
    """
    def __init__(self, respuesta_servidor):
        try:
            self._dict = json.loads(respuesta_servidor)
        except Exception as e:
            self.__codigo = 'ER'
            self.__mensaje = "En este momento el sistema se encuentra " + \
                             "ocupado debido a la gran cantidad de " + \
                             "usuarios en línea.\nPor favor, aguarde " + \
                             "o reintente en unos instantes."
            self._dict = {'status': self.__codigo, 'mensaje': self.__mensaje}
            logger.debug('Error al interpretar respuesta del servidor: %s' %
                         str(e))
        else:
            if 'status' in self._dict:
                self.__codigo = self._dict['status']
            if 'mensaje' in self._dict:
                self.__mensaje = self._dict['mensaje']

    def status_ok(self):
        return self.__codigo == 'OK'

    def __getitem__(self, clave):
        """ Método para obtener valores de la respuesta del servidor, dada una
        clave """
        if clave in self._dict:
            return self._dict[clave]
        else:
            return None

    def __setitem__(self, clave, valor):
        """ Método para guardar valores en el diccionario de respuesta. No
        debería usarse, pero lo implemento por compatibilidad con los
        diccionarios.
        """
        self._dict[clave] = valor

    def __contains__(self, clave):
        """ Método para devolver si una clave está en el diccionario de
        respuesta """
        return clave in self._dict

    def __str__(self):
        return '%s,%s' % (self.__codigo, self.__mensaje)


class DNSResolver(object):
    """
    La respuesta del DNS debe contener la siguiente estructura:
    Registros A:    Direcciones IPv4 de todos los servidores de transmisión
    Registros AAAA: Direcciones IPv6 de todos los servidores de transmisión,
    cuando eventualmente se implementen.
    Registro TXT:   Este registro se lo va a utilizar para almacenar
    configuración adicional en el formato key, value pero existe una limitación
    del protocolo con respecto al máximo de datos que puede almacenar un string
    el largo inferior a 255 caracteres. Como salvedad de esto permite un
    número ilimitado de strings con la restricción de que el tamaño total del
    paquete debe ser inferior a 64k.
    Por este motivo se define una estructura para los strings
        key,numero_parte:value
    siendo el máximo de numeros de parte de 9 y el largo máximo permitido
    del value:
        255 - len(key) - 3 (número, coma y dos puntos)
    Por lo que por cada key se permite almacenar:
        size = (255 - (len(key) + 1)) * 9
    Por ejemplo para una key de tamaño 5 se pueden almacenar 2232 Bytes con un
    overhead de 63 Bytes.
    Por ejemplo, un string de largo inferior a 255 estaría estructurado como:
        prueba,0:Esta es una cadena de pruebas.
    un string con largo superior a 255 estaría estructurado como:
        prueba,0:Imaginese que es una cadena de largo superior a 255 caract.
        prueba,1:Continua la cadena anterior.
    """

    def __init__(self, queries):
        self._queries = queries
        self.ip_primaria = None
        self.ip_secundarias = []
        self.txt_register = None

    def resolv(self, name_server):
        # Codigo sacado de http://stackoverflow.com/questions/13842116/how-do-we-get-txt-cname-and-soa-records-from-dnspython
        ADDITIONAL_RDCLASS = 65535

        for hostname in self._queries:
            request = dns.message.make_query(hostname, dns.rdatatype.ANY)
            request.flags |= dns.flags.AD
            request.find_rrset(request.additional, dns.name.root,
                               ADDITIONAL_RDCLASS, dns.rdatatype.OPT,
                               create=True, force_unique=True)
            response = dns.query.udp(request, name_server)

        txt_list = []
        a_list = []
        for register_obj in response.answer:
            type = register_obj.rdtype
            # A record
            if type == 1:
                for a in register_obj:
                    a_list.append(a.address)
            # TXT record
            elif type == 16:
                for txt in register_obj:
                    txt_list += txt.strings
            # AAAA record
            elif type == 28:
                pass

        self.txt_register = self._parse_txt_register(txt_list)

        # Si se adjunta el campo primario en el registro txt se lo almacena
        if 'primario' in self.txt_register:
            self.ip_primaria = self.txt_register['primario']
        # Elimino la ip del primario de las ips secundarias
        if self.ip_primaria in a_list:
            a_list.pop(a_list.index(self.ip_primaria))
        self.ip_secundarias = a_list

    # Dejo este método acá a modo de demostración del funcionamiento del reg
    def make_txt_register(**datos):
        txt_register = []
        for key, value in datos.iteritems():
            max_size = 255 - len(key) - 1
            value_list = [value[i * max_size:(i + 1) * max_size] for i in
                          range((len(value) / max_size) + 1)]

            for part, v in enumerate(value_list):
                _msg_part = '{},{}:{}'.format(key, part, v)
                txt_register.append(_msg_part)
        return txt_register

    def _parse_txt_register(self, txt):
        txt_register = {}
        for string in txt:
            head, value = string.split(':')
            key, part = head.split(',')
            if key not in txt_register:
                txt_register[key] = {}
            txt_register[key][part] = value
        for key in txt_register:
            register = ''
            temp_dict = txt_register[key]
            for part in sorted(temp_dict):
                register += temp_dict[part]
            txt_register[key] = register
        return txt_register


class Conexion(object):

    UNKNOW_ERROR = 1
    SSL_ERROR = 2
    CONNECTION_ERROR = 3

    """ Esta Clase brinda un nivel de abstracción para el manejo del tráfico de
    red contra el servidor """
    def __init__(self, url, debug=True, timeout=None):
        # TODO: Validar/Sanear la url, al menos que cumpla con una regex o algo
        # http://aaa.com.ar/cosa.py/
        self.DEBUG = debug
        if debug:
            self.DEBUG_LEVEL = 1
        else:
            self.DEBUG_LEVEL = 0
        self.url = url
        self._cookiejar = cookielib.CookieJar()
        self.timeout = timeout
        self._tmp_error = ""

    def set_https_keys(self, key_file, cert_file):
        """ Configura las claves https """
        https_auth_handler.key_file = key_file
        https_auth_handler.cert_file = cert_file

    def set_ca_certificate(self, ca_file):
        """ Establece el certificado del CA para validar la conexión HTTPS
        desde el lado del cliente """
        https_auth_handler.ca_file = ca_file

    def __get_https_opener(self):
        """ Devuelve una instancia del opener adecuado para interactuar vía
        https con client key y soporte de cookies """
        if self.timeout:
            https_auth_handler._timeout = float(self.timeout)
        return build_opener(HTTPHandler(debuglevel=self.DEBUG_LEVEL),
                            HTTPSClientAuthHandler(
                                debuglevel=self.DEBUG_LEVEL),
                            HTTPCookieProcessor(self._cookiejar))

    def __get_http_opener(self):
        """ Devuelve una instancia del opener adecuado para interactuar vía
        https con client key y soporte de cookies """
        return build_opener(HTTPHandler(debuglevel=self.DEBUG_LEVEL),
                            HTTPCookieProcessor(self._cookiejar))

    def _enviar(self, funcion, **datos):
        """ Llama a la función del servidor pasada por parámetro,
            con los parámetros de la tupla de datos, siempre sobre la url del
            constructor de Conexion.
        """
        parametros = urllib.urlencode(datos)
        opener = self.__get_https_opener()
        req = Request(self.url + funcion, parametros)
        try:
            url = opener.open(req)
        except HTTPError, e:
            # Error en el servidor, construyo una respuesta desde acá
            respuesta = Respuesta(json.dumps(
                {'status': 'ER',
                 'mensaje': 'El sistema se encuentra ocupado en este ' +
                            'momento. Espere unos minutos y reintente ' +
                            'más tarde.'}))
            logger.error(str(e))
        else:
            respuesta = url.read()
        return respuesta

    def enviar_recuento(self, datos_tag):
        """ Envía un recuento al servidor """
        # El recuento lo envío en base64 porque urllib2 no soporta nativamente
        # envíos POST con el tipo MIME multipart/form-data (que sería lo lógico
        # para mandar un byte stream como este, o como un file upload).
        # Ver: http://bytes.com/groups/python/33833-file-upload-using-httplib
        #      http://code.activestate.com/recipes/146306/
        #      http://stackoverflow.com/questions/680305/
        #            using-multipartposthandler-to-post-form-data-with-python
        # (los tipos MIME de envío y devolución de datos se establecen con el
        # encabezado 'Content-Type: xxxx' de HTTP).

        # Si quiero pasar directamente los bytes de datos_tag con el tipo MIME
        # 'application/x-www-form-urlencoded' (el único método de urllib2,
        # además por defecto para los POST y GET, y utilizado en todas las
        # funciones de esta clase), mod_python parece "tirarlos" y los bytes#
        # '\x00\x01...' no llegan del otro lado.
        #
        # Ojo, mod_python en el server sí soporta 'multipart/form-data' para
        # recepción de archivos, pero no parece soportar caracteres no
        # imprimibles con 'application/x-www-form-urlencoded'.
        #
        # Por todo esto uso base64, donde me aseguro utilizar siempre
        # caracteres imprimibles dado el content-type que utilizo
        # ('application/x-www-form-urlencoded').
        # Aunque si bien base64 ocupa más bytes de envío que con el método
        # 'oficial' de subida de archivos, el tamaño máximo de los tags que
        # manejamos es irrisorio, con lo cual sirve lo mismo.
        logger.debug("CARGANDO RECUENTO")
        respuesta = self._enviar('cargar_recuento',
                                 datos_tag=b64encode(datos_tag))
        return Respuesta(respuesta)

    def autenticar(self, usuario, clave):
        """ Autentica este cliente contra el servidor.
            El parámetro datos es el string de autenticación.
        """
        respuesta = self._enviar('login', usuario=usuario, clave=clave)
        return Respuesta(respuesta)

    def test_conexion(self):
        """ Conecta con el servidor, intercambia algo de tráfico de prueba y
        devuelve True en caso de éxito o False en caso contrario.
        """
        try:
            respuesta_servidor = self._enviar('echo')
            logger.debug("respuesta_servidor %s", respuesta_servidor)
        except URLError, e:
            self._tmp_error = time.time(), e
            logger.debug('Funcion: test_conexion, URLError: %s' % e)
            # return False
            respuesta_servidor = json.dumps({'status': 'ER'})

        r = Respuesta(respuesta_servidor)
        return r

    def diagnosticar(self):
        """ Conecta con el servidor, intercambia algo de tráfico de prueba y
            devuelve un diagnostico si fue fallida la prueba.
        """
        try:
            error = self.UNKNOW_ERROR
            # Me fijo que el error tiene una *antiguedad* de 1 seg.
            # No es la solución óptima, pero para esta caso es la más sencilla.
            if self._tmp_error[0] > time.time() - 1:
                e = self._tmp_error[1]
                if hasattr(e, 'reason'):
                    tipo_error = type(e.reason)
                    if tipo_error is socket.gaierror:
                        error = self.CONNECTION_ERROR
                    elif tipo_error is SSLError:
                        error = self.SSL_ERROR
                return error
        except Exception, e:
            logger.debug('Funcion: diagnosticar, Error: %s' % e)
        return None

    def descargar(self, url_address, destino):
        """ Descarga un recurso del servidor y lo almacena en el destino local
        """
        file_out = open(destino, 'wb')
        opener = self.__get_https_opener()
        try:
            url = opener.open(url_address)
        except HTTPError, e:
            # Error en el servidor, construyo una respuesta desde acá
            respuesta = Respuesta(
                json.dumps({
                    'status': 'ER',
                    'mensaje':
                    'El sistema se encuentra ocupado en este momento.' +
                    'Espere unos minutos y reintente más tarde.'}))
            logger.error(str(e))
        else:
            file_out.write(url.read())

    def obtener_datos_servidor(self, db_version):
        """ Descarga un recurso del servidor y lo almacena en el destino local
        """
        respuesta = self._enviar('datos', db_version=db_version)
        return Respuesta(respuesta)

    def confirmar_acta(self, datos_tag):
        """ Llama a la función del servidor para confirmar el acta """
        respuesta = self._enviar('confirmar_acta',
                                 datos_tag=b64encode(datos_tag))
        return Respuesta(respuesta)

    def enviar_diagnostico(self, diagnostico):
        respuesta = self._enviar('diagnostico',
                                 diagnostico=diagnostico)
        return Respuesta(respuesta)
