# -*- coding: utf-8 -*-

RESOLUCION_BAJA = 0
RESOLUCION_ALTA = 2

medidas_alta = {
    'ancho_boleta': 832,
    'alto_boleta': 2000,
    'alto_con_verif': 2200,
    'alto_solo_mostrar': 1930,

    'pos_verif': (260, 540),

    'verif_size': (200, 185),

    'logo': (530, 0),
    'dimensiones_logo': (60, 65),

    'titulo': (595, 35),
    'subtitulo': (595, 70),
    'tercer_titulo': (595, 70),
    'img_verificador': 'verificador_alta.png',

    'default_tfz': 26,
    'fs_water': 30,
    'fs_titulo': 35,
    'fs_subtitulo': 30,
    'fs_numero_lista': 40,

    'pos_watermark': (300, 350, 40),
    'pos_troquel': (-680, 1990, 40, -525, 2020, 30),

    'ancho_linea': 1, # tamaño de las lineas separadoras

    'margen_izq': 70,

    'alto_fondo_titulo': 40, # alto del cuadrado negro de fondo
    'padding_txt_lista': 22, # separacion entre el tope del bloque y la palabra lista
    'padding_num_lista': 40, # separacion enter la palabra_lista y el numero
    'padding_nom_lista': 125, # separacion entre el tope del bloque y el nombre del la lista
    'sep_lineas_lista': 30, # alto de las lineas del nombre de la lista
    'padding_cand_titular': 10,
    'sep_lineas_titular': 25, # alto de las lineas del nombre de la lista
    'padding_secundarios': 20, # separacion entre el titular y los secunadarios
    'padding_selecciones': 90, # margen superior desde el borde de la boleta hasta el primer bloque
    'fs_secundarios': 3, # cantidad de numeros menos de fuente que tiene el secundario que el principal
    'sep_lineas_secundarios': 25, # alto de las lineas del nombre de la lista
}

medidas_baja = {
    'ancho_boleta': 400,
    'alto_boleta': 890,
    'alto_con_verif': 890,

    'pos_verif': (65, 245),
    'verif_size': (100, 100),

    'logo': (160, 0),
    'dimensiones_logo': (47, 52),

    'titulo': (200, 20),
    'subtitulo': (200, 33),
    'img_verificador': 'verificador_baja.png',

    'default_tfz': 11,
    'fs_water': 25,
    'fs_titulo': 13,
    'fs_subtitulo': 12,
    'fs_numero_lista': 25,

    'pos_watermark': (200, -100, 20),
    'pos_troquel': (-225, 600, 16, -180, 615, 15),

    'ancho_linea': 2,

    'margen_izq': 30,

    'alto_fondo_titulo': 20, # alto del cuadrado negro de fondo
    'padding_txt_lista': 10, # separacion entre el tope del bloque y la palabra lista
    'padding_num_lista': 22, # separacion enter la palabra_lista y el numero
    'padding_nom_lista': 55, # separacion entre el tope del bloque y el nombre del la lista
    'sep_lineas_lista': 12, # alto de las lineas del nombre de la lista
    'padding_cand_titular': 6,
    'sep_lineas_titular': 15, # alto de las lineas del nombre de la lista
    'padding_secundarios': 5, # separacion entre el titular y los secunadarios
    'padding_selecciones': 50, # margen superior desde el borde de la boleta hasta el primer bloque
    'fs_secundarios': 3, # cantidad de numeros menos de fuente que tiene el secundario que el principal
    'sep_lineas_secundarios': 10, # alto de las lineas del nombre de la lista
}

MEDIDAS_BOLETA = {
    RESOLUCION_ALTA: medidas_alta,
    RESOLUCION_BAJA: medidas_baja
}
