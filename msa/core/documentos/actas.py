from struct import pack as struct_pack

from base64 import b64encode
from codecs import encode
from io import BytesIO

import six

from construct import Container
from msa.constants import CAM_BOL_CONT, CAM_TOT_VOT
from msa.core.config_manager import Config
from msa.core.data import Ubicacion
from msa.core.data.candidaturas import Candidatura, Categoria, Lista
from msa.core.data.constants import TIPO_DOC
from msa.core.data.helpers import get_config
from msa.core.documentos.autoridades import Autoridad
from msa.core.documentos.constants import (BITS_DNI, CIERRE_CERTIFICADO,
                                           CIERRE_COPIA_FIEL,
                                           CIERRE_ESCRUTINIO, CIERRE_RECUENTO,
                                           CIERRE_TRANSMISION)
from msa.core.documentos.helpers import (decodear_string_apertura,
                                         encodear_string_apertura)
from msa.core.documentos.settings import GUARDAR_DNI
from msa.core.documentos.structs import (struct_apertura, struct_recuento,
                                         struct_recuento_dni)
from msa.core.documentos.tabulacion import Pizarra
from msa.core.exceptions import (MesaNoEncontrada, QRMalformado,
                                 SerialRepetido, TagMalformado, TipoQrErroneo)
from msa.core.i18n.decorators import forzar_idioma
from msa.core.i18n.settings import DEFAULT_LOCALE
from msa.core.imaging.acta import ImagenActa
from msa.core.imaging.qr import crear_qr
from msa.core.logging import get_logger
from msa.core.packing.settings import SMART_PACKING
from msa.core.rfid.constants import TAG_RECUENTO, TAG_NO_ENTRA
from msa.core.settings import TOKEN
from six.moves import range, zip

logger = get_logger("core_documentos_actas")


from msa.core.packing import smart_numpacker
from msa.core.packing import numpacker

from msa.core.packing.numpacker import pack_slow, unpack_slow


class Acta():

    clase_acta = "ACTA"                     # prefijo para QR y serialización

    def _encode_qr(self, qr):
        output = BytesIO()
        qr.save(output, format='PNG')
        qr_img_data = output.getvalue()
        output.close()
        header = 'data:image/png;base64,'
        qr_data = header + b64encode(qr_img_data).decode()
        return qr_data


class Apertura(Acta):

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
        container = Container(numero_mesa=int(self.mesa.id_unico_mesa),
                              hora=int(self.hora["horas"]),
                              minutos=int(self.hora["minutos"]),
                              cantidad_autoridades=len(self.autoridades),
                              len_nombres=len(nombres),
                              nombres=nombres,
                              tipos=tipos,
                              dnis=dnis,
                              len_docs=len(dnis)
                              )
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
            tipos.append(tipo.encode())
            dnis.append(int(autoridad.nro_documento))

        nombres = encodear_string_apertura(";".join(nombres))
        dnis = pack_slow(dnis, BITS_DNI)
        return nombres, dnis, tipos

    @classmethod
    def desde_tag(cls, tag):
        """Devuelve un apertura a partir de la informacion de un tag rfid."""
        # parseamos los datos del tag.
        datos = struct_apertura.parse(tag)
        # instanciamos una mesa
        mesa = Ubicacion.first(id_unico_mesa=str(datos.numero_mesa))
        # extraemos los nombres y DNIs
        nombres = decodear_string_apertura(datos.nombres).split(";")
        dnis = unpack_slow(datos.dnis, BITS_DNI)
        # y armamos las autoridades
        autoridades = []
        for i in range(datos.cantidad_autoridades):
            apellido = nombres.pop(0)
            nombre = nombres.pop(0)
            tipo = datos.tipos.pop(0)
            dni = dnis.pop(0)
            autoridad = Autoridad(apellido, nombre, tipo, dni)
            autoridades.append(autoridad)
        # armamos el diccionario de la hora
        hora = {
            "horas": datos.hora,
            "minutos": datos.minutos
        }
        # y finalmente instanciamos la Apertura que vamos a devolver
        apertura = Apertura(mesa, autoridades, hora)
        return apertura

    @forzar_idioma(DEFAULT_LOCALE)
    def a_imagen(self, mostrar=None, svg=False):
        """Devuelve la imagen para imprimir el apertura."""
        if mostrar is None:
            mostrar = {
                "en_pantalla": False
            }
        mostrar["texto"] = mostrar.get("texto", True)

        datos = {
            'titulo': _("titulo_apertura"),
            'leyenda': None,
            "mesa": self.mesa,
            "autoridades": self.autoridades,
            "hora": self.hora
        }
        config = Config(["imaging"], self.mesa.cod_datos)
        usar_qr = config.val("usar_qr")
        qr_img = (self.a_qr_b64_encoded()
                  if usar_qr and not mostrar["en_pantalla"]
                  else None)
        imagen = ImagenActa(datos, mostrar, qr=qr_img)
        rendered = imagen.render(svg)
        return rendered

    def a_qr_str(self):
        """Devuelve la informacion del recuento para almacenar en qr."""
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
        qr_data = None
        qr = self.a_qr()
        if qr is not None:
            qr_data = self._encode_qr(qr)
        return qr_data

    def __str__(self):
        return 'Apertura de ' + self.mesa.descripcion


