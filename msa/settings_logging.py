from logging import INFO as logging_INFO

# settings relativas a logging
DEFAULT_LOG_LEVEL = logging_INFO
LOGGING_SERVER_HOST = 'localhost'

#settings para logging local
LOG_TO_FILE = False
LOG_TO_DB = False
LOG_TO_STDOUT = False
LOG_TO_SENTRY = False
LOG_SENTRY_PATH = ''

LOG_CAPTURE_STDOUT = False

FILELOG_SIZE = 100000
FILELOG_ROTATION = 9
LOG_NAME = "/var/log/msa/%s.log"
