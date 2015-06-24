#-*- coding: utf-8 -*-

import socket
import ssl
import httplib
import urllib2

key_file = None
cert_file = None
ca_file = None
_timeout = None


class HTTPSClientAuthConnection(httplib.HTTPSConnection):
    """ Class to make a HTTPS connection, with support for client-based SSL
        Authentication
    """

    def __init__(self, host, timeout=None):
        httplib.HTTPSConnection.__init__(self, host, key_file=key_file,
                                         cert_file=cert_file)
        self.timeout = _timeout
        self.ca_file = ca_file

    def connect(self):
        """ Connect to a host on a given (SSL) port.
            If ca_file is pointing somewhere, use it to check Server
            Certificate.

            Redefinido/copiado y extendido de
            /usr/lib/python2.6/httplib.py:1105
            Necesario para pasarle cert_reqs=ssl.CERT_REQUIRED y el cliente
            valide que el cert del servidor sea válido.
        """
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        # If there's no CA File, don't force Server Certificate Check
        if self.ca_file:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        ca_certs=self.ca_file,
                                        cert_reqs=ssl.CERT_REQUIRED)
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        cert_reqs=ssl.CERT_NONE)


class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSClientAuthConnection, req)