class Recuento(Acta):

    """Recuento de votos de una mesa."""

    # usar la configuración predeterminada para empaquetamiento de numeros:
    smart_packing = SMART_PACKING
    clase_acta = "REC "                     # prefijo para QR y serialización
    tipo_tag = TAG_RECUENTO                 # código para identificar el tag

    def __init__(self, mesa, autoridades=None, hora=None):
        if autoridades is None:
            autoridades = []

        self.autoridades = autoridades
        self.mesa = mesa
        self.grupo_cat = None

        self.hora = hora  # si hora es None no se muestra el texto del acta
        _campos_extra = get_config("campos_extra")
        self.campos_extra = dict(list(zip(_campos_extra,
                                          [0] * len(_campos_extra))))
        _lst_esp = self.mesa.listas_especiales
        if _lst_esp is not None:
            dict_esp = dict(list(zip(_lst_esp, [0] * len(_lst_esp))))
        else:
            dict_esp = {}
        self.listas_especiales = dict_esp

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
        if seleccion is not None:
            if serial is None or not self.serial_sumado(serial):
                self.pizarra.sumar_seleccion(seleccion)
                if serial is not None:
                    self._serials.append(serial)
                self.campos_extra[CAM_BOL_CONT] += 1
                self.campos_extra[CAM_TOT_VOT] += 1
            else:
                raise SerialRepetido()
        else:
            raise ValueError("La seleccion es Invalida")

    def boletas_contadas(self):
        """Obtiene la cantidad de selecciones contadas."""
        return self.campos_extra[CAM_BOL_CONT]

    def total_boletas(self):
        return self.campos_extra[CAM_TOT_VOT]

    def reiniciar_resultados(self):
        """Reinicia los resultados del recuento."""
        self.pizarra = Pizarra()

        self._serials = []
        self.campos_extra[CAM_BOL_CONT] = 0
        self.campos_extra[CAM_TOT_VOT] = 0

    def get_resultados(self, id_umv=None):
        """Devuelve todos los resultados o uno en especifico."""
        # si le pedimos uno solo busca los votos de ese candidato.
        if id_umv is not None:
            ret = self.pizarra.votos_candidato(id_umv)
        else:
            # Sino devolvemos todos
            votos = self.pizarra.get_votos_actuales()
            # Si el acta está desglosada devolvemos la categorias que tiene el
            # acta guardada
            if self.grupo_cat is not None:
                categorias_grupo = Categoria.many(id_grupo=self.grupo_cat)
                cods_categoria = [cat.codigo for cat in categorias_grupo]
                ret = {}
                for key in votos.keys():
                    cand = Candidatura.one(id_umv=key,
                                           cod_categoria__in=cods_categoria)
                    if cand is not None:
                        ret[key] = votos[key]
            else:
                # no esta desglosada devolvemos todos los votos.
                ret = votos
        return ret

    def a_tag(self, grupo_cat=None, con_dnis=GUARDAR_DNI):
        """Devuelve la informacion del recuento para almacenar en tag rfid."""
        valores = []

        candidatos = Candidatura.para_recuento(grupo_cat)
        for candidato in candidatos:
            resultado = self.get_resultados(candidato.id_umv)
            valores.append(resultado)

        ordered_keys = sorted(self.campos_extra.keys())
        for key in ordered_keys:
            valores.append(self.campos_extra[key])

        ordered_keys = sorted(self.listas_especiales.keys())
        for key in ordered_keys:
            valores.append(self.listas_especiales[key])

        container = Container()

        # cod_mesa
        if self.smart_packing:
            num_mesa = self.mesa.id_unico_mesa.encode('ascii')
            datos = smart_numpacker.pack(int(num_mesa), valores)
            container.datos = datos
        else:
            cod_mesa = self.mesa.codigo.encode('ascii')
            packed = numpacker.pack(valores)
            datos = str(len(cod_mesa)).zfill(2).encode() + cod_mesa + packed

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

            documentos = pack_slow(documentos, BITS_DNI)
            container.len_docs = len(documentos)
            container.documentos = documentos

            struct = struct_recuento_dni
        else:
            struct = struct_recuento

        container.grupo = int(grupo_cat) if grupo_cat is not None else 0

        return struct.build(container)

    def a_qr_str(self, grupo_cat=None, con_dnis=True):
        """Devuelve la informacion del recuento para almacenar en qr."""
        encoded_data = self.a_tag(grupo_cat, con_dnis)
        datos = bytearray(b"")
        # Agregamos el Token
        datos.append(int(TOKEN, 16))
        # agregamos el largo de los datos en 2 bytes
        len_data = len(encoded_data) * 2
        datos.extend(struct_pack(">H", len_data))
        # metemos el resto de los datos
        datos.extend(encoded_data)
        # lo encodeamos en hexa y lo pasamos a mayúsculas
        todo = encode(datos, "hex_codec").decode().upper()
        return todo

    def a_qr(self, grupo_cat=None, con_dnis=True):
        datos = self.clase_acta + self.a_qr_str(grupo_cat, con_dnis)
        return crear_qr(datos)

    def a_qr_b64_encoded(self, grupo_cat=None):
        qr_data = None
        qr = self.a_qr(grupo_cat)
        if qr is not None:
            qr_data = self._encode_qr(qr)
        return qr_data

    def generar_titulo(self, tipo):
        # Por defecto no tenemos titulo, a menos que el tipo de acta tenga
        # titulo.
        titulo = ""
        leyenda = None
        # Muestra el icono del verificador en la boleta. Si no tiene chip en el
        # documento en el que imprimimos no imprimirmos el verificador.
        verif = True

        # Internamente todas las actas son iguales, lo que cambia es el texto
        # que se imprime, pero el acta una vez serializada no sabe cual es.
        if tipo == CIERRE_RECUENTO:
            # El acta de cierre.
            titulo = _("titulo_recuento")
            leyenda = _("no_insertar_en_urna")
        elif tipo == CIERRE_TRANSMISION:
            # El acta de transmision.
            titulo = _("titulo_transmision")
            leyenda = _("no_insertar_en_urna")
        elif tipo in (CIERRE_CERTIFICADO, CIERRE_ESCRUTINIO):
            # El certificado de escrutinio.
            titulo = _("titulo_certificado")
            verif = False
        elif tipo == CIERRE_COPIA_FIEL:
            # Una copia fiel del certificado. (Certificado sin datos desc_mesa
            # autoridades)
            titulo = _("titulo_copia_fiel")
            verif = False

        return titulo, leyenda, verif


    @forzar_idioma(DEFAULT_LOCALE)
    def a_imagen(self, mostrar=None, tipo=None, svg=False):
        """Devuelve la imagen para imprimir recuento.

        Argumentos:
        tipo -- una tupla con el tipo de acta y el id_de grupo de categorias.
            Puede ser None si no no queremos agrupar.
        mostrar -- un diccionario con las cosas a mostrar.
        svg -- Devuelve un svg si True, en caso contrario un objeto PIL.Image
        """
        if mostrar is None:
            mostrar = {
                "en_pantalla": False
            }

        if tipo is None:
            tipo = (CIERRE_RECUENTO, None)

        titulo, leyenda, verif = self.generar_titulo(tipo[0])
        grupo_cat = tipo[1]

        mesa = self.mesa
        # Armamos los datos para el texto.
        datos = {
            'titulo': titulo,
            "autoridades": self.autoridades,
            'mesa': mesa,
            'hora': self.hora,
            'leyenda': leyenda,
            "cod_datos": self.mesa.cod_datos,
        }

        if self.hora is not None:
            datos["horas"] = "%02d" % self.hora.get('horas', "")
            datos["minutos"] = "%02d" % self.hora.get('minutos', "")
            mostrar["texto"] = True
        else:
            datos["horas"] = ""
            datos["minutos"] = ""
            mostrar["texto"] = False

        config = Config(["imaging"], mesa.cod_datos)
        usar_qr = config.val("usar_qr")
        # Generamos el QR que va a ir en el acta.
        qr_img = self.a_qr_b64_encoded(grupo_cat) if usar_qr else None

        mostrar["verificador"] = verif

        # Y armamos la imagen.
        imagen = ImagenActa(datos, mostrar, qr=qr_img, recuento=self,
                            grupo_cat=grupo_cat)

        rendered = imagen.render(svg)

        # Devolvemos la imagen en el formato solicitado.
        return rendered

    def __str__(self):
        """Representacion como string del acta."""
        return 'Recuento de la mesa %s' % self.mesa

    @classmethod
    def desde_tag(cls, tag, con_dnis=GUARDAR_DNI):
        # Si vamos a guardar los dnis usamos el struct con DNIS, sino no.
        if con_dnis:
            struct = struct_recuento_dni
        else:
            struct = struct_recuento
        # Parseamos el tag
        datos_tag = struct.parse(tag)
        # Nos fijamos si el tag tiene la data de una categoria o solo de una
        if cls.smart_packing:
            try:
                string_datos = b""
                for byte in datos_tag.datos:
                    string_datos += byte
                num_mesa, valores = smart_numpacker.unpack(string_datos)
            except IndexError as e:
                raise TagMalformado(e)
            mesa = Ubicacion.first(id_unico_mesa=str(num_mesa))
        else:
            tag = b""
            for byte in datos_tag.datos:
                tag += byte
            len_cod_mesa = int(tag[:2])
            cod_mesa = tag[2:2 + len_cod_mesa]
            mesa = Ubicacion.first(codigo=cod_mesa.decode("utf8"))
            valores = numpacker.unpack(tag[len_cod_mesa + 2:])

        if not mesa:
            raise MesaNoEncontrada()
        mesa.usar_cod_datos()
        recuento = cls(mesa)
        grupo = datos_tag.grupo
        # Establecemos el grupo del recuento, si viene en 0 lo establecemos en
        # None
        recuento.grupo_cat = grupo if grupo else None

        # Traemos las candidaturas que se guardaron en el recuento
        candidatos = Candidatura.para_recuento(recuento.grupo_cat)
        # leemos los valores y los seteamos en los resultados
        for candidato in candidatos:
            recuento.pizarra.set_votos_candidato(candidato.id_umv,
                                                 valores.pop(0))

        # extraemos los campos extras (boletas_contadas, total_boletas, etc)
        ordered_keys = sorted(recuento.campos_extra.keys())
        for key in ordered_keys:
            recuento.campos_extra[key] = valores.pop(0)

        # extraemos las listas especiales (OBS, IMP, NUL, REC, etc)
        ordered_keys = sorted(recuento.listas_especiales.keys())
        for key in ordered_keys:
            recuento.listas_especiales[key] = valores.pop(0)

        # si estan los DNIS los extraemos del tag
        if con_dnis:
            dnis = unpack_slow(datos_tag.documentos, BITS_DNI)
            for dni in dnis:
                autoridad = Autoridad("", "", 0, dni)
                recuento.autoridades.append(autoridad)

        return recuento

    @classmethod
    def desde_qr(cls, datos):
        """Devuelve un recuento a partir de la informacion de un qr."""
        # tipo de qr
        if datos.startswith(cls.clase_acta):
            datos = datos[4:]

        token = datos[0:2]
        if token != TOKEN:
            raise TipoQrErroneo()

        len_datos = int(datos[2:6], 16)
        datos_recuento = datos[6:]
        if len_datos != len(datos_recuento):
            raise QRMalformado()

        bytes_recuento = bytearray(b'')
        for i in range(0, len_datos, 2):
            bytes_recuento.append(int(datos_recuento[i:i+2], 16))

        recuento = cls.desde_tag(bytes_recuento, con_dnis=True)

        return recuento

    @classmethod
    def desde_dict(cls, id_planilla, hora, data_dict, campos_extra):
        """Genera un recuento desde un diccionario con los datos.
           Argumentos:
            id_planilla -- el id_planilla del acta que queremos generar.
            hora -- un diccionario con la hora {"horas": int, "minutos": int}
            data_dict -- un diccionario con los datos. De key el id_ubicacion y
                de value la cantidad de votos.
            listas_especiales -- un diccionaio con las listas_especiales
                de key el id_de lista especial y de value un diccionario que a
                su vez tiene de key el codigo de categoria y la cantidad de
                votos especiales como valor.
            campos_extra -- un diccionario con los campos_extra como key y el
                valor numerico del campo extra como valor.
        """
        mesa = Ubicacion.one(id_planilla=id_planilla)
        mesa.usar_cod_datos()
        recuento = cls(mesa, hora=hora)
        for key, value in data_dict.items():
            recuento.pizarra.set_votos_candidato(key, value)
        recuento.campos_extra = campos_extra
        return recuento

    def a_human(self):
        texto = "{} - {}, {}, {} ({})\n".format(self.mesa.descripcion,
                                                self.mesa.escuela,
                                                self.mesa.municipio,
                                                self.mesa.departamento,
                                                self.mesa.codigo)
        for autoridad in self.autoridades:
            texto += "Autoridad: {}\n".format(autoridad.nro_documento)

        grupo = int(self.grupo_cat) if self.grupo_cat is not None else 1
        for categoria in Categoria.many(sorted="posicion",
                                        id_grupo=grupo):
            texto += "{}\n".format(categoria.nombre)
            for lista in Lista.many(sorted='codigo'):
                candidato = Candidatura.one(cod_categoria=categoria.codigo,
                                            cod_lista=lista.codigo)
                if candidato is not None:
                    votos = self.get_resultados(candidato.id_umv)
                    texto += "\t{} - {} Votos: {}\n".format(lista.nombre,
                                                            candidato.nombre,
                                                            votos)
            candidato = Candidatura.one(cod_categoria=categoria.codigo,
                                        clase="Blanco")
            if candidato is not None:
                votos = self.get_resultados(candidato.id_umv)
                texto += "\t{}: {}\n".format(_("votos_en_blanco"), votos)
            texto += "\n"

        texto += "\nCampos extra:\n"
        ordered_keys = sorted(self.campos_extra.keys())
        for key in ordered_keys:
            texto += "{}: {}\n".format(key, self.campos_extra[key])

        texto += "\nListas Especiales:\n"
        ordered_keys = sorted(self.listas_especiales.keys())
        for key in ordered_keys:
            titulo = _("titulo_votos_{}".format(key))
            texto += "{}: {}\n".format(titulo, self.listas_especiales[key])

        return texto


