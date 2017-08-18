MEDIDAS_BOLETA = {
    'ancho_boleta': 832,
    'alto_boleta': 2000,
    'alto_con_verif': 2200,
    'alto_solo_mostrar': 1930,
    'pos_verif': (150, 520),
    'verif_size': (200, 185),
    'logo': (520, 0),
    'dimensiones_logo': (87, 87),
    'titulo': (605, 40),
    'subtitulo': (605, 75),
    'tercer_titulo': (595, 70),
    'img_verificador': 'verificador_alta_flecha.png',
    'fs_water': 30,
    'fs_titulo': 35,
    'fs_subtitulo': 30,
    'pos_watermark': [(-50, 125, 35),
                      (400, 500, 35),
                      (850, 900, 35)],
    'pos_troquel': (-720, 1990, 33, -525, 2020, 28),
    'margen_izq': 70,
}

PATH_BLOQUE = "boletas/bloques/{}/bloque.tmpl"

DEFAULTS_BLOQUE = {
    "alto_fondo_titulo": 40,
    "diff_ancho_texto": 5,
    "em_adherentes": 0.7,
    "em_candidato": 1,
    "em_nom_lista": 0.85,
    "em_num_lista": 0.85,
    "em_secundarios": 0.9,
    "em_suplentes": 0.7,
    "font_size": 45,
    "font_size_titulo": 40,
    "giros_rotacion": 3,
    "mostrar_borde": True,
    "mostrar_titulo": True,
    "padding_cand_titular": 12,
    "padding_nom_lista": 35,
    "padding_num_lista": 35,
    "padding_secundarios": 24,
    "padding_suplentes": 22,
    "padding_selecciones": 90,
    "rotar_bloque": False,
    "sep_lineas_adherentes": 29,
    "sep_lineas_lista": 30,
    "sep_lineas_secundarios": 29,
    "sep_lineas_suplentes": 29,
    "sep_lineas_titular": 30,
    "nombre_template": "default",
    "wrap_adherentes": 35,
    "wrap_candidato": 22,
    "wrap_lista": 30,
    "wrap_secundarios": 27,
    "wrap_titulo": 30,
    "wrap_suplentes": 30,
}

MEDIDAS_ACTA = {
    'ancho': 832,
    'alto_recuento': 2800,
    'alto_apertura': 2800,
    'verificador': [60, 270],  # posicion del verificador en formato [x,y]
    'qr_recuento': [415, 50, 400, 400],  # x, y, w, h
    'qr_apertura': [600, 2160, 550, 550],  # x, y, w, h
    'id_planilla': [320, 70],  # posicion del id_planilla en formato [x,y]
    'escudo': [0, 0],  # posicion de escudo
    'titulo': [450, 50],  # posicion, wrap TODO: esto se usa?
    'texto': [460, 53],  # posicion, wrap
    'ancho_col': 80,
    'margen_derecho_tabla': 20,
    'inicio_tabla': 700,
    'alto_linea_filas': 23,
    'separacion_tablas': 50,
    'distancia_firmas': 200,
    'alto_panel_autoridades': 260,
    'pos_watermark': [(-320, 400, 30),
                      (-550, 700, 30),
                      (-800, 1100, 30)],
    'margin_center': "50%",
    'margin_left': 10,
    'margin_right': 810,
    'fin_encabezado': 470,
    'alto_linea_texto': 24,
    'alto_linea_tabla': 22,
    'caracteres_tabla': 53,
    'separacion_especiales': 50,
    'separacion_firmas': 60,
    'alto_firmas': 460,
}

DEFAULTS_MOSTRAR_BOLETA = {
    "verificador": True,
    "en_pantalla": False,
    "watermark": True,
    "multiplicador_fz": 0.9,
}

DEFAULTS_MOSTRAR_ACTA = {
    "verificador": True,
    "en_pantalla": False,
    "watermark": True,
    "texto": True,
}

CONFIG_BOLETA_APERTURA = {
    'tipo': 'apertura',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#ffb634',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#fef0cc',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#ffb634',
        'posicion': "matrix(1.7464477,0,0,-1.4816169,292.0272,994.4291)"
    },
    'vot_ar': {
        'fill': '#ffffff'
    },
    'legend': {
        'fill': '#ffffff'
    },
}

CONFIG_BOLETA_CIERRE = {
    'tipo': 'cierre',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#61b9e7',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#d9edf9',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#ffffff',
        'posicion': "matrix(1.7464477,0,0,-1.4816169,292.0272,994.4291)"
    },
    'vot_ar': {
        'fill': '#ffffff'
    },
    'legend': {
        'fill': '#ffffff'
    },
}

CONFIG_BOLETA_ESCRUTINIO = {
    'tipo': 'escrutinio',
    'width': 605,
    'height': 1035,
    'top_rect': {
        'x': 2,
        'y': 1,
        'width': 596,
        'height': 580,
        'fill': '#ffffff',
        'style': 'stroke:#cccccc;stroke-width:1;'
    },
    'bottom_rect': {
        'fill': '#ecf6fc',
        'style': 'stroke:#cccccc;stroke-width:1;',
        'transform': 'matrix(0.99694,0,0,0.96,4,25)',
    },
    'flecha': {
        'fill': '#61b9e7',
	'posicion': "matrix(1.7464477,0,0,-1.4816169,292.0272,994.4291)"
    },
    'vot_ar': {
        'fill': '#61b9e7'
    },
    'legend': {
        'fill': '#61b9e7'
    },
}

CONFIG_BOLETA_TRANSMISION = {
    'tipo': 'transmision',
    'width': 600,
    'height': 1020,
    'style': 'stroke:#cccccc;stroke-width:1;',
    'top_rect': {
        'x': 30,
        'y': 40,
        'width': 529,
        'height': 530,
        'fill': '#ffffff',
    },
    'bottom_rect': {
        'x': 30,
        'y': 565,
        'width': 529,
        'height': 425,
        'fill': '#ecf6fc',
    },
    'flecha': {
        'fill': '#ffb634',
	'posicion': "matrix(1.7464477,0,0,-1.4816169,292.0272,964.4291)"
    },
    'vot_ar': {
        'fill': '#ffb634'
    },
    'legend': {
        'fill': '#ffb634'
    },
}

COLORES = {
    "blanco": "#ffffff",
    "negro": "#000000"
}

# constantes QR
QR_PIXEL_SIZE = 10
QR_ERROR_LEVEL = 'Q'
