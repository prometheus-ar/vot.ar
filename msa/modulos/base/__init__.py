"""
Modulo base.

Contiene:
    * La aplicacion principal que corre la maquina la cual se ocupa de correr
      los diferentes modulos.
    * Las clases base para Controladores, Modulos, Rampa y Actions
"""
import gc
import os
from importlib import import_module

from msa.core.audio.player import WavPlayer
from msa.core.audio.settings import VOLUMEN_GENERAL
from msa.core.i18n import levantar_locales
from msa.modulos.constants import (COMANDO_APAGADO, COMANDO_EXPULSION_CD,
                                   MODULO_APERTURA, MODULO_CALIBRADOR,
                                   MODULO_INICIO, MODULO_TOTALIZADOR, SHUTDOWN,
                                   SUBMODULO_DATOS_APERTURA)


class App():
    def __init__(self, modulos_startup, modulos_habilitados):
        """Constructor de la aplicacion.
        Argumentos:
            modulos_startup -- los modulos que corren previos a la ejecucion
            normal la app (calibrador y el que queramos ejecutar
            explicitamente).
            modulos_habilitados -- modulos habilitados de la aplicacion.
        """
        self.set_locales()
        self.set_volume()
        self.modulos_startup = modulos_startup
        self.modulos_habilitados = modulos_habilitados

    def set_locales(self):
        """Establece los locales de la aplicacion."""
        levantar_locales()

    def set_volume(self):
        """Setea el volumen del audio al nivel deseado antes de iniciar."""
        audioplayer = WavPlayer(as_daemon=False)
        audioplayer.set_volume(VOLUMEN_GENERAL)
        audioplayer.close()

    def _get_modulo_startup(self):
        """Devuelve el proximo modulo de startup"""
        return self.modulos_startup.pop()

    def apagar_maquina(self):
        """Apaga la maquina."""
        os.system(COMANDO_EXPULSION_CD)
        os.system(COMANDO_APAGADO)
        # Gracias, vuelva pronto.

    def _loop(self, modulo=None, titulo=None):
        """Ejecuta la secuencia de modulos de la aplicacion."""
        if modulo is None:
            modulo = self._get_modulo_startup()
        else:
            self.modulos_startup = []

        ejecutar = True
        res = ''
        # la app corre "para siempre" modulo por modulo. A menos que
        # explicitamente salgamos, apaguemos la maquina o salte alguna
        # excepcion
        while ejecutar:
            if modulo in self.modulos_habilitados:
                res = self.ejecutar_modulo(modulo, titulo)

                if len(self.modulos_startup):
                    modulo = self._get_modulo_startup()
                # Si no vengo de un calibrador y el retorno es volver a inicio,
                # o apagar, salgo
                elif not modulo == MODULO_CALIBRADOR and res in (MODULO_INICIO,
                                                                 SHUTDOWN):
                    ejecutar = False
                elif res in self.modulos_habilitados:
                    modulo = res
                # para el disco totalizador.
                # TODO: Habria que resolver mejor esto via disk_runner
                elif res == SUBMODULO_DATOS_APERTURA and MODULO_APERTURA \
                        not in self.modulos_habilitados:
                    modulo = MODULO_TOTALIZADOR

                if res == SHUTDOWN:
                    self.apagar_maquina()
            else:
                raise Exception("El modulo {} no existe".format(modulo))

    def _get_clase_modulo(self, modulo):
        """Devuelve la clase del modulo."""
        if ',' in modulo:
            nombre_paquete, submodulo = modulo.split(",")
        else:
            nombre_paquete = modulo
        paquete = import_module(".%s" % nombre_paquete, "msa.modulos")
        clase_modulo = getattr(paquete, "Modulo")
        return clase_modulo

    def ejecutar_modulo(self, modulo, titulo=None):
        """Ejecuta un modulo de la aplicacion."""
        # Instancio una clase, y ejecuto su metodo main()
        # Este metodo debe devolver un string si quiere llamar a otro modulo
        clase_modulo = self._get_clase_modulo(modulo)
        mod = clase_modulo(modulo)
        res = mod.main(titulo=titulo)

        # Borro explicitamente el modulo de la memoria
        del mod
        # Y ya que estoy llamo al Garbage Collector
        gc.collect()

        return res

    def run(self, modulo=None, titulo=None):
        """Ejecuta el loop de la aplicacion."""
        try:
            self._loop(modulo, titulo)
        except KeyboardInterrupt:
            pass