class Totalizacion(Recuento):

    """Suma de recuentos de votos de varias mesa."""

    # usar siempre num_packer para empaquetamiento de numeros grandes:
    smart_packing = False
    clase_acta = "TOT "                     # prefijo para QR y serialización
    tipo_tag = TAG_NO_ENTRA                 # código para diferenciar el tag

    def __init__(self, mesa, autoridades=None, hora=None):
        super().__init__(mesa, autoridades, hora)

    def sumar_recuento(self, recuento, serial):
        if not serial or not self.serial_sumado(serial):
            resultados = recuento.get_resultados()

            for key, votos in resultados.items():
                actual = self.get_resultados(key)
                self.pizarra.set_votos_candidato(key, actual + votos)

            for key, votos in six.iteritems(recuento.campos_extra):
                actual = self.campos_extra.get(key, 0)
                self.campos_extra[key] = actual + votos

            for key, votos in six.iteritems(recuento.listas_especiales):
                actual = self.listas_especiales.get(key, 0)
                self.listas_especiales[key] = actual + votos

            if serial:
                self._serials.append(serial)
        else:
            raise SerialRepetido()

    def generar_titulo(self, tipo):
        titulo = _("titulo_totalizacion")
        leyenda = None
        verif = True
        return titulo, leyenda, verif
