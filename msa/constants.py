from os.path import join

PATH_CODIGO = '/cdrom/app/msa/'  # poner la barra al final
PATH_REPO_RECURSOS = '/cdrom/app_recursos/'
PATH_VARS = join(PATH_CODIGO, 'var')
PATH_CONFIGS = join(PATH_VARS, 'config')
PATH_RECURSOS = join(PATH_CODIGO, 'recursos')
PATH_TTS = join(PATH_VARS, 'tts')
PATH_FUENTES = join(PATH_RECURSOS, 'fuentes')
PATH_CERTS = join(PATH_REPO_RECURSOS, 'keys')
PATH_CD = '/cdrom'

COD_LISTA_BLANCO = 'BLC'
COD_NULO = 'NUL'
COD_IMPUGNADO = 'IMP'
COD_RECURRIDO = 'REC'
COD_OBSERVADO = 'OBS'
COD_TOTAL = 'TOT'

CAM_BOL_CONT = "boletas_contadas"
CAM_TOT_VOT = "total_votantes"
PLANILLAS_DATOS_EXTRA = [CAM_TOT_VOT, CAM_BOL_CONT]

try:
    from msa.constants_extras import *
except ImportError:
    pass
