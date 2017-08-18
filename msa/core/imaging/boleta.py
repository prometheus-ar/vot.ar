from os.path import join
from textwrap import wrap

from msa.core.constants import PATH_IMAGENES_VARS
from msa.core.data.candidaturas import Categoria
from msa.core.data.helpers import get_config
from msa.core.imaging import Imagen
from msa.core.imaging.constants import (DEFAULTS_BLOQUE,
                                        DEFAULTS_MOSTRAR_BOLETA,
                                        MEDIDAS_BOLETA, PATH_BLOQUE)


class ImagenBoleta(Imagen):
    """Clase para la imagen de la boleta."""
    def __init__(self, seleccion, mostrar):
        self.template = "boletas/voto.tmpl"
        self.render_template()
        self.seleccion = seleccion
        self.medidas = self._get_medidas()
        self.data = None
        self._mostrar = DEFAULTS_MOSTRAR_BOLETA
        if mostrar is not None:
            self._mostrar.update(mostrar)

    def generate_data(self):
        """Genera la data para mandar al template de la boleta."""
        data = {}
        if not self.config_vista("en_pantalla"):
            troquel, sub_troquel = self._get_troquel()
            data['troquel'] = troquel
            data['sub_troquel'] = sub_troquel
        else:
            self.medidas['margen_izq'] = 5

        if self.config_vista("verificador"):
            data['verificador'] = self._get_verificador()

        data['width'], data['height'] = self._get_size()
        data['escudo'] = self._get_escudo()
        data['titulo'], data['subtitulo'] = self._get_titulos()
        data['margen_izq'] = self.medidas["margen_izq"]
        if self.config_vista("en_pantalla"):
            data['multiplicador_fz'] = self.config_vista("multiplicador_fz")
        else:
            data['multiplicador_fz'] = 1

        secciones = self._get_datos_candidatos()
        data['secciones'] = secciones

        data['watermark'] = self._get_watermark()
        self.data = data
        return data

    def _get_watermark(self):
        """Devuelveve los datos de la posicion del watermark."""
        watermarks = []
        if (self.config_vista("watermark") and
                not self.config_vista("en_pantalla")):
            # solo muestro la marca de agua si imprimo (con verificador)
            for posicion in self.medidas['pos_watermark']:
                watermark = (posicion[0], posicion[1], _("watermark_text"),
                             posicion[2])
                watermarks.append(watermark)

        return watermarks

    def _get_troquel(self):
        """Devuelve los datos de lo que se debe imprimir en el troquel."""
        pos_troquel = self.medidas['pos_troquel']

        troquel = (pos_troquel[0], pos_troquel[1], _("texto_troquel_1"),
                   pos_troquel[2])
        sub_troquel = (pos_troquel[3], pos_troquel[4], _("texto_troquel_2"),
                       pos_troquel[5])

        return troquel, sub_troquel

    def _get_medidas(self):
        """Devuelve las medidas de la boleta."""
        return MEDIDAS_BOLETA

    def _get_verificador(self):
        """Devuelve los datos del verificador para el template."""
        img_path = join(PATH_IMAGENES_VARS, self.medidas['img_verificador'])
        img_link = self._get_img_b64(img_path)

        pos_verif = self.medidas['pos_verif']
        verif_size = self.medidas['verif_size']
        verificador = (pos_verif[0] + self.medidas["margen_izq"], pos_verif[1],
                       img_link, verif_size[0], verif_size[1], _("verifique"),
                       _("su_voto"))
        return verificador

    def _get_size(self):
        u"""Trae los tamaños de la boleta."""
        if self.config_vista("en_pantalla"):
            size = (self.medidas['alto_solo_mostrar'],
                    self.medidas['ancho_boleta'])
        elif self.config_vista('verificador'):
            size = (self.medidas['alto_con_verif'],
                    self.medidas['ancho_boleta'])
        else:
            size = (self.medidas['alto_boleta'],
                    self.medidas['ancho_boleta'])

        return size

    def _get_escudo(self):
        """Genera los datos del escudo."""
        img_link = self._get_img_b64(join(PATH_IMAGENES_VARS,
                                          'logo_boleta.png'))

        data_escudo = (self.medidas['margen_izq'] +
                       self.medidas["logo"][0],
                       self.medidas["logo"][1],
                       self.medidas["dimensiones_logo"][0],  # width
                       self.medidas["dimensiones_logo"][1],  # height
                       img_link)
        return data_escudo

    def _get_titulos(self):
        """Genera los datos de los titulos de la boleta para el template."""
        datos = get_config('datos_eleccion')
        texto_titulo = datos['titulo']
        titulo = (self.medidas['margen_izq'] +
                  self.medidas['titulo'][0],
                  self.medidas['titulo'][1],
                  texto_titulo,
                  self.medidas['fs_titulo'],
                  self.medidas['alto_boleta'])

        texto_subtitulo = datos['subtitulo']

        mostrar_ubicacion = self.config("mostrar_ubicacion_boleta",
                                        self.seleccion.mesa.cod_datos)
        if mostrar_ubicacion:
            texto_subtitulo += " - %s" % self.seleccion.mesa.municipio

        subtitulo = (self.medidas['margen_izq'] +
                     self.medidas['subtitulo'][0],
                     self.medidas['subtitulo'][1],
                     texto_subtitulo,
                     self.medidas['fs_subtitulo'],
                     self.medidas['alto_boleta'])

        return titulo, subtitulo

    def _get_datos_candidatos(self):
        """Devuelve los datos de los candidatos de la seleccion."""
        filter = {
            "sorted": "posicion"
        }
        mostrar_adheridas = self.config("mostrar_adheridas_boleta",
                                        self.seleccion.mesa.cod_datos)
        if not mostrar_adheridas:
            filter["adhiere"] = None

        categorias = Categoria.many(**filter)
        template = self.seleccion.mesa.template_ubic()
        candidatos = self.seleccion.candidatos_elegidos()
        if template is not None:
            cand_bloques = len([cand for cand in candidatos
                                if cand.categoria.adhiere is None
                                or mostrar_adheridas])
            if cand_bloques > len(template.bloques):
                template = self.seleccion.mesa.fallback_template()

        secciones = []
        if template is not None:
            categorias_usadas = []
            idx_categorias = [categoria.codigo for categoria in categorias]

            # recorro las selecciones, traigo los daots del candidato.
            for candidato in candidatos:
                if candidato.categoria.adhiere is None or mostrar_adheridas:
                    datos = self._get_datos_candidato(candidato, template,
                                                    idx_categorias,
                                                    categorias_usadas)
                    secciones.append(datos)

        return secciones

    def _armar_layout(self, template, index):
        """Arma el dicconario de datos con los defaults de todas las configs +
        los defaults para el template en particular + lo que establece para si
        mismo ada bloque."""
        layout = {}
        layout.update(DEFAULTS_BLOQUE)
        layout.update(template.get_default())
        layout.update(template.bloques[index])

        return layout

    def _generar_titulo_bloque(self, layout, seccion, categoria, margen_sup):
        # si no hay titulo queda en cero
        alto_titulo = 0
        if layout["mostrar_titulo"]:
            lineas_titulo = []
            # El titulo de la categoría se muestra siempre en mayúscula
            nombre_categoria = categoria.nombre.upper()

            # Si el titulo es mas largo tiene unas de una linea
            pos_y = margen_sup - 10
            pos_wrap = pos_y
            for linea_wrapeada in wrap(nombre_categoria,
                                       layout["wrap_titulo"]):
                linea = (pos_wrap, linea_wrapeada)
                pos_wrap += layout['alto_fondo_titulo']
                lineas_titulo.append(linea)

            seccion["titulo"] = {
                "pos_x": 4,
                "pos_y": pos_y,
                "lineas": lineas_titulo,
                "width": layout["ancho"],
                "font_size": layout["font_size_titulo"],
            }

            alto_titulo = layout['alto_fondo_titulo'] * len(lineas_titulo);
            seccion["box_titulo"]  = {
                "pos_x": 1,
                "pos_y": margen_sup,
                "width": layout["ancho"] - 5,
                "height": alto_titulo,
            }
        # devolvemos el alto del titulo que es lo que va a empujar para abajo a
        # todo el resto de los elementos del bloque
        return alto_titulo

    def _generar_nro_lista_bloque(self, layout, seccion, categoria, candidato,
                                  alto_titulo):
        pos_num_lista = (seccion["margen_sup"] + alto_titulo +
                         layout["padding_num_lista"])

        num_lista = None
        if candidato.es_blanco:
            texto_lista = ""
        elif categoria.consulta_popular:
            texto_lista = candidato.lista.nombre.upper()
        else:
            num_lista = candidato.lista.numero.lstrip("0")
            texto_lista = " ".join((_("palabra_lista"), num_lista))

        seccion["numero_lista"] = {
            "pos_y": pos_num_lista,
            "texto": texto_lista,
            "numero": num_lista,
            "em": layout["em_num_lista"],
        }

        return pos_num_lista + layout['padding_nom_lista']

    def _generar_lista_bloque(self, layout, seccion, categoria, candidato,
                              padding_lista):

        if candidato.es_blanco or categoria.consulta_popular:
            nombre_lista = ""
            padding_lista += layout['sep_lineas_lista']
        else:
            lineas_titulo = []
            mostrar_partido = self.config("mostrar_partido_en_boleta",
                                          self.seleccion.mesa.cod_datos)
            if mostrar_partido and candidato.partido is not None:
                for linea_wrapeada in wrap(candidato.partido.nombre,
                                           layout["wrap_lista"]):
                    linea = (padding_lista, linea_wrapeada)
                    padding_lista += layout['sep_lineas_lista']
                    lineas_titulo.append(linea)

            for linea_wrapeada in wrap(candidato.lista.nombre,
                                       layout["wrap_lista"]):
                linea = (padding_lista, linea_wrapeada)
                padding_lista += layout['sep_lineas_lista']
                lineas_titulo.append(linea)
            nombre_lista = lineas_titulo

        seccion["nombre_lista"] = {
            "pos_y": padding_lista,
            "lineas": nombre_lista,
            "em": layout["em_nom_lista"],
        }
        return padding_lista

    def _generar_candidato_bloque(self, layout, seccion, categoria, candidato,
                                  padding_lista):
        # nombre del primer candidato
        y_candidato = padding_lista + layout["padding_cand_titular"]
        nombre_candidato = []
        nombre = candidato.nombre
        if categoria.consulta_popular and len(candidato.secundarios):
            nombre = " ".join(candidato.secundarios)

        for linea_wrapeada in wrap(nombre, layout["wrap_candidato"]):
            linea = (y_candidato, linea_wrapeada)
            y_candidato += layout["sep_lineas_titular"]
            nombre_candidato.append(linea)

        seccion["nombre_candidato"] = {
            "pos_y": y_candidato,
            "lineas": nombre_candidato,
            "em": layout["em_candidato"],
        }

        return y_candidato

    def _generar_secundarios_bloque(self, layout, seccion, categoria,
                                    candidato, y_candidato):
        pad_sec = layout['padding_secundarios']
        # nombre del resto de los candidatos (si hay)
        y_secundarios = y_candidato + pad_sec
        secundarios = candidato.secundarios
        if len(secundarios) and not categoria.consulta_popular:
            candidatos_secundarios = "; ".join([cand for cand
                                               in secundarios])
            lineas_texto = []
            for linea_wrapeada in wrap(candidatos_secundarios,
                                       layout["wrap_secundarios"]):
                linea = (y_secundarios, linea_wrapeada)
                y_secundarios += layout['sep_lineas_secundarios']
                lineas_texto.append(linea)
            seccion['secundarios'] = {
                "pos_y": y_secundarios,
                "lineas": lineas_texto,
                "em": layout["em_secundarios"]
            }
        return y_secundarios

    def _generar_suplentes_bloque(self, layout, seccion, categoria,
                                  candidato, y_suplentes):
        pad_sec = layout['padding_suplentes']
        # nombre del resto de los candidatos (si hay)
        suplentes = candidato.suplentes
        mostrar_suplentes = self.config("mostrar_suplentes_en_boleta",
                                        self.seleccion.mesa.cod_datos)
        if mostrar_suplentes and len(suplentes) and not \
                categoria.consulta_popular:
            candidatos_suplentes = "; ".join([cand for cand in suplentes])
            y_suplentes = y_suplentes + pad_sec
            lineas_texto = [(y_suplentes, _("Suplentes:"))]
            y_suplentes += layout['sep_lineas_suplentes']
            for linea_wrapeada in wrap(candidatos_suplentes,
                                       layout["wrap_suplentes"]):
                linea = (y_suplentes, linea_wrapeada)
                y_suplentes += layout['sep_lineas_suplentes']
                lineas_texto.append(linea)

            seccion['suplentes'] = {
                "pos_y": y_suplentes,
                "lineas": lineas_texto,
                "em": layout["em_suplentes"]
            }

        return y_suplentes

    def _generar_adherida_bloque(self, layout, seccion, categoria,
                                 y_secundarios):
        # si no quiero mostrar las categorias adheridas como paneles separados
        # seguramente quiera mostrar la seleccion dentro del bloque del padre
        pad_sec = layout['padding_secundarios']
        mostrar_adheridas = self.config("mostrar_adheridas_boleta",
                                        self.seleccion.mesa.cod_datos)
        if not mostrar_adheridas:
            hijas = Categoria.many(adhiere=categoria.codigo)
            lineas_texto = []
            for hija in hijas:
                cands_hijos = self.seleccion.candidato_categoria(hija.codigo)
                if cands_hijos is not None:
                    candidatos = [cands_hijos[0].nombre]
                    candidatos += cands_hijos[0].secundarios
                    cand_hijo = "{}: {}".format(hija.nombre,
                                                "; ".join(candidatos))
                    y_secundarios = y_secundarios + pad_sec
                    for linea_wrapeada in wrap(cand_hijo,
                                               layout["wrap_adherentes"]):
                        linea = (y_secundarios, linea_wrapeada)
                        y_secundarios += layout['sep_lineas_adherentes']
                        lineas_texto.append(linea)
            seccion['adherentes'] = {
                "pos_y": y_secundarios,
                "lineas": lineas_texto,
                "em": layout["em_adherentes"]
            }

    def _get_datos_candidato(self, candidato, template, idx_categorias,
                             categorias_usadas):
        categoria = candidato.categoria

        index = idx_categorias.index(categoria.codigo)
        if categoria in categorias_usadas:
            index += categorias_usadas.count(categoria)
        categorias_usadas.append(categoria)

        layout = self._armar_layout(template, index)

        #margen_izq = self.medidas['margen_izq']
        margen_sup = layout['padding_selecciones']

        seccion = {}
        seccion["layout"] = layout
        seccion["ancho_texto"] = layout['ancho'] - layout['diff_ancho_texto']
        seccion['posicion'] = layout["posicion"]
        seccion['font_size'] = layout["font_size"]
        seccion['height'] = layout['alto']
        seccion['width'] = layout['ancho']
        seccion['mostrar_titulo'] = layout["mostrar_titulo"]
        seccion['mostrar_borde'] = layout["mostrar_borde"]
        seccion['rotar_bloque'] = layout["rotar_bloque"]
        seccion['margen_sup'] = margen_sup
        seccion['template'] = PATH_BLOQUE.format(layout["nombre_template"])
        seccion["es_blanco"] = candidato.es_blanco

        # titulo de la categoria (fondo negro, letras blancas)
        alto_titulo = self._generar_titulo_bloque(layout, seccion, categoria,
                                                  margen_sup)
        # genero el numero de lista si es necesario
        padding_lista = self._generar_nro_lista_bloque(layout, seccion,
                                                       categoria, candidato,
                                                       alto_titulo)
        # genero la descripcion de la agrupación
        padding_lista = self._generar_lista_bloque(layout, seccion, categoria,
                                                   candidato, padding_lista)
        # genero la descripcion del candidato
        y_candidato = self._generar_candidato_bloque(layout, seccion,
                                                     categoria, candidato,
                                                     padding_lista)
        # genero los candidatos secundarios
        y_secundarios = self._generar_secundarios_bloque(layout, seccion,
                                                         categoria, candidato,
                                                         y_candidato)
        # genero los candidatos suplentes
        y_secundarios = self._generar_suplentes_bloque(layout, seccion,
                                                       categoria, candidato,
                                                       y_secundarios)
        # genero los datos de la categoría adherida a este bloque
        self._generar_adherida_bloque(layout, seccion, categoria,
                                      y_secundarios)

        return seccion
