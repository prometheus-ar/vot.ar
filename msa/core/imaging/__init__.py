# -*- coding: utf-8 -*-
import cairo
import rsvg
import textwrap

from base64 import b64encode
from jinja2 import Environment, FileSystemLoader
from os.path import join
from PIL import Image

from msa import get_logger
from msa.constants import COD_LISTA_BLANCO, COD_TOTAL
from msa.core import get_config, get_tipo_elec
from msa.core.imaging.constants import RESOLUCION_BAJA, RESOLUCION_ALTA, \
    MEDIDAS_BOLETA
from msa.core.constants import DPI_VOTO_ALTA, DPI_VOTO_BAJA
from msa.core.data.candidaturas import Lista, Categoria, Candidato
from msa.core.settings import IMPRESION_HD_BOLETAS
from msa.core.settings import USA_ARMVE, PATH_IMAGENES_CORE, USAR_QR, \
    PATH_TEMPLATES_BOLETAS
from msa.settings import MODO_DEMO


logger = get_logger("imaging")
env = Environment(loader=FileSystemLoader(PATH_TEMPLATES_BOLETAS))


def get_dpi_boletas():
    if IMPRESION_HD_BOLETAS:
        dpi = DPI_VOTO_ALTA
    else:
        dpi = DPI_VOTO_BAJA
    return dpi


def xml2pil(xml, width, height):
    """ Takes an SVG as input, renders via cairo and returns it as a PIL image
    """
    # http://stackoverflow.com/questions/6589358/convert-svg-to-png-in-python
    # http://cairographics.org/pythoncairopil/
    handle = rsvg.Handle(None, xml)
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    context = cairo.Context(surface)
    handle.render_cairo(context)
    return Image.frombuffer('RGBA', (width, height), surface.get_data(), 'raw',
                            'RGBA', 0, 1)


class Imagen(object):
    def generate_data(self):
        raise NotImplementedError("You must implement on subclass")

    def render_svg(self):
        data = self.generate_data()
        template = env.get_template(self.template)
        xml = template.render(**data)
        return xml

    def render_image(self):
        xml = self.render_svg()
        return xml2pil(xml, self.data['width'], self.data['height'])

    def _get_img_b64(self, img_path):
        image = open(img_path)
        img_data = b64encode(image.read())
        image.close()
        img_link = "data:image/png;base64,%s" % img_data
        return img_link


class ImagenPrueba(Imagen):
    def __init__(self, hd=True):
        self.template = "test.svg"
        self.hd = hd

    def generate_data(self):
        svg_args = {}
        if self.hd:
            if USA_ARMVE:
                ancho_boleta = 832
            else:
                ancho_boleta = 800
        else:
            ancho_boleta = 263  # Ancho en baja de apertura y cierre.

        alto_boleta = 938  # Alto de apertura y cierre.
        svg_args['width'] = ancho_boleta
        svg_args['height'] = alto_boleta

        self.data = svg_args

        return svg_args


