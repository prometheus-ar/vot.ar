# -*- coding: utf-8 -*-
from construct import Container, RangeError

from msa.core.data.candidaturas import Categoria, Candidatura
from msa.core.data import Ubicacion
from msa.core.documentos.constants import LEN_LEN_UBIC, LEN_LEN_OPC
from msa.core.documentos.structs import struct_voto
from msa.core.exceptions import MesaIncorrecta
from msa.core.imaging.boleta import ImagenBoleta
from msa.core.i18n.decorators import forzar_idioma
from msa.core.i18n.settings import DEFAULT_LOCALE


class Seleccion(object):

    """Seleccion de candidatos (voto)."""

    def __init__(self, mesa, interna=None, candidatos=None):
        self.mesa = mesa
        self.__candidatos = candidatos[:] if candidatos else []
        self.interna = interna

    def elegir_candidato(self, candidato, borrar=True):
        """Guarda un candidato seleccionado.

        Argumentos:
            candididato -- un objeto Candidatura.
            borrar -- Borra todos los candidatos de esa categoria si es True
        """
        # Primero nos fijamos que el candididato no sea None
        if candidato is not None:
            # y despues buscamos que ese candidato efectivamente exista
            seleccionables = Candidatura.seleccionables()
            encontrado = seleccionables.one(id_umv=candidato.id_umv)
            if encontrado is not None:
                if borrar:
                    self.borrar_categoria(candidato.cod_categoria)
                self.__candidatos.append(candidato)
            else:
                raise ValueError
        else:
            raise ValueError

    def borrar_categoria(self, cod_categoria):
        """Borra los candidatos de una categoria.

        Argumentos:
            cod_categoria -- el codigo de la categoria de la que se quieren
                borrar los candidatos
        """
        remover = []
        for candidato in self.__candidatos:
            if str(candidato.cod_categoria) == str(cod_categoria):
                remover.append(candidato)
        for candidato in remover:
            self.__candidatos.remove(candidato)

    def candidato_categoria(self, cod_categoria):
        """Determina si se ha seleccionado candidato para una categoria.
           Si se eligio lo devuelve."""
        candidatos = [c for c in self.__candidatos
                      if c.cod_categoria == cod_categoria]
        if candidatos:
            return candidatos
        else:
            return None

    def candidatos_elegidos(self):
        """Devuelve una copia de la lista con los canditatos elegidos."""
        return self.__candidatos[:]

    def rellenar_de_blanco(self):
        """Agrega voto en blanco a las categorias que no fueron votadas."""
        for categoria in Categoria.many():
            if self.candidato_categoria(categoria.codigo) is None:
                blanco = Candidatura.one(cod_categoria=categoria.codigo,
                                         clase="Blanco")
                if blanco is not None:
                    self.elegir_candidato(blanco)

    def a_tag(self):
        """Devuelve la informacion de la seleccion para almacenar en tag rfid.
        """
        # Generamos el largo del codigo de ubicacion de la mesa
        # Y los votos de cada categoria
        votos_categorias = self._votos_categorias()

        ubicacion = bytes(self.mesa.cod_datos, "ascii")
        len_ubic = bytes(str(len(ubicacion)).zfill(LEN_LEN_UBIC), "ascii")
        opciones = bytes(votos_categorias, "ascii")
        len_opciones = bytes(str(len(opciones)).zfill(LEN_LEN_OPC), "ascii")

        container = Container(len_ubic=len_ubic,
                              ubicacion=ubicacion,
                              opciones=opciones,
                              len_opciones=len_opciones)
        built = struct_voto.build(container)
        return built

    def _votos_categorias(self):
        """Devuelve una lista con los votos a guardar en el tag."""
        categorias = []
        cand_ordenados = sorted(self.__candidatos,
                                key=lambda cand: cand.categoria.posicion)
        for candidato in cand_ordenados:
            categoria = "{}:{}".format(candidato.cod_categoria,
                                       candidato.id_umv)
            categorias.append(categoria)
        return ",".join(categorias)

    @forzar_idioma(DEFAULT_LOCALE)
    def a_imagen(self, mostrar=None, svg=False):
        """Genera la imagen de la boleta."""
        imagen = ImagenBoleta(self, mostrar)
        rendered = imagen.render(svg)
        return rendered

    def __str__(self):
        return ','.join('%s: %s' % (c.cod_categoria, c.id_umv)
                        for c in self.__candidatos)

    @classmethod
    def desde_tag(cls, tag, mesa=None):
        """Devuelve una seleccion a partir de la informacion de un tag rfid.
        """
        seleccion = None

        try:
            datos_tag = struct_voto.parse(tag)
        except RangeError:
            # Manejamos que no nos puedan meter cualquier
            datos_tag = None

        if datos_tag is not None:
            ubic = datos_tag.ubicacion.decode("utf-8")
            if mesa is not None:
                # verificamos la mesa
                if mesa.cod_datos != ubic:
                    raise MesaIncorrecta()
            else:
                # OJO: Esto trae cualquier mesa del juego de datos.
                # No importa cual porque todas las mesas del mismo juego son
                # compatibles pero no nos permite identificar de que mesa es
                # el voto.
                mesa = Ubicacion.first(cod_datos=ubic)
                mesa.usar_cod_datos()

            seleccion = Seleccion(mesa)

            sel_por_cat = {}
            # recorremos cada uno de los pares de categoria/candidatos en el
            # tag
            str_opciones = datos_tag.opciones.decode()
            opciones = str_opciones.split(",")
            if len(opciones):
                for elem in opciones:
                    if len(elem):
                        cod_cat, id_umv = elem.split(":")
                        id_umv = int(id_umv)
                        sel_por_cat[cod_cat] = sel_por_cat.get(cod_cat, 0) + 1

                        # Buscamos el candidato votado para la categoria en
                        # cuestion
                        candidato = Candidatura.one(id_umv=id_umv,
                                                    cod_categoria=cod_cat)
                        # y lo elegimos (Si no encontró ninguno lanza un value
                        # error).
                        if candidato is None:
                            raise ValueError()
                        max_selecciones = int(
                            candidato.categoria.max_selecciones)
                        borrar = max_selecciones == 1
                        seleccion.elegir_candidato(candidato, borrar=borrar)

                if len(list(sel_por_cat.keys())) != len(Categoria.all()):
                    # caso en el que la canditad de categorias votadas sea
                    # diferente que la cantidad de categorias
                    seleccion = None
                else:
                    # aca verificamos que la cantidad de candidatos por
                    # categoria sea menor o igual de la cantidad de selecciones
                    # maximas que esperamos
                    for cod_categoria, cantidad in list(sel_por_cat.items()):
                        categoria = Categoria.one(cod_categoria)
                        max_selec = int(categoria.max_selecciones)
                        if categoria is None or cantidad > max_selec:
                            seleccion = None
                            break

        return seleccion
