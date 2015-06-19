# coding: utf-8
import pkg_resources

pkg_resources.declare_namespace(__name__)

import os
import sys
import colorama

from logging import getLogger, StreamHandler, Formatter, DEBUG
from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT, \
    RotatingFileHandler
from types import MethodType

from msa.settings import DEFAULT_LOG_LEVEL, LOGGING_SERVER_HOST, \
    FILELOG_SIZE, FILELOG_ROTATION, LOG_TO_FILE, LOG_NAME, LOG_TO_DB, \
    LOG_TO_STDOUT, LOG_TO_SENTRY, LOG_SENTRY_PATH, LOG_CAPTURE_STDOUT

loggers = {}


def debug_armve(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'DEBUG'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.debug_armve("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    try:
        if self.isEnabledFor(DEBUG):
            stream = args[0].split(" ")
            data = colorama.Fore.WHITE + stream[0] + " "
            data += colorama.Fore.YELLOW + " ".join(stream[1:4]) + " "
            data += colorama.Fore.GREEN + stream[4] + " "
            data += colorama.Fore.BLUE + " ".join(stream[5:7]) + " "
            resto = stream[7:]
            nuevo_resto = []
            prox_cambio = 0
            for i, elem in enumerate(resto):
                if elem == "e0" and resto[i+1] == "04":
                    color = colorama.Fore.RED
                    prox_cambio = i + 8
                elif prox_cambio == i:
                    color = colorama.Fore.MAGENTA
                nuevo_resto.append(color+elem)

            data += " ".join(nuevo_resto)

            self._log(DEBUG, msg, (data, ), **kwargs)
    except KeyboardInterrupt:
        raise KeyboardInterrupt()
    except Exception:
        pass


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=DEFAULT_LOG_LEVEL):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


def get_logger(name):
    logger = loggers.get(name)
    if logger is None:
        logger = getLogger(name)
        logger.setLevel(DEFAULT_LOG_LEVEL)  # opcional
        setattr(logger, "debug_armve", debug_armve)
        logger.debug_armve = MethodType(debug_armve, logger)

        # Le asociamos los handlers
        if LOG_TO_DB:
            add_socket_handler(logger)
        if LOG_TO_FILE:
            add_file_handler(logger)
        if LOG_TO_STDOUT and not LOG_CAPTURE_STDOUT:
            add_stdout_handler(logger)
        if LOG_TO_SENTRY:
            add_raven_logger(logger, LOG_SENTRY_PATH)
        loggers[name] = logger
    return logger


def add_socket_handler(logger):
    handler = SocketHandler(LOGGING_SERVER_HOST,
                            DEFAULT_TCP_LOGGING_PORT)
    logger.addHandler(handler)


def add_file_handler(logger):
    try:
        log_file = LOG_NAME % logger.name.lower()
        if not os.path.exists(log_file):
            try:
                open(log_file, 'w').close()
            except IOError:
                pass
        handler = RotatingFileHandler(log_file,
                                      maxBytes=FILELOG_SIZE,
                                      backupCount=FILELOG_ROTATION)
        logger.addHandler(handler)
    except IOError:
        print("La ubicacion %s no existe" % log_file)


def add_stdout_handler(logger):
    formatter = Formatter(
        "[%(asctime)s] %(name)s %(funcName)s():%(lineno)d\t%(message)s")
    try:
        # Si está instalado rainbow_logging_handler (coloriza el output
        # de consola) lo usamos, sino defaulteamos al módulo logging
        from rainbow_logging_handler import RainbowLoggingHandler
        handler = RainbowLoggingHandler(sys.stderr, color_funcName=(
            'black', 'black', True))
    except ImportError:
        handler = StreamHandler()
        pass

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def add_raven_logger(logger, raven_url):
    from raven.base import Client
    from raven.handlers.logging import SentryHandler

    client = Client(raven_url, auto_log_stacks=True)
    handler = SentryHandler(client)
    logger.addHandler(handler)

