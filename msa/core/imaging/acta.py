import textwrap

from os.path import join

from msa.constants import COD_TOTAL
from msa.core.constants import PATH_IMAGENES_VARS
from msa.core.data.candidaturas import Agrupacion, Candidatura, Categoria
from msa.core.imaging import Imagen, jinja_env
from msa.core.imaging.constants import MEDIDAS_ACTA, COLORES
from msa.settings import MODO_DEMO


class ImagenActa(Imagen):
    def __init__(self, titulo, data, recuento=None, qr=None,
                 de_muestra=False, verificador=True, grupo_cat=None):
        """Constructor.

        Argumentos:
            titulo: titulo del acta.
            data: datos para rellenar el acta.
            recuento: Un objeto recuento (solo para actas de cierre).
            qr: imagen del QR.
            de_muestra: True si es la version para mostrar en pantalla.
            verificador: Muestra el icono que marca la posicion del chip.
            grupo_cat: el grupo de categorias de la cual queremos hacer el acta.
        """
        self.template = "actas/acta.tmpl"
        self.render_template()
        self.titulo = titulo
        self.data = data
        self.recuento = recuento
        self.qr = qr
        self.de_muestra = de_muestra
        # TODO: manejar el offset mejor, mover a get_medidas,
        # eliminar varible
        if de_muestra:
          self.offset_top = 370
        else:
          self.offset_top = 0
        self.verificador = verificador
        self.grupo_cat = grupo_cat

        template = "recuento" if recuento is not None else "apertura"
        self.template_texto = "actas/textos/%s.tmpl" % template

    def _get_medidas(self):
        """Devuelve las medidas del acta."""

        if self.recuento is not None:
            alto = MEDIDAS_ACTA["alto_recuento"]
        else:
            alto = MEDIDAS_ACTA["alto_apertura"]

        medidas = {
            "width": MEDIDAS_ACTA["ancho"],
            "height": alto,
            "alto_linea_tabla": MEDIDAS_ACTA["alto_linea_tabla"],
        }
        return medidas


    def generate_data(self):
        """Genera todos los datos que vamos a necesitar para armar el acta."""
        medidas = self._get_medidas()
        data = {
            "colores": COLORES,
            "medidas": medidas,
            "width": medidas['width'],
            "height": medidas['height'],
            "encabezado": self._get_encabezado(),
            "i18n": self._get_i18n(),
            "qr": self._get_qr(medidas['width']),
            "mesa": self.data['mesa'],
            "escudo": self._get_escudo(),
            "verificador": self._get_verificador(),
            "texto_acta": self._get_texto(),
            "watermark": self._get_watermark(),
            "de_muestra": self.de_muestra,
            "presidente": self.data['presidente'],
            "suplentes": self.data['suplentes'],
            "leyenda": self.data['leyenda'],
            "pie": self.data['pie'],
        }

        if self.recuento is not None:
            data["tabla"] = self._get_tabla()
        data["posiciones"] = self._get_posiciones(data)

        self.data = data
        return data

    def _get_posiciones(self, data):
        """Averigua la ubicacion de cada uno de los elementos del acta."""
        posiciones = {}

        # Traigo las medidas que necesito para hacer el calculo
        fin_encabezado = MEDIDAS_ACTA['fin_encabezado']
        alto_linea_texto = MEDIDAS_ACTA['alto_linea_texto']
        alto_linea_tabla = MEDIDAS_ACTA['alto_linea_tabla']
        separacion_especiales = MEDIDAS_ACTA['separacion_especiales']
        separacion_firmas = MEDIDAS_ACTA['separacion_firmas']
        alto_firmas = MEDIDAS_ACTA['alto_firmas']

        # primero vamos a averigual el alto del texto del acta
        if data['texto_acta'] is not None:
            alto_texto_acta = alto_linea_texto * len(data["texto_acta"][1])
        else:
            alto_texto_acta = 0

        # si un acta de cierre tenemos que mostrar latabla y el resto de las
        # cosas estan ubicados despues de la tabla
        if self.recuento is not None:
            # el alto de la tabla es igual a la cantidad de filas
            alto_tabla = alto_linea_tabla * len(data["tabla"]["filas"])
            # lo mismo para la tablita de especiales
            alto_especiales = (alto_linea_tabla *
                               len(data["tabla"]["especiales"]))
            # sabiendo donde esta el fin del encabezado le sumamos el alto del
            # texto de la tabla y le restamos el offset superior que esta
            # relacionado directamente con si la imagen es la "de muestra"
            posiciones['tabla'] = (fin_encabezado + alto_texto_acta -
                                   self.offset_top)
            # las listas especiales van abajo de la tabla, con cierta
            # separacion
            posiciones['especiales'] = (posiciones['tabla'] + alto_tabla +
                                        separacion_especiales)
            # posicionamos las firmas
            posiciones['firmas'] = (posiciones['especiales'] + alto_especiales
                                    + separacion_firmas)
        else:
            # si no hay tabla las firmas van directamente abajo del texto
            posiciones['firmas'] = (fin_encabezado + alto_texto_acta -
                                    self.offset_top)
        # calculamos el final de las firmas
        posiciones['final'] = (data["height"] - posiciones['firmas'] -
                               alto_firmas)

        # si es una apertura y mostramos un QR tenemos que achicar el final de
        # las firmas por que sino tapan al QR, vamos a dejar un poquito mas de
        # espacio por un tema de legibilidad
        if self.recuento is None and data["qr"] is not None:
            posiciones['final'] -= data["qr"][3] + 50

        # si la imagen es para mostrar en pantalla tocamos las medidas de la
        # imagen para ajustarlas al contenido.
        if self.de_muestra:
            data["height"] = posiciones['firmas']
            data["medidas"]["height"] = posiciones['firmas']

        return posiciones

    def _get_encabezado(self):
        # Devuelve los datos del encabezado
        datos = {
            "nombre_acta": self.titulo,
            "texto": self._get_texto_encabezado()
        }

        return datos

    def _get_i18n(self):
        textos = {
            "mesa": _("mesa"),
            "firmas_autoridades": _("firmas_autoridades"),
            "firmas_fiscales": _("firmas_fiscales"),
            "firmas_fiscales_detalle": _("firmas_fiscales_detalle"),
            "agrupaciones": _("agrupaciones"),
            "titulo_especiales": _("titulo_especiales"),
            "cantidad": _("cantidad"),
        }

        return textos

    def _get_qr(self, width):
        """Devuelve los datos del QR para el template."""
        qr = None
        if not self.de_muestra:
            usar_qr = self.config("usar_qr", self.data["cod_datos"])
            if self.qr is not None and usar_qr:
                key = "qr_recuento" if self.recuento is not None \
                    else "qr_apertura"
                pos_x, pos_y, pos_w, pos_h = MEDIDAS_ACTA[key]
                qr = [width - pos_x, pos_y, self.qr, pos_w, pos_h]

        return qr

    def _get_escudo(self):
        """Devuelve los datos del escudo para el template."""
        logo = self._get_img_b64(join(PATH_IMAGENES_VARS, 'logo_boleta.png'))
        pos_x, pos_y = MEDIDAS_ACTA["escudo"]
        escudo = (pos_x, pos_y, logo)
        return escudo

    def _get_verificador(self):
        """Devuelve los datos del verificador para el template."""
        # muestro imagen verificador y corro margen superior hacia abajo
        if not self.de_muestra and self.verificador:
            verif_x, verif_y = MEDIDAS_ACTA["verificador"]
            img_verif = join(PATH_IMAGENES_VARS, 'verificador_alta.png')
            img_verif = self._get_img_b64(img_verif)

            return (verif_x, verif_y, img_verif)

    def _get_texto_encabezado(self):
        """Devuelve los datos de los titulos para el template."""
        lineas = []

        if not self.de_muestra:
            # Esto sería un for si no cambiara tanto de eleccion a eleccion
            # probamos varias cosas con los años, esta es la solucion mas
            # customisable
            lineas = [
                _("encabezado_acta_1"),
                _("encabezado_acta_2"),
                _("encabezado_acta_3"),
                _("encabezado_acta_4"),
                _("encabezado_acta_5")
            ]

        return lineas

    def _get_texto(self):
        """Devuelve los datos del texto del acta para el template."""
        texto = None
        if self.data['mostrar_texto']:
            # traigo los templates
            tmpl_suplentes = jinja_env.get_template("actas/textos/suplentes.tmpl")
            tmpl_presidente = jinja_env.get_template("actas/textos/presidente.tmpl")
            template = jinja_env.get_template(self.template_texto)
            # los renderizo y los meto en data
            self.data['texto_suplentes'] = tmpl_suplentes.render(**self.data)
            self.data['texto_presidente'] = tmpl_presidente.render(**self.data)
            # y le paso todo al template del texto para armar el texto del acta
            self.texto = template.render(**self.data)

            posicion, wrap = MEDIDAS_ACTA['texto']
            dy = posicion - self.offset_top
            texto = (dy, textwrap.wrap(self.texto, wrap))
        return texto

    def _get_watermark(self):
        """Devuelve el watermark de las actas."""
        watermarks = []
        if MODO_DEMO and not self.de_muestra:
            # solo muestro la marca de agua si imprimo (con verificador)
            for posicion in MEDIDAS_ACTA['pos_watermark']:
                watermark = (posicion[0], posicion[1], _("watermark_text"),
                             posicion[2])
                watermarks.append(watermark)
        return watermarks

    def _get_datos_especiales(self):
        """Devuelve los valores para la tabla de listas especiales."""
        valores_especiales = []
        for lista_esp in self.recuento.mesa.listas_especiales:
            fila = (lista_esp, _("titulo_votos_%s" % lista_esp),
                    self.recuento.listas_especiales[lista_esp])
            valores_especiales.append(fila)

        # Armamos el total general
        general = self.recuento.boletas_contadas()
        general += sum(self.recuento.listas_especiales.values())
        valores_especiales.append((COD_TOTAL, _("total_general"), general))

        len_general = len(str(general))
        if len_general < 3:
            len_general = 3

        return valores_especiales, len_general

    def _get_datos_tabla(self, categorias, agrupaciones):
        """Devuelve los datos de la tabla principal del acta.

        Argumentos:
            categorias -- las categorias que queremos mostrar en la tabla.
            agrupaciones -- las agrupaciones que participan en esta Ubicacion.
        """
        filas = []
        max_char = 3
        partido_omitido = False
        clases_a_mostrar = self.config("clases_a_mostrar",
                                       self.data["cod_datos"])
        colapsar_partido = self.config("colapsar_partido",
                                       self.data["cod_datos"])
        # Recorro todas las agrupaciones (Alianza, Partido, Lista)
        # viendo cual segun la forma de la eleccion y las configuraciones debo
        # mostrar
        for agrupacion in agrupaciones:
            # si esta la eleccion configurada para mostrar esa clase de
            # agrupacion
            clase = agrupacion.clase
            if clase in clases_a_mostrar:
                # colapso el partido si tiene una sola lista y esta habilitado
                if colapsar_partido and clase == "Partido":
                    partido_omitido = len(agrupacion.listas) == 1
                # Traigo los datos de la fila en caso de que tenga que
                # mostrarla
                if not partido_omitido or (partido_omitido and
                                           clase != "Partido"):
                    fila, chars_lista = self._get_datos_fila(categorias,
                                                             agrupacion,
                                                             partido_omitido)
                    # Las listas solo aparecen si tienen candidatos en
                    # categorias que queremos mostrar en este acta.
                    if (clase != "Lista" or not
                            all([elem=="-" for elem in fila[3:]])):
                        if chars_lista > max_char:
                            max_char = chars_lista
                        filas.append(fila)

        # Vemos si tenemos votos en blanco para agregar
        fila_blanca = self._get_datos_fila_blanca(categorias)
        if fila_blanca is not None:
            filas.append(fila_blanca)

        return filas, max_char

    def _get_datos_fila_blanca(self, categorias):
        """Devuelve los datos de la fila de votos en blanco.

        Argumentos:
            categorias -- las categorias que queremos mostrar en la tabla.
        """
        mostrar_numero = self.config("numero_lista_en_tabla",
                                     self.data["cod_datos"])
        numero = " " if mostrar_numero else ""
        # Manejo de la fila que tiene los votos en blanco
        fila = [numero, _("votos_en_blanco"), 0]
        # cantidad_blancos no es un booleano por que a veces en algunas
        # elecciones esta bueno saber cuantas candidaturas en blanco hay
        cantidad_blancos = 0
        # Recorro todas las categorias buscando las candidaturas blancas en
        # caso de que las haya
        for categoria in categorias:
            candidato = Candidatura.get_blanco(categoria.codigo)
            # el contenido del cuadro va a ser "-" a menos que haya algun
            # candidato blanco en esta categoria para esta Ubicacion
            resultado = "-"
            if candidato is not None:
                resultado = self.recuento.get_resultados(candidato.id_umv)
                # muestro la cantidad de blancos
                cantidad_blancos += 1
            fila.append(resultado)
        # si tengo candidatos blancos tenemos que mostar la fila de blancos.
        if not cantidad_blancos:
            fila = None

        return fila

    def _get_datos_fila(self, categorias, agrupacion, partido_omitido):
        """Devuelve los datos de la tabla principal del acta.

        Argumentos:
            categorias -- las categorias que queremos mostrar en la tabla.
            agrupacion -- la agrupacion de la que estamos mostrando la tabla
        """
        # primero vamos a averiguar la indentacion que queremos ponerle a esta
        # fila en la tabla.
        clases_a_mostrar = self.config("clases_a_mostrar",
                                       self.data["cod_datos"])
        mostrar_numero = self.config("numero_lista_en_tabla",
                                     self.data["cod_datos"])
        indentacion = clases_a_mostrar.index(agrupacion.clase)
        # si el partido no esta omitido vamos a ponerle profundidad.
        if not partido_omitido:
            nombre = " " * indentacion
            nombre += agrupacion.nombre
        # sino el nombre pasa de largo y queda el que está.
        else:
            nombre = agrupacion.partido.nombre
        # establecemos el numero de la lista. En alguna eleccion esto puede ser
        # mas complejo que traer el numero, puede ser la concatenacion de
        # varios numeros diferentes.
        if mostrar_numero and hasattr(agrupacion, "numero"):
            numero = str(agrupacion.numero)
        else:
            numero = ""

        # armamos la base de la fila.
        fila = [numero, nombre, indentacion]

        # Recorremos todas las categorias que queremos mostrar en este acta
        # buscando cuantos votos tiene cada candidato.
        for categoria in categorias:
            candidato = Candidatura.one(cod_lista=agrupacion.codigo,
                                        cod_categoria=categoria.codigo)
            # Si el candidato existe vamos a buscar cuantos votos tiene y sino
            # devolvemos "-" que se transforma en una cruz en el acta
            if candidato is not None:
                votos = self.recuento.get_resultados(candidato.id_umv)
            else:
                votos = "-"
            fila.append(votos)

        return fila, len(numero)

    def _get_categorias(self):
        # Ordenamos siempre por la posicion de la Categoria.
        filter = {
            "sorted": "posicion",
        }

        # Quizas queremos omitir las categorias adheridas, como en algunas
        # elecciones en las que el vicegobernador es un cargo que adhiere al de
        # gobernador.
        mostrar_adheridas = self.config("mostrar_adheridas",
                                        self.data["cod_datos"])
        if not mostrar_adheridas:
            filter["adhiere"] = None

        # En caso de querer generar la tabla con un solo grupo de categorias
        if self.grupo_cat is not None:
            filter["id_grupo"] = self.grupo_cat

        # Traemos todas las categorias con el filtro que acabamos de armar
        categorias = Categoria.many(**filter)

        return categorias

    def _get_tabla(self):
        """Construye la tabla del recuento y devuelve los datos."""

        categorias = self._get_categorias()
        # traigo los datos de las listas especiales
        especiales, caracteres_categoria = self._get_datos_especiales()
        dx = MEDIDAS_ACTA['margen_derecho_tabla']
        # ancho genérico de columnas
        ancho_col = MEDIDAS_ACTA['ancho_col']
        # calculo ancho columna descripción
        w = 700 - dx - len(categorias) * ancho_col
        w = w - ancho_col  # resto ancho col. nº de lista

        clases_a_mostrar = self.config("clases_a_mostrar",
                                       self.data["cod_datos"])
        # Traemos solo las agrupaciones que queremos mostrar segun existe en el
        # juego de datos y segun tenemos configurado en clases_a_mostrar
        agrupaciones = Agrupacion.many(clase__in=clases_a_mostrar,
                                       sorted="orden_absoluto")
        # traemos todas las filas
        filas, caracteres_lista = self._get_datos_tabla(categorias,
                                                        agrupaciones)

        # calculo la cantidad maxima de caracteres que debe tener el nombre de
        # la agrupacion que estoy mostrando
        caracteres_tabla = MEDIDAS_ACTA['caracteres_tabla']
        cods_categorias = [cat.codigo for cat in categorias]

        # corto el largo del nombre de las agrupaciones
        remain_chars = (caracteres_tabla - caracteres_lista -
                        (len(cods_categorias) * caracteres_categoria))
        for i in range(len(filas)):
            filas[i][1] = filas[i][1][:int(remain_chars)]


        tabla = {
            "filas": filas,
            "especiales": especiales,
            "categorias": cods_categorias,
            "len_categorias": len(cods_categorias),
            "caracteres_categoria": caracteres_categoria,
            "caracteres_lista": caracteres_lista,
        }

        return tabla
