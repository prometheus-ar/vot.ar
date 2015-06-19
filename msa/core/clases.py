# -*- coding: utf-8 -*-
from base64 import b64encode
from collections import defaultdict
from cStringIO import StringIO

from construct import Container
from ojota import current_data_code

from msa.core import get_config, get_tipo_elec
from msa.constants import CAM_BOL_CONT, CAM_TOT_VOT
from msa.core.armve.helpers import array_to_printable_string, \
    string_to_array, serial_16_to_8, array_to_string
from msa.constants import COD_LISTA_BLANCO
from msa.core.constants import CIERRE_RECUENTO, CIERRE_TRANSMISION, \
    CIERRE_CERTIFICADO, CIERRE_COPIA_FIEL, CIERRE_ESCRUTINIO
from msa.core.data import Ubicacion
from msa.core.data.candidaturas import Categoria, Candidato, Partido, Lista
from msa.core.decorators import forzar_idioma
from msa.core.exceptions import MesaIncorrecta, SerialRepetido, \
    MesaNoEncontrada, TipoQrErroneo, QRMalformado
from msa.core.imaging import ImagenBoleta, ImagenActa
from msa.core.qr import crear_qr
from msa.core.settings import IMPRESION_HD_APERTURA, USAR_QR, \
    IMPRESION_HD_CIERRE, SMART_PACKING
from msa.settings import DEFAULT_LOCALE
from msa.core.settings import TOKEN
from msa.core.structs import struct_voto, struct_recuento, struct_apertura, \
    struct_recuento_dni
from msa.voto.constants import TIPO_DOC


if SMART_PACKING:
    from msa.core.smart_numpacker import pack, unpack, MAXBITS
else:
    from msa.core.numpacker import pack, unpack

from msa.core.numpacker import pack_slow, unpack_slow


