"""Maneja la sumatoria de votos del escrutinio."""
from msa.core.data.candidaturas import Candidatura, Categoria


class Pizarra():

    """Clase que maneja la sumatoria de votos del escrutinio."""

    def __init__(self):
        """Constructor de la Pizarra.

        Es una representacion de la Pizarra Fisica que usan las autoridades de
        mesa en las elecciones tradicionales.
        """
        self.__resultados = {}
        candidaturas = Candidatura.seleccionables()
        for candidatura in candidaturas:
            self.set_votos_candidato(candidatura.id_umv, 0)

    def validar_seleccion(self, seleccion):
        """Valida que la seleccion tiene una cantidad permitida de votos por
        categoria.

        Argumentos:
            seleccion -- un objeto de tipo seleccion
        """
        # a menos que digamos otra cosa la seleccion es valida
        selecciones_validas = True
        len_selec = 0
        categorias = Categoria.all()
        # voy a recorrer las categorias fijandome que la cantidad de votos
        # almacenados en el objeto seleccion es valida para cada una de ellas
        candidatos = seleccion.candidatos_elegidos()
        for categoria in categorias:
            len_selecciones_categoria = 0
            # sumo a la cantidad maxima de selecciones
            len_selec += int(categoria.max_selecciones)
            for candidato in candidatos:
                # si el candidato pertenece a la categoría sumo un voto para el
                # total de votos de la misma
                if candidato.cod_categoria == categoria.codigo:
                    len_selecciones_categoria += 1
            # si hay mas votos que la cantidad de selecciones maximas
            # permitidas salimos
            if len_selecciones_categoria > int(categoria.max_selecciones):
                selecciones_validas = False
                break

        return selecciones_validas and len_selec == len(candidatos)

    def sumar_seleccion(self, seleccion):
        """Suma una seleccion en caso de ser válida.

        Argumentos:
            seleccion -- Un objeto de tipo Seleccion.
        """
        if self.validar_seleccion(seleccion):
            # Si la seleccion es valida recorro cada candidatura y le sumo un
            # voto. Este es el lugar donde las cosas se hacen realidad.
            for candidato in seleccion.candidatos_elegidos():
                self._sumar_un_voto_candidato(candidato.id_umv)
        else:
            raise ValueError("La cantidad de candidatos en la "
                             "seleccion no coincide con la esperada")

    def votos_candidato(self, id_umv):
        """Devuelve la cantidad de votos que tiene una candidatura.

        Argumentos:
            id_umv -- el id_umv de una candidatura.
        """
        return self.__resultados[id_umv]

    def get_votos_actuales(self):
        """Devuelve la cantidad de votos que posee cada candidatura."""
        return self.__resultados

    def set_votos_candidato(self, id_umv, votos):
        """Devuelve la cantidad de votos que tiene una candidatura.

        Argumentos:
            id_umv -- el id_umv de una candidatura.
            votos -- la cantidad de votos que se quiere establecer
        """
        assert type(votos) == int

        seleccionables = Candidatura.seleccionables()
        candidato = seleccionables.one(id_umv=id_umv)
        if candidato is not None:
            self.__resultados[id_umv] = votos
        else:
            raise ValueError

    def _sumar_un_voto_candidato(self, id_umv):
        """Le suma un voto a una candidatura.

        Argumentos:
            id_umv -- el id_umv de una candidatura.
        """
        # aca es donde efectivamente se suman los votos.
        self.__resultados[id_umv] += 1
