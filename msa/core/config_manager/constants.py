COMMON_SETTINGS = "common"
DEFAULT_FILE = "default"
OVERRIDE_FILE = "local"
EXTENSION = "yml"

try:
    from msa.core.config_manager.settings_local import *
except ImportError:
    pass