class Apertura(object):

    """Apertura de mesa de votacion."""

    def __init__(self, mesa, autoridades=None, hora=None):
        if autoridades is None:
            autoridades = []
        self.autoridades = autoridades

        self.mesa = mesa
        self.hora = hora or {'horas': 8, 'minutos': 0}

    def a_tag(self):
        """Devuelve la informacion del apertura para almacenar en tag rfid."""
        nombres, dnis, tipos = self.encodear_autoridades()
        container = Container(numero_mesa=int(self.mesa.numero),
                              hora=int(self.hora["horas"]),
                              minutos=int(self.hora["minutos"]),
                              cantidad_autoridades=len(self.autoridades),
                              len_nombres=len(nombres),
                              nombres=nombres,
                              tipos=tipos,
                              dnis=dnis)
        built = struct_apertura.build(container)

        return built

    def encodear_autoridades(self):
        nombres = []
        dnis = []
        tipos = []
        for autoridad in self.autoridades:
            nombres.append(autoridad.apellido)
            nombres.append(autoridad.nombre)
            tipo = "%s" % TIPO_DOC.index(autoridad.tipo_documento)
            tipos.append(tipo)
            campo = pack_slow([int(autoridad.nro_documento)], 27)
            dnis.append(campo)

        nombres = self.encodear_string(";".join(nombres))
        return nombres, dnis, tipos

    def encodear_string(self, string):
        string = unicode(string.upper())
        datos = []
        letra = None
        for char in string:
            codigo_letra = ord(char)
            if 65 <= codigo_letra <= 90:
                letra = codigo_letra - 64
            elif char == "'":
                letra = 28
            elif char == u"Ñ":
                letra = 29
            elif char == " ":
                letra = 30
            elif char == u"Á":
                letra = 1
            elif char == u"É":
                letra = 5
            elif char == u"Í":
                letra = 9
            elif char == u"Ó":
                letra = 15
            elif char == u"Ú":
                letra = 21
            elif char == u";":
                letra = 31

            if letra is not None:
                datos.append(letra)

        ret = pack_slow(datos, 5)
        return ret

    @classmethod
    def decodear_string(cls, string):
        ret = u""
        datos = unpack_slow(string, 5)
        for codigo_letra in datos:
            letra = None
            # A-Z
            if 1 <= codigo_letra <= 27:
                letra = chr(codigo_letra + 64)
            # '
            elif codigo_letra == 28:
                letra = u"'"
            # Ñ
            elif codigo_letra == 29:
                letra = u"Ñ"
            # Espacio
            elif codigo_letra == 30:
                letra = u" "
            elif codigo_letra == 31:
                letra = ";"
            if letra is not None:
                ret += letra
        return ret

    @classmethod
    def desde_tag(self, tag):
        """Devuelve un apertura a partir de la informacion de un tag rfid."""
        autoridades = []
        datos = struct_apertura.parse(tag)
        nro_mesa = datos.numero_mesa
        horas = datos.hora
        minutos = datos.minutos
        mesa = Ubicacion.one(numero=str(nro_mesa))
        nombres = self.decodear_string(datos.nombres).split(";")

        for i in range(datos.cantidad_autoridades):
            apellido = nombres.pop(0)
            nombre = nombres.pop(0)
            tipo = datos.tipos.pop(0)
            dni = unpack_slow(datos.dnis.pop(0), 27)[0]
            autoridad = Autoridad(apellido, nombre, tipo, dni)
            autoridades.append(autoridad)
        return Apertura(mesa, autoridades, hora={"horas": horas,
                                                 "minutos": minutos})

    def a_imagen(self, de_muestra=False, svg=False):
        """Devuelve la imagen para imprimir el apertura."""
        titulo = _("titulo_apertura") % self.mesa.descripcion_completa.upper()
        try:
            presidente = self.autoridades[0]
        except IndexError:
            presidente = ""
        suplentes = self.autoridades[1:]
        datos = {
            'presidente': presidente,
            'suplentes': suplentes,
            'cantidad_suplentes': len(suplentes),
            'mesa': self.mesa.descripcion_completa,
            'escuela': self.mesa.escuela,
            'municipio': self.mesa.municipio,
            'departamento': self.mesa.departamento,
            'horas': "%02d" % self.hora['horas'],
            'minutos': "%02d" % self.hora['minutos'],
            'mostrar_texto': True
        }

        qr_img = self.a_qr_b64_encoded() if USAR_QR and not de_muestra else None
        imagen = ImagenActa(titulo, datos, hd=IMPRESION_HD_APERTURA,
                            de_muestra=de_muestra, qr=qr_img)
        if svg:
            rendered = imagen.render_svg()
        else:
            rendered = imagen.render_image()
        return rendered

    def a_qr_str(self):
        """Devuelve la informacion del recuento para almacenar en qr."""
        # tipo de qr
        # cod_mesa
        #encoded_data = string_to_array(self.a_tag())
        #datos = [int(TOKEN, 16), len(encoded_data) * 2]
        #datos.extend(encoded_data)
        #todo = "A" + array_to_printable_string(datos)
        datos = [self.mesa.numero,
                 "%s:%s" % (self.hora["horas"], self.hora["minutos"])]
        for autoridad in self.autoridades:
            dato = ",".join((autoridad.apellido, autoridad.nombre,
                             str(autoridad.nro_documento)))
            datos.append(dato)
        return ";".join(datos)

    def a_qr(self):
        datos = self.a_qr_str()
        return crear_qr(datos)

    def a_qr_b64_encoded(self):
        qr = self.a_qr()
        output = StringIO()
        qr.save(output, format='PNG')
        qr_img_data = output.getvalue()
        output.close()
        # despues de cerrar el buffer, armo el qr para mostrarlo embebido
        return 'data:image/png;base64,' + b64encode(qr_img_data)

    def __str__(self):
        return 'Apertura de ' + self.mesa.descripcion


