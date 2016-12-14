from construct import (Array, Bytes, Embed, GreedyRange, If, Struct, UBInt8,
                       UBInt16)
from msa.core.data.constants import LEN_COD_CATEGORIA
from msa.core.documentos.constants import LEN_LEN_OPC, LEN_LEN_UBIC, LEN_SERIAL


struct_voto = Struct(
    "voto",
    Bytes("len_ubic", LEN_LEN_UBIC),
    Bytes("ubicacion", lambda ctx: int(ctx.len_ubic)),
    Bytes("len_opciones", LEN_LEN_OPC),
    Bytes("opciones", lambda ctx: int(ctx.len_opciones)),
    Bytes("serial", LEN_SERIAL)
)

struct_recuento = Struct(
    "Recuento",
    UBInt8("grupo"),
    GreedyRange(Bytes("datos", 1))
)

struct_recuento_dni = Struct(
    "Recuento con dni",
    UBInt8("len_docs"),
    Bytes("documentos", lambda ctx: ctx.len_docs),
    Embed(struct_recuento),
)

struct_apertura = Struct(
    "Apertura",
    UBInt16("numero_mesa"), UBInt8("hora"), UBInt8("minutos"),
    UBInt8("cantidad_autoridades"), UBInt8("len_nombres"),
    Array(lambda ctx: ctx.len_nombres, Bytes("nombres", 1)),
    Array(lambda ctx: ctx.cantidad_autoridades, Bytes("tipos", 1)),
    UBInt8("len_docs"),
    Bytes("dnis", lambda ctx: ctx.len_docs),
)
