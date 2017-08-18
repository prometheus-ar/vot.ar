from construct import Struct, Bytes, UBInt8

# estructura para construir el contenido del tag de un voto.
struct_voto = Struct(
    "voto",
    Bytes("gcm_tag", 16),
    UBInt8("len_datos"),
    Bytes("datos", lambda ctx: ctx.len_datos),
)

# estructura para construir el contenido de la credencial de autoridad de mesa.
struct_credencial = Struct(
    "credencial",
    Bytes("gcm_tag", 16),
    Bytes("salt", 16),
    Bytes("datos", 16),
    Bytes("firma", 48),
)

# estructura para construir el contenido de la credencial de tecnico.
struct_credencial_tecnico = Struct(
    "credencial",
    Bytes("gcm_tag", 16),
    Bytes("salt", 16),
    UBInt8("len_datos"),
    Bytes("datos", lambda ctx: ctx.len_datos),
    Bytes("firma", 48),
)