class Seleccion(object):

    """Seleccion de candidatos (voto)."""

    def __init__(self, mesa, interna=None, candidatos=None):
        self.mesa = mesa
        self._candidatos = candidatos[:] if candidatos else []
        self.interna = interna

    def elegir_candidato(self, candidato, borrar=True):
        """Elegir un candidato."""
        if candidato is not None:
            if borrar:
                self.borrar_categoria(candidato.cod_categoria)
            self._candidatos.append(candidato)

            categorias_hijas = candidato.categoria.get_hijas()
            if len(categorias_hijas) > 0:
                for cat_hija in categorias_hijas:
                    principal = Candidato.one(cod_categoria=cat_hija.codigo,
                                              cod_lista=candidato.cod_lista,
                                              titular=True,
                                              numero_de_orden=1)
                    self.elegir_candidato(principal)

    def borrar_categoria(self, cod_categoria):
        remover = []
        for candidato in self._candidatos:
            if str(candidato.cod_categoria) == str(cod_categoria):
                remover.append(candidato)
        for candidato in remover:
            self._candidatos.remove(candidato)

    def elegir_lista(self, lista):
        """Elegir una lista."""
        self._candidatos = lista.candidatos
        self.rellenar_de_blanco()

    def candidato_categoria(self, cod_categoria):
        """Determina si se ha seleccionado candidato para una categoria.
           Si se eligio lo devuelve."""
        candidatos = [c for c in self._candidatos
                      if c.cod_categoria == cod_categoria]
        if candidatos:
            return candidatos
        else:
            return None

    def candidatos_elegidos(self):
        """Devuelve todos los canditatos elegidos."""
        return self._candidatos[:]

    def completa(self, interna=None):
        """Determina si la seleccion es completa (candidatos en todas las
           categorias)."""
        if get_tipo_elec("interna") and interna is not None:
            categorias = Categoria.all()
            cat_usadas = []
            for categoria in categorias:
                has_cand = Candidato.one(cod_categoria=categoria.codigo,
                                         cod_interna=interna.codigo)
                if has_cand is not None:
                    cat_usadas.append(categoria)
            len_categoria = len(cat_usadas)

        else:
            len_categoria = len(Categoria.all())
        return len(self._candidatos) == len_categoria

    def rellenar_de_blanco(self):
        for categoria in Categoria.many(consulta_popular=False):
            if self.candidato_categoria(categoria.codigo) is None:
                blanco = Candidato.one(cod_categoria=categoria.codigo,
                                       cod_lista=COD_LISTA_BLANCO)
                self.elegir_candidato(blanco)

    def a_tag(self):
        """Devuelve la informacion de la seleccion para almacenar en tag rfid.
        """
        return self.a_string()

    def a_string(self):
        len_cods = get_config("len_cod")

        len_cod_mesa = ("%d" % len(self.mesa.cod_datos)).zfill(2)
        if self.interna:
            datos_interna = self.interna.codigo.rjust(len_cods["interna"])
        else:
            datos_interna = ' ' * len_cods["interna"]

        categorias = []
        for c in sorted(self._candidatos, key=lambda c: c.cod_categoria):
            categoria = Container(
                cod_categoria=c.cod_categoria.rjust(len_cods["categoria"]),
                cod_candidatura=c.codigo_clean().rjust(len_cods["candidato"]))
            categorias.append(categoria)

        container = Container(len_ubic=len_cod_mesa,
                              ubicacion=self.mesa.cod_datos,
                              cod_interna=datos_interna,
                              voto_categoria=categorias)
        built = struct_voto.build(container)
        return built

    def a_qr(self):
        """Devuelve la informacion de la seleccion para almacenar en qr."""
        return ''

    @forzar_idioma(DEFAULT_LOCALE)
    def a_imagen(self, verificador=True, solo_mostrar=False, svg=False):
        imagen = ImagenBoleta(self, verificador, solo_mostrar)
        if svg:
            rendered = imagen.render_svg()
        else:
            rendered = imagen.render_image()
        return rendered

    def __str__(self):
        return ','.join('%s: %s' % (c.cod_categoria, c.codigo)
                        for c in self._candidatos)

    @classmethod
    def desde_tag(cls, tag, mesa):
        """Devuelve una seleccion a partir de la informacion de un tag rfid.
        """
        return cls.desde_string(tag, mesa)

    @classmethod
    def desde_string(cls, tag, mesa=None):
        datos_tag = struct_voto.parse(tag)

        if mesa is not None:
            # verificamos la mesa
            if mesa.cod_datos != datos_tag.ubicacion:
                raise MesaIncorrecta()
        else:
            #OJO: ESTO trae cualquier mesa del juego de datos
            mesa = Ubicacion.one(cod_datos=datos_tag.ubicacion)
            current_data_code(datos_tag.ubicacion)

        if datos_tag.cod_interna != "":
            interna = Partido.one(datos_tag.cod_interna)
        else:
            interna = None

        candidatos = []
        for elem in datos_tag.voto_categoria:
            cod_categoria = elem["cod_categoria"].strip()
            cod_candidato = elem["cod_candidatura"].strip()

            if cod_candidato == COD_LISTA_BLANCO:
                candidato = Candidato.one(codigo__endswith=cod_candidato,
                                          cod_categoria=cod_categoria)
            else:
                candidato = Candidato.one(codigo__endswith="." + cod_candidato,
                                          cod_categoria=cod_categoria)
            candidatos.append(candidato)

        return Seleccion(mesa, None, candidatos)

    @classmethod
    def desde_qr(cls, datos):
        """Devuelve una seleccion a partir de la informacion de un qr."""
        return Seleccion()


