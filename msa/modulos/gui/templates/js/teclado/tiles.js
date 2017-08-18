var layouts = [
    /*
     * Contiene los diversos layouts de teclado.
     * Para cada teclado debe especificarse un id (que debe coincidir
     * con el del archivo layouts.js), el container en el que se renderiza,
     * el template de handlebar que se utiliza, el callback que se utiliza
     * para renderizar el template de handlebar, el selector de jquery
     * para las teclas y el callback que se le asocia a las mismas
     */
    {"id": "qwerty",
     "container": "#keyboard",
     "template": "qwerty",
     "template_data_callback": popular_teclado,
     "button_filter": "#qwerty .ui-keyboard-button",
     "callback_click": click_letra,
     "callback_before": sonido_teclado,
    },
    {"id": "alpha",
     "container": "#keyboard",
     "template": "qwerty",
     "template_data_callback": popular_teclado,
     "button_filter": "#alpha .ui-keyboard-button",
     "callback_click": click_letra,
     "callback_before": sonido_teclado,
    },
    {"id": "docs",
     "container": "#keyboard",
     "template": "qwerty",
     "template_data_callback": popular_teclado,
     "button_filter": "#docs .ui-keyboard-button",
     "callback_click": click_letra,
     "callback_before": sonido_teclado,
    },
    {"id": "num",
     "container": "#keyboard",
     "template": "qwerty",
     "template_data_callback": popular_teclado,
     "button_filter": "#num .ui-keyboard-button",
     "callback_click": click_letra,
     "callback_before": sonido_teclado,
    },
    {"id": "asistida",
     "container": "#keyboard-asistida",
     "template": "qwerty",
     "template_data_callback": popular_teclado,
     "button_filter": "#asistida .ui-keyboard-button",
     "callback_click": click_letra,
     "callback_before": sonar_beep,
    },
    {"id": "mensaje",
     "container": "#keyboard",
     "template": "mensaje",
    }
]

var contexto = [];

var callbacks_especiales = {
    /*
     * Diccionario de callbacks para las teclas especiales
     */
    "docs": seleccionar_documento,
    "tilde": boton_tilde,
    "asterisco": seleccionar_asterisco,
    "numeral": seleccionar_numeral,
    "espacio": boton_espacio,
    "borrar": boton_borrar,
    "anterior": seleccionar_anterior,
    "siguiente": seleccionar_siguiente, 
};
