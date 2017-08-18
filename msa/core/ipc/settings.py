UPSTREAM_CHANNEL = "/tmp/upstream"
DOWNSTREAM_CHANNEL = "/tmp/downstream"

try:
    from msa.core.ipc.settings_local import *
except ImportError:
    pass