class Recuento(object):

    """Recuento de votos de una mesa."""

    def __init__(self, mesa, autoridades=None, hora=None):
        if autoridades is None:
            autoridades = []

        self.__dict_candidatos = None
        self.autoridades = autoridades
        self.mesa = mesa
        self.cod_categoria = None

        self.hora = hora # si hora es None no se muestra el texto del acta
        _campos_extra = get_config("campos_extra")
        self.campos_extra = dict(zip(_campos_extra, [0] * len(_campos_extra)))
        _lst_esp = get_config("listas_especiales")
        self.listas_especiales = dict(zip(_lst_esp, [0] * len(_lst_esp)))

        self.reiniciar_resultados()

    def actualizar_lista_especial(self, key, votos, suma_al_total=True):
        if suma_al_total:
            valor_actual = self.listas_especiales[key]
            self.campos_extra[CAM_TOT_VOT] += votos - valor_actual

        self.listas_especiales[key] = votos

    def serial_sumado(self, serial):
        """Determina si un serial ya ha sido sumado en el recuento."""
        return serial in self._serials

    def sumar_seleccion(self, seleccion, serial=None):
        """Suma una seleccion a los resultados."""
        if not serial or not self.serial_sumado(serial):
            for candidato in seleccion._candidatos:
                self._resultados[candidato.cod_categoria,
                                 candidato.codigo] += 1
            if serial:
                self._serials.append(serial)
            self.campos_extra[CAM_BOL_CONT] += 1
            self.campos_extra[CAM_TOT_VOT] += 1
        else:
            raise SerialRepetido()

    def obtener_resultado(self, cod_categoria, cod_candidato):
        """Obtiene el resultado de una categoria+lista."""
        return self._resultados[cod_categoria, cod_candidato]

    def boletas_contadas(self):
        """Obtiene la cantidad de selecciones contadas."""
        return self.campos_extra[CAM_BOL_CONT]

    def reiniciar_resultados(self):
        """Reinicia los resultados del recuento."""
        # (cod_categoria, cod_lista) -> votos
        self._resultados = defaultdict(lambda: 0)
        self._serials = []
        self.campos_extra[CAM_BOL_CONT] = 0
        self.campos_extra[CAM_TOT_VOT] = 0

    def sumar_recuento(self, recuento, serial):
        if not serial or not self.serial_sumado(serial):
            for key, votos in recuento._resultados.iteritems():
                actual = self._resultados.get(key, 0)
                self._resultados[key] = actual + votos

            for key, votos in recuento.campos_extra.iteritems():
                actual = self.campos_extra.get(key, 0)
                self.campos_extra[key] = actual + votos

            for key, votos in recuento.listas_especiales.iteritems():
                actual = self.listas_especiales.get(key, 0)
                self.listas_especiales[key] = actual + votos

            if serial:
                self._serials.append(serial)
        else:
            raise SerialRepetido()

    def _get_dict_candidatos(self):
        if self.__dict_candidatos is None:
            cand = {(candidato.cod_lista, candidato.cod_categoria): candidato
                    for candidato in Candidato.many(titular=True,
                                                    numero_de_orden=1)}

            self.__dict_candidatos = cand
        else:
            cand = self.__dict_candidatos

        return cand

    def a_tag(self, cod_categoria=None, con_dnis=True):
        """Devuelve la informacion del recuento para almacenar en tag rfid."""
        # valores ordenados por cod_lista,cod_categoria
        valores = []
        if cod_categoria is not None:
            por_categoria = 1
            categorias = Categoria.many(codigo=cod_categoria)
        else:
            por_categoria = 0
            categorias = Categoria.many(sorted='codigo')

        principales = self._get_dict_candidatos()
        for lista in Lista.many(sorted='codigo'):
            for categoria in categorias:
                try:
                    candidato = principales.get((lista.codigo,
                                                 categoria.codigo))
                    if candidato is not None:
                        cod_candidato = candidato.codigo
                        valores.append(self._resultados[categoria.codigo,
                                                        cod_candidato])
                except AttributeError:
                    #si no hay candidato lo ignoramos
                    pass

        ordered_keys = sorted(self.campos_extra.keys())
        for key in ordered_keys:
            valores.append(self.campos_extra[key])

        ordered_keys = sorted(self.listas_especiales.keys())
        for key in ordered_keys:
            valores.append(self.listas_especiales[key])

        container = Container(por_categoria=str(por_categoria))
        if por_categoria:
            container.cod_categoria = cod_categoria.encode('ascii')
        else:
            container.cod_categoria = ""

        # cod_mesa
        if SMART_PACKING:
            num_mesa = self.mesa.numero.encode('ascii')
            try:
                datos = pack(int(num_mesa), valores)
            except NameError:
                datos = pack(int(num_mesa), valores, max_bits=MAXBITS*2)
        else:
            cod_mesa = self.mesa.codigo.encode('ascii')
            datos = str(len(cod_mesa)) + cod_mesa + pack(valores)

        container.datos = datos
        documentos = []
        for autoridad in self.autoridades:
            documentos.append(int(autoridad.nro_documento))

        if con_dnis:
            documentos = []
            for autoridad in self.autoridades:
                documentos.append(int(autoridad.nro_documento))
            len_documentos = len(documentos)
            if len_documentos == 1:
                documentos.append(0)
            elif len_documentos == 0:
                documentos = [0, 0]

            documentos = pack_slow(documentos, 27)
            container.documentos = documentos

            struct = struct_recuento_dni
        else:
            struct = struct_recuento

        return struct.build(container)

    def a_qr_str(self, cod_categoria=None, con_dnis=True):
        """Devuelve la informacion del recuento para almacenar en qr."""
        # tipo de qr
        # cod_mesa
        encoded_data = string_to_array(self.a_tag(cod_categoria, con_dnis))
        datos = [int(TOKEN, 16), len(encoded_data) * 2]
        datos.extend(encoded_data)
        todo = "R" + array_to_printable_string(datos)
        return todo

    def a_qr(self, cod_categoria=None, con_dnis=True):
        datos = self.a_qr_str(cod_categoria, con_dnis)
        return crear_qr(datos)

    def a_qr_b64_encoded(self, cod_categoria=None):
        qr = self.a_qr(cod_categoria)
        output = StringIO()
        qr.save(output, format='PNG')
        qr_img_data = output.getvalue()
        output.close()
        # despues de cerrar el buffer, armo el qr para mostrarlo embebido
        return 'data:image/png;base64,' + b64encode(qr_img_data)

    def a_imagen(self, tipo=None, de_muestra=False, svg=False):
        """Devuelve la imagen para imprimir recuento."""
        if tipo is None:
            tipo = (CIERRE_RECUENTO, None)

        verif = True
        titulo = ""

        desc_mesa = self.mesa.descripcion_completa.upper()

        if tipo[0] == CIERRE_RECUENTO:
            titulo = _("titulo_recuento") % desc_mesa
        elif tipo[0] == CIERRE_TRANSMISION:
            titulo = _("titulo_transmision") % desc_mesa
        elif tipo[0] == CIERRE_CERTIFICADO or tipo[0] == CIERRE_ESCRUTINIO:
            titulo = _("titulo_certificado") % desc_mesa
            verif = False
        elif tipo[0] == CIERRE_COPIA_FIEL:
            titulo = _("titulo_copia_fiel") % desc_mesa
            verif = False
        categoria = tipo[1]

        try:
            presidente = self.autoridades[0]
        except IndexError:
            presidente = ""
        suplentes = self.autoridades[1:]
        datos = {
            'presidente': presidente,
            'suplentes': suplentes,
            'cantidad_suplentes': len(suplentes),
            'mesa': self.mesa.descripcion_completa,
            'escuela': self.mesa.escuela,
            'municipio': self.mesa.municipio,
            'departamento': self.mesa.departamento,
            'horas': "%02d" % self.hora.get('horas', "") \
                if self.hora is not None else "",
            'minutos': "%02d" % self.hora.get('minutos', "")
                if self.hora is not None else "",
            'mostrar_texto': self.hora is not None
        }

        qr_img = self.a_qr_b64_encoded(categoria) if USAR_QR else None
        imagen = ImagenActa(titulo, datos, hd=IMPRESION_HD_CIERRE,
                            qr=qr_img, recuento=self, categoria=categoria,
                            de_muestra=de_muestra, verificador=verif)

        if svg:
            rendered = imagen.render_svg()
        else:
            rendered = imagen.render_image()

        return rendered

    def __str__(self):
        return 'Recuento de la mesa %s' % self.mesa

    @classmethod
    def desde_tag(cls, tag, con_dnis=True):
        if con_dnis:
            struct = struct_recuento_dni
        else:
            struct = struct_recuento
        datos_tag = struct.parse(tag)
        por_categoria = int(datos_tag.por_categoria)
        cod_categoria = datos_tag.cod_categoria

        if SMART_PACKING:
            num_mesa, valores = unpack("".join(datos_tag.datos))
            mesa = Ubicacion.one(numero=str(num_mesa))
        else:
            tag = "".join(datos_tag.datos)
            len_cod_mesa = int(tag[:2])
            cod_mesa = tag[2:2 + len_cod_mesa]
            mesa = Ubicacion.one(cod_mesa)
            valores = unpack(tag[len_cod_mesa + 2:])

        if not mesa:
            raise MesaNoEncontrada()

        current_data_code(mesa.cod_datos)

        if por_categoria:
            categorias = Categoria.many(codigo=cod_categoria)
        else:
            categorias = Categoria.many(sorted='codigo')

        recuento = Recuento(mesa)
        principales = recuento._get_dict_candidatos()
        # leemos los valores y los seteamos en los resultados
        # vienen ordenados por cod_lista,cod_categoria
        for lista in Lista.many(sorted='codigo'):
            for categoria in categorias:
                candidato = Candidato.one(cod_categoria=categoria.codigo,
                                          cod_lista=lista.codigo, titular=True,
                                          numero_de_orden=1)
                if candidato is not None:
                    recuento._resultados[categoria.codigo,
                                         candidato.codigo] = valores.pop(0)

        ordered_keys = sorted(recuento.campos_extra.keys())
        for key in ordered_keys:
            recuento.campos_extra[key] = valores.pop(0)

        ordered_keys = sorted(recuento.listas_especiales.keys())
        for key in ordered_keys:
            recuento.listas_especiales[key] = valores.pop(0)

        if por_categoria:
            recuento.cod_categoria = cod_categoria

        if con_dnis:
            dnis = unpack_slow(datos_tag.documentos, 27)
            for dni in dnis:
                autoridad = Autoridad("", "", 0, dni)
                recuento.autoridades.append(autoridad)

        return recuento

    @classmethod
    def desde_qr(cls, datos):
        """Devuelve un recuento a partir de la informacion de un qr."""
        # tipo de qr
        token = datos[1:3]
        if not datos.startswith('R') or token != TOKEN:
            raise TipoQrErroneo()

        datos = datos[1:]
        len_datos = int(datos[2:4], 16)
        datos_recuento = datos[4:]
        if len_datos != len(datos_recuento):
            len_datos = int(datos[2:5], 16)
            datos_recuento = datos[5:]
            if len_datos != len(datos_recuento):
                raise QRMalformado()
        datos_recuento = array_to_string(serial_16_to_8(datos_recuento))
        recuento = Recuento.desde_tag(datos_recuento, con_dnis=True)

        return recuento

    def a_human(self):
        texto = "%s - %s, %s, %s (%s)\n" % (self.mesa.descripcion,
                                            self.mesa.escuela,
                                            self.mesa.municipio,
                                            self.mesa.departamento,
                                            self.mesa.codigo)
        for categoria in Categoria.many(sorted="posicion"):
            texto += "%s\n" % categoria.nombre
            for lista in Lista.many(sorted='codigo'):
                candidato = Candidato.one(cod_categoria=categoria.codigo,
                                          cod_lista=lista.codigo,
                                          titular=True,
                                          numero_de_orden=1)
                if candidato is not None:
                    votos = self._resultados[categoria.codigo,
                                             candidato.codigo]
                    texto += "\t%s - %s Votos: %s\n" % (lista.nombre,
                                                        candidato.nombre,
                                                        votos)
            texto += "\n"

        texto += "\nCampos extra:\n"
        ordered_keys = sorted(self.campos_extra.keys())
        for key in ordered_keys:
            texto += "%s: %s\n" % (key, self.campos_extra[key])

        texto += "\nListas Especiales:\n"
        ordered_keys = sorted(self.listas_especiales.keys())
        for key in ordered_keys:
            texto += "%s: %s\n" % (_("titulo_votos_%s" % key),
                                   self.listas_especiales[key])

        return texto


