# -*- coding: utf-8 -*-
from msa.core.constants import CIERRE_ESCRUTINIO
from msa.voto.controllers.recuento import ControllerRecuento


class ControllerTotalizador(ControllerRecuento):

    def actualizar_resultados(self, seleccion, cant_leidas, image_data):
        """ Actualiza la grilla de resultados del recuento """

        self.send_command("preview_acta", {"tipo": CIERRE_ESCRUTINIO,
                                           "imagen": image_data,
                                           "hide_titulo": True})
        cat_list, listas = self._get_data_listas()
        self.send_command("forzar_generar_tabla_recuento",
                          [cat_list, listas, cant_leidas])
