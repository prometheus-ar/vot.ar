from construct import GreedyRange, Bytes, Struct, UBInt8, UBInt16, Array, \
    Embed, If

from msa.core import get_config

len_cods = get_config("len_cod")
if len_cods is None:
    len_cods = {}

struct_voto = Struct("voto",
                     Bytes("len_ubic", 2),
                     Bytes("ubicacion", lambda ctx: int(ctx.len_ubic)),
                     Bytes("cod_interna", len_cods.get('interna')),
                     GreedyRange(
                         Struct("voto_categoria",
                                Bytes("cod_categoria",
                                      len_cods.get('categoria')),
                                Bytes("cod_candidatura",
                                      len_cods.get('candidato')))
                     ))

struct_recuento = Struct("Recuento",
                         Bytes("por_categoria", 1),
                         If(lambda ctx: ctx.por_categoria == "1",
                            Bytes("cod_categoria", len_cods.get('categoria'))),
                         GreedyRange(Bytes("datos", 1))
                         )
struct_recuento_dni = Struct("Recuento con dni",
                             Array(7, Bytes("documentos", 1)),
                             Embed(struct_recuento),
                             )

struct_apertura = Struct("Apertura",
                         UBInt16("numero_mesa"),
                         UBInt8("hora"),
                         UBInt8("minutos"),
                         UBInt8("cantidad_autoridades"),
                         UBInt8("len_nombres"),
                         Array(lambda ctx: ctx.len_nombres,
                               Bytes("nombres", 1)),
                         Array(lambda ctx: ctx.cantidad_autoridades,
                               Bytes("tipos", 1)),
                         Array(lambda ctx: ctx.cantidad_autoridades,
                               Bytes("dnis", 4)),
                         )