class Autoridad(object):

    """Presidente de mesa."""

    def __init__(self, apellido='', nombre='', tipo_documento='',
                 nro_documento=''):
        self.apellido = apellido
        self.nombre = nombre
        self.tipo_documento = TIPO_DOC[int(tipo_documento)]
        self.nro_documento = nro_documento

    def a_dict(self):
        return {"nombre": self.nombre,
                "apellido": self.apellido,
                "tipo_documento": TIPO_DOC.index(self.tipo_documento),
                "nro_documento": self.nro_documento}

    @classmethod
    def desde_dict(cls, data):
        return cls(data['apellido'], data['nombre'], data["tipo_documento"],
                   data['nro_documento'])

    def __str__(self):
        return "%s, %s" % (self.apellido, self.nombre)

    def __repr__(self):
        return "%s, %s, %s, %s" % (self.apellido, self.nombre,
                                   self.tipo_documento, self.nro_documento)


class Jerarquia(str):
    """
    Representa nodos de un árbol jerárquico y provee propiedades para realizar
    operaciones comunes.
    Es una subclase de String, así que es json serializable y todos los métodos
    de str funcionan ok.
    """

    def __init__(self, jerarquia):
        self.jerarquia = jerarquia

    @property
    def segments(self):
        return self.jerarquia.split('.')

    @property
    def root(self):
        """
        Devuelve el nodo TOP de la jerarquía
        """
        return self.segments[0]

    @property
    def last_segment(self):
        """
        Devuelve el nodo TOP de la jerarquía
        """
        return self.segments[-1]

    @property
    def len(self):
        """
        Devuelve la cantidad de labels que contiene la jerarquia
        """
        return len(self.segments)

    @property
    def parent(self):
        """
        Devuelve el nodo inmediatamente superior de la jerarquia o None
        si el es nodo superior
        """
        if self.len > 1:
            # Devolvemos el parent sólo si hay más de una label
            return Jerarquia('.'.join(self.segments[:-1]))
        else:
            return None

    def is_ancestor(self, label):
        """
        Devuelve True si label es ancestro de la jerarquia
        """
        if self.jerarquia.startswith(label):
            return True
        else:
            return False

    def is_sibling(self, otra_jerarquia):
        return self.segments[:-1] == otra_jerarquia.segments[:-1]