class ImagenActa(Imagen):
    def __init__(self, titulo, data, recuento=None, hd=True, qr=None,
                 de_muestra=False, verificador=True, categoria=None):
        self.template = "actas.svg"
        self.titulo = titulo
        self.data = data
        self.recuento = recuento
        self.hd = hd
        self.qr = qr
        self.de_muestra = de_muestra
        self.verificador = verificador
        self.categoria = categoria

        if recuento is not None:
            self.template_texto = "texto_recuento.tmpl"
        else:
            self.template_texto = "texto_apertura.tmpl"

    def _get_medidas(self):
        if self.hd:
            ancho_boleta = 800
            if USA_ARMVE:
                ancho_boleta += 32
        else:
            ancho_boleta = 263  # Ancho en baja de apartura y cierre.

        alto_boleta = 938  # Alto de apertura y cierre.
        if self.recuento is not None:
            if self.hd:
                if USA_ARMVE:
                    alto_boleta = 2950
                else:
                    alto_boleta = 2800
            elif self.de_muestra:
                alto_boleta = 2050
        elif self.hd:
                alto_boleta = 2060
        return ancho_boleta, alto_boleta

    def _get_verificador(self):
        # muestro imagen verificador y corro margen superior hacia abajo
        if not self.de_muestra and self.verificador:
            if self.hd:
                verif_y = 270
                verif_x = 60
            else:
                verif_y = 16
                verif_x = 26
            if USA_ARMVE:
                img_verif = join(PATH_IMAGENES_CORE,
                                 'verificador_%s.png' % ("alta" if self.hd
                                                         else "baja"))
            else:
                img_verif = join(PATH_IMAGENES_CORE,
                                 'verificador_%s.png' % ("alta_circular" if
                                                         self.hd else "baja"))
            img_verif = self._get_img_b64(img_verif)

            return (verif_x, verif_y, img_verif)

    def _get_qr(self, width):
        qr = None
        if not self.de_muestra:
            if self.qr is not None and USAR_QR:
                if self.recuento is not None:
                    qr = (width - 430, 40, self.qr, 400, 400)
                else:
                    qr = (width - 530, 1420, self.qr, 500, 500)

        return qr

    def _get_id_planilla(self, width):
        id_planilla = None
        if not self.de_muestra:
            if self.recuento is not None:
                id_planilla = (width - 440 - 17 *
                               len(self.recuento.mesa.id_planilla),
                               80,
                               self.recuento.mesa.id_planilla)
        return id_planilla

    def _get_escudo(self):
        escudo = None
        if not self.de_muestra:
            logo = self._get_img_b64(join(PATH_IMAGENES_CORE,
                                          'logo_boleta.png'))
            y = 20 if not self.de_muestra else 0
            escudo = (40, y * self.zoom, logo)
        return escudo

    def _get_titulos(self):
        titulos = [None, None, None, None, None]
        if not self.de_muestra:
            x = 20
            y = 70 * self.zoom if not self.de_muestra else 0
            encabezado_actas = (x, y, "Tribunal Electoral")
            titulo = (x, y + 12 * self.zoom, "Provincia de Ejemplo")
            elecciones = (x, y + 24 * self.zoom,
                          "Elecciones de Autoridades")
            abiertas = (x, y + 36 * self.zoom, "Provinciales y Municipales")
            obligatorias = (x, y + 48 * self.zoom, "")
            titulos = (encabezado_actas, titulo, elecciones, abiertas,
                       obligatorias)

        return titulos

    def _get_titulo(self):
        dy = 225 if not self.de_muestra else 20
        return (self.margin_center, dy * self.zoom,
                textwrap.wrap(self.titulo, 50))

    def _get_texto(self):
        texto = ""
        if self.data['mostrar_texto']:
            tmpl_suplentes = env.get_template("texto_suplentes.tmpl")
            tmpl_presidente = env.get_template("texto_presidente.tmpl")
            template = env.get_template(self.template_texto)

            self.data['texto_suplentes'] = tmpl_suplentes.render(**self.data)
            self.data['texto_presidente'] = tmpl_presidente.render(**self.data)
            self.texto = template.render(**self.data)

            dy = 250 if not self.de_muestra else 40
            texto = (self.margin_center, dy * self.zoom,
                     textwrap.wrap(self.texto, 65))
        return texto

    def _get_tabla(self, width):
        ret = {}
        empujar_firmas = 0
        lineas = []
        # muestro la tabla solo si tiene recuento
        mostrar_partidos = any([lista.cod_partido for lista in Lista.all()])
        if self.categoria is None:
            categorias = Categoria.many(sorted="posicion")
        else:
            categorias = Categoria.many(codigo=self.categoria)

        dx = 10

        # ancho genérico de columnas
        ancho_col = 40 * self.zoom
        # calculo ancho columna descripción
        w = width - dx * 2 - len(categorias) * ancho_col
        w = w - ancho_col           # resto ancho col. nº de lista
        y2 = 370 if not self.de_muestra else 160
        lineas.append((y2 * self.zoom, self.margin_left, self.margin_right))

        filas = []
        # listas ordenadas por numero, con blanco al final
        listas = [l for l in Lista.many(sorted='cod_partido, numero')
                  if not l.es_blanco()]

        def _sort_listas(lista_a, lista_b):
            return cmp(int(lista_a.numero)if lista_a.numero != ""
                       else lista_a.codigo,
                       int(lista_b.numero)if lista_b.numero != ""
                       else lista_b.codigo)

        def _sort_listas_paso(lista_a, lista_b):
            return cmp(lista_a.partido.nombre.upper(),
                       lista_b.partido.nombre.upper())

        if get_tipo_elec("paso"):
            listas = sorted(listas, _sort_listas_paso)
        else:
            listas = sorted(listas, _sort_listas)

        lista_blanca = Lista.one(COD_LISTA_BLANCO)
        if lista_blanca is not None:
            listas.append(lista_blanca)
        partido_actual = None
        num_listas = 0
        guiones = ["-"] * (len(categorias) + 1)

        principales = self.recuento._get_dict_candidatos()

        for lista in listas:
            lista_partido = False
            partido = lista.partido
            es_blanco = lista.es_blanco()
            if mostrar_partidos and not es_blanco and \
                    partido_actual != lista.cod_partido:
                partido_actual = lista.cod_partido
                if num_listas == 0:
                    filas = filas[:-1]
                else:
                    num_listas = 0
                una_lista = num_listas == 0 and len(partido.listas) == 1
                if una_lista or partido.nombre == lista.nombre:
                    lista_partido = True
                else:
                    fila = [partido.nombre] + guiones
                    filas.append(fila)
                    lista_partido = False

            numero = lista.numero if lista.numero is not None else ""
            nombre_lista = lista.nombre if not lista_partido else partido.nombre
            if not es_blanco and not lista_partido and get_tipo_elec("paso"):
                nombre_lista = "-- " + nombre_lista
            fila = [nombre_lista, numero]
            for categoria in categorias:
                candidato = principales.get((lista.codigo, categoria.codigo))
                resultado = "- "
                if candidato is not None:
                    resultado = self.recuento.obtener_resultado(
                        categoria.codigo, candidato.codigo)
                fila.append(resultado)
            num_listas += 1
            filas.append(fila)

        empujar_firmas += len(filas) * 23

        # Armando tabla superior
        x = self.margin_left
        y = (350 if not self.de_muestra else 140) * self.zoom
        ancho_columnas = [w, ancho_col] + [ancho_col] * len(categorias)
        titulo_columnas = [_("palabra_lista"), "Nº"] + \
            [cat.codigo for cat in categorias]
        columnas = []
        for i, titulo in enumerate(titulo_columnas):
            columna = [titulo]
            for fila in filas:
                max_chars = ancho_columnas[i] * 80 / 800
                data = fila[i] if i > 0 else fila[i][:max_chars]
                columna.append(data)
            columnas.append((columna, x, y, ancho_columnas[i]))
            x += ancho_columnas[i]

        ret['alto_rectangulo'] = len(filas) * 23
        ret['tabla'] = columnas

        titulo_columnas = ["Cod.", _("palabra_categoria"), "N°"]
        w = width - dx * 2 - ancho_col * 3
        ancho_columnas = [ancho_col, w, ancho_col]
        y2 = 385 if not self.de_muestra else 173
        lineas.append((y2 * self.zoom + empujar_firmas, self.margin_left,
                       self.margin_right))

        valores_especiales = []
        for lista_esp in get_config("listas_especiales"):
            _cod_esp = lista_esp.split(".")[-1]
            valores_especiales.append(
                (_cod_esp, _("titulo_votos_%s" % _cod_esp),
                 self.recuento.listas_especiales[lista_esp]))

        general = self.recuento.boletas_contadas()
        general += sum(self.recuento.listas_especiales.values())
        valores_especiales.append((COD_TOTAL, _("total_general"), general))

        x = self.margin_left
        y += empujar_firmas + 30

        columnas = []
        for i, titulo in enumerate(titulo_columnas):
            columna = [titulo]
            for fila in valores_especiales:
                columna.append(fila[i])
            columnas.append((columna, x, y, ancho_columnas[i]))
            x += ancho_columnas[i]
        ret['alto_rectangulo_especiales'] = len(valores_especiales) * 23
        ret['tabla_especiales'] = columnas
        empujar_firmas += len(valores_especiales) * 23

        ret['lineas'] = lineas
        return ret, empujar_firmas

    def _get_firmas(self, empujar_firmas):
        lineas = []
        autoridades = None
        fiscales = None
        # firmas autoridades:
        if not self.de_muestra:
            lineas.append((410 * self.zoom + empujar_firmas, self.margin_left,
                           self.margin_right))

            autoridades = (self.margin_left, 422 * self.zoom + empujar_firmas,
                           _("firmas_autoridades"))
            lineas.append((540 * self.zoom + empujar_firmas, self.margin_left,
                           self.margin_right))
            fiscales = (self.margin_left, 552 * self.zoom + empujar_firmas,
                        _("firmas_fiscales"))
            lineas.append((655 * self.zoom + empujar_firmas, self.margin_left,
                           self.margin_right))

        return autoridades, fiscales, lineas

    def _get_watermark(self):
        watermark = None
        if MODO_DEMO and not self.de_muestra:
            watermark = (-500, 600, _("watermark_text"))
        return watermark

    def generate_data(self):
        self.margin_center = "50%"
        self.margin_left = 10
        self.margin_right = 810
        self.zoom = 2 if self.hd else 0.71

        data = {"margin_center": self.margin_center}

        data['width'], data['height'] = self._get_medidas()
        data['verificador'] = self._get_verificador()
        data['qr'] = self._get_qr(data['width'])
        data['id_planilla'] = self._get_id_planilla(data['width'])
        data['escudo'] = self._get_escudo()
        data['titulo1'], data['titulo2'], data["titulo3"], \
            data["titulo4"], data["titulo5"] = self._get_titulos()
        data['titulo_acta'] = self._get_titulo()
        data['texto_acta'] = self._get_texto()
        if self.recuento is not None:
            data_rec, empujar_firmas = self._get_tabla(data['width'])
            data.update(data_rec)
        else:
            empujar_firmas = 0
            data['lineas'] = []

        data['autoridades'], data['fiscales'], lineas = \
            self._get_firmas(empujar_firmas)
        for linea in lineas:
            data['lineas'].append(linea)

        data['watermark'] = self._get_watermark()

        self.data = data
        return data


