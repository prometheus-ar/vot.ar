var keyboard_layouts = (function() {
    /*
     * Diccionario de layouts de teclado.
     * La clave debe coincidir con su id en el tile de Patio
     * Cada array se corresponde con una linea de teclado,
     * siendo las teclas en llaves consideradas especiales
     *
     * Se puede designar el contenido del campo separandolo con un pipe,
     * No hay soporte para que la primer porcion de un campo especial sea vacio
     */
    var layouts = {
        "qwerty": [
            ['1 2 3 4 5 6 7 8 9 0'],
            ['Q W E R T Y U I O P'],
            ['A S D F G H J K L Ñ'],
            ['Z X C V B N M {tilde|\'} {Borrar}'],
            ['{Espacio} {Anterior} {Siguiente}' ],
        ],
        "alpha": [
            [],
            ['Q W E R T Y U I O P'],
            ['A S D F G H J K L Ñ'],
            ['Z X C V B N M {tilde|\'} {Borrar}'],
            ['{Espacio} {Anterior} {Siguiente}' ],
        ],
        "docs": [
            [],
            ['{docs|DNI}'],
            ['{docs|LE}'],
            ['{docs|LC}'],
            ['{Anterior} {Siguiente}'],
        ],
        "num": [
            ['1 2 3'],
            ['4 5 6'],
            ['7 8 9'],
            ['0 {Borrar}'],
            ['{Anterior} {Siguiente}'],
        ],
        "asistida": [
            ['1 2 3'],
            ['4 5 6'],
            ['7 8 9'],
            ['{asterisco|⁎} 0 {numeral|#}']
        ]
    };

    return layouts;
}());