class ImagenBoleta(Imagen):
    def __init__(self, seleccion, verificador=True, de_muestra=False):
        self.template = "voto.svg"
        self.seleccion = seleccion
        self.verificador = verificador
        self.de_muestra = de_muestra
        self.medidas_boleta = self._get_medidas_boleta()
        self.data = None

    def generate_data(self):
        data = self._get_diccionario_boleta()
        if not self.de_muestra:
            troquel, sub_troquel = self._get_troquel()
            data['troquel'] = troquel
            data['sub_troquel'] = sub_troquel

            if self.verificador:
                data['verificador'] = self._get_verificador()
        else:
            self.medidas_boleta['margen_izq'] = 0

        data['width'], data['height'] = self._get_size()
        data['escudo'] = self._get_escudo()
        data['titulo'], data['subtitulo'] = self._get_titulos()

        lineas, secciones = self._get_datos_candidatos()
        data['lineas'] = lineas
        data['secciones'] = secciones

        data['watermark'] = self._get_watermark()
        self.data = data
        return data

    def _get_watermark(self):
        if MODO_DEMO and not self.de_muestra:
            # solo muestro la marca de agua si imprimo (con verificador)
            watermark = (self.medidas_boleta['pos_watermark'][0],
                         self.medidas_boleta['pos_watermark'][1],
                         _("watermark_text"),
                         self.medidas_boleta['pos_watermark'][2])
        else:
            watermark = None

        return watermark

    def _get_troquel(self):
        pos_troquel = self.medidas_boleta['pos_troquel']

        troquel = (pos_troquel[0], pos_troquel[1], _("texto_troquel_1"),
                   pos_troquel[2])
        sub_troquel = (pos_troquel[3], pos_troquel[4], _("texto_troquel_2"),
                       pos_troquel[5])

        return troquel, sub_troquel

    def _get_medidas_boleta(self):
        if self.de_muestra or IMPRESION_HD_BOLETAS:
            size_boleta = RESOLUCION_ALTA
        else:
            size_boleta = RESOLUCION_BAJA
        medidas_boleta = MEDIDAS_BOLETA[size_boleta]

        return medidas_boleta

    def _get_diccionario_boleta(self):
        data = {
            "ancho_linea": self.medidas_boleta['ancho_linea'],
        }

        return data

    def _get_verificador(self):
        img_path = join(PATH_IMAGENES_CORE,
                        self.medidas_boleta['img_verificador'])
        img_link = self._get_img_b64(img_path)

        pos_verif = self.medidas_boleta['pos_verif']
        verif_size = self.medidas_boleta['verif_size']
        verificador = (pos_verif[0], pos_verif[1], img_link, verif_size[0],
                       verif_size[1])
        return verificador

    def _get_size(self):
        if self.de_muestra:
            size = (self.medidas_boleta['alto_solo_mostrar'],
                    self.medidas_boleta['ancho_boleta'])
        elif self.verificador:
            size = (self.medidas_boleta['alto_con_verif'],
                    self.medidas_boleta['ancho_boleta'])
        else:
            size = (self.medidas_boleta['alto_boleta'],
                    self.medidas_boleta['ancho_boleta'])

        return size

    def _get_escudo(self):
        img_link = self._get_img_b64(join(PATH_IMAGENES_CORE,
                                          'logo_boleta.png'))

        data_escudo = (self.medidas_boleta['margen_izq'] +
                       self.medidas_boleta["logo"][0],
                       self.medidas_boleta["logo"][1],
                       self.medidas_boleta["dimensiones_logo"][0],  # width
                       self.medidas_boleta["dimensiones_logo"][1],  # height
                       img_link)
        return data_escudo

    def _get_titulos(self):
        datos = get_config('datos_eleccion')
        titulo = (self.medidas_boleta['margen_izq'] +
                  self.medidas_boleta['titulo'][0],
                  self.medidas_boleta['titulo'][1],
                  datos["titulo"].encode("utf8"),
                  self.medidas_boleta['fs_titulo'],
                  self.medidas_boleta['alto_boleta'])

        subtitulo = (self.medidas_boleta['margen_izq'] +
                     self.medidas_boleta['subtitulo'][0],
                     self.medidas_boleta['subtitulo'][1],
                     datos["subtitulo"].encode("utf8"),
                     self.medidas_boleta['fs_subtitulo'],
                     self.medidas_boleta['alto_boleta'])

        return titulo, subtitulo

    def _get_datos_candidatos(self):
        templates = self.seleccion.mesa.templates_impresion(
            forzar_media=self.de_muestra)
        margen_izq = self.medidas_boleta['margen_izq']  # margen izquierdo
        original_dx = margen_izq
        idx_categorias = [categoria.codigo for categoria in
                          Categoria.many(sorted="posicion")]
        categorias_usadas = []
        lineas = []
        secciones = []

        # recorro las selecciones, dibujo el cargo elegido, lista, etc.
        for candidato in self.seleccion._candidatos:
            datos = self._get_datos_candidato(candidato, templates,
                idx_categorias, categorias_usadas, lineas)
            secciones.append(datos)

        for categoria in categorias_usadas:
            index = idx_categorias.index(categoria.codigo)
            template_impresion = templates[index]
            w = template_impresion['ancho']
            h = template_impresion['alto']
            if template_impresion.get('vr', True):
                dx = original_dx + template_impresion['posicion'][0]
                dy = self.medidas_boleta['padding_selecciones'] + \
                    template_impresion['posicion'][1]
                # sep vert (sin encabezado)
                puntos = (dx + w - 1, dy, dx + w - 1, dy + h)
                lineas.append(puntos)

        return lineas, secciones

    def _get_datos_candidato(self, candidato, templates, idx_categorias,
                            categorias_usadas, lineas):
        categoria = candidato.categoria
        #lista = Lista.one(candidato.cod_lista)

        margen_izq = self.medidas_boleta['margen_izq']
        margen_sup = self.medidas_boleta['padding_selecciones']

        index = idx_categorias.index(categoria.codigo)
        if categoria in categorias_usadas:
            index += categorias_usadas.count(categoria)
        layout = templates[index]

        categorias_usadas.append(categoria)
        w = layout['ancho']
        h = layout['alto']
        dy = margen_sup + layout['posicion'][1]
        dx = margen_izq + layout['posicion'][0]
        br = layout.get('wrap_secundarios', 40)
        brl = layout.get('wrap_lista', 40)
        brn = layout.get('wrap_candiadto', 30)
        fz = layout.get('font_size', self.medidas_boleta['default_tfz'])
        tfz = layout.get('tfz', self.medidas_boleta['default_tfz'])
        lfz = tfz - 1
        lnfz = self.medidas_boleta['fs_numero_lista']
        if layout.get('hr', False):
            # sep horiz (categorias intermedias)
            lineas.append((dx, dy + h, dx - 2 + w, dy + h))


        # titulo de la categoria (fondo negro, letras blancas)
        seccion = {}
        seccion['posicion'] = layout["posicion"]
        seccion['template'] = layout.get("tmpl", "bloque") + ".tmpl"

        seccion["titulo"] = (
            margen_izq + w / 2,
            margen_sup + (self.medidas_boleta['alto_fondo_titulo'] / 1.4),
            categoria.nombre, tfz, w)

        h = self.medidas_boleta['alto_fondo_titulo']
        seccion["box_titulo"] = (margen_izq + 1, margen_sup , w - 5, h,
                                 categoria.codigo)

        pos_datos_lista = margen_sup + h + \
            self.medidas_boleta['padding_txt_lista']
        # texto lista
        x = margen_izq + w - 4
        if not candidato.lista.es_blanco() and not categoria.consulta_popular:
            #separacion = layout.get('sp', separacion)
            seccion['texto_lista'] = (x, pos_datos_lista, _("palabra_lista"),
                                      lfz, w, categoria.codigo)

        pos_num_lista = pos_datos_lista + \
            self.medidas_boleta['padding_num_lista']

        if candidato.lista.es_blanco():
            num_lista = _("palabra_blanco")
        elif categoria.consulta_popular:
            num_lista = candidato.lista.nombre
        else:
            num_lista = candidato.lista.numero.lstrip("0")

        seccion["numero_lista"] = (x, pos_num_lista, num_lista, lnfz, w,
                                   categoria.codigo)

        padding_lista = margen_sup + self.medidas_boleta['padding_nom_lista']

        if candidato.lista.es_blanco() or categoria.consulta_popular:
            nombre_lista = ""
        else:
            lineas_titulo = []
            if candidato.partido is not None and candidato.partido.nombre != candidato.lista.nombre:
                for linea_wrapeada in textwrap.wrap(candidato.partido.nombre,
                                                    brl):
                    linea = (padding_lista, linea_wrapeada)
                    padding_lista += self.medidas_boleta['sep_lineas_lista']
                    lineas_titulo.append(linea)
            for linea_wrapeada in textwrap.wrap(candidato.lista.nombre, brl):
                linea = (padding_lista, linea_wrapeada)
                padding_lista += self.medidas_boleta['sep_lineas_lista']
                lineas_titulo.append(linea)
            nombre_lista = lineas_titulo

        seccion["nombre_lista"] = (dx + w / 2,
                                   padding_lista, nombre_lista, fz - 1, w)

        # nombre del primer candidato
        y_candidato = padding_lista + \
            self.medidas_boleta['padding_cand_titular']
        nombre_candidato = []
        for linea_wrapeada in textwrap.wrap(candidato.nombre, brn):
            linea = (y_candidato, linea_wrapeada)
            y_candidato += self.medidas_boleta['sep_lineas_titular']
            nombre_candidato.append(linea)

        x = dx + w / 2
        seccion["nombre_candidato"] = (x, y_candidato,
                                       nombre_candidato, fz + 2, w)

        # nombre del resto de los candidatos (si hay)
        secundarios = candidato.secundarios
        if len(secundarios):
            candidatos_secundarios = "; ".join([cand.nombre for cand
                                               in secundarios])
            lineas_texto = []
            y_secundarios = y_candidato + \
                self.medidas_boleta['padding_secundarios']
            for linea_wrapeada in textwrap.wrap(candidatos_secundarios, br):
                linea = (y_secundarios, linea_wrapeada)
                y_secundarios += self.medidas_boleta['sep_lineas_secundarios']
                lineas_texto.append(linea)
            x = margen_izq + w / 2
            seccion['secundarios'] = (x, y_secundarios, w,
                fz - self.medidas_boleta['fs_secundarios'],
                lineas_texto)

        return seccion


class ImagenReversoBoleta(Imagen):
    def __init__(self, config):
        self.template = "reverso_boleta_base.svg"
        self.data = config

    def generate_data(self):
        return self.data
