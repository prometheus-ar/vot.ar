var pantallas = [
  {"id": "loading",
   "template": "loading"
  },
  {"id": "insercion_boleta",
   "template": "insercion_boleta",
   "context_tiles": ["barra_opciones", "alto_contraste"]
  },
  {"id": "pantalla_modos",
   "template": "pantalla_modos",
   "context_tiles": ["barra_opciones", "alto_contraste"],
   "callback_click": click_modo,
   "button_filter": ".opcion-tipo-voto",
   "template_data_callback": popular_pantalla_modos
  },
  {"id": "pantalla_candidatos",
   "template": "candidatos",
   "context_tiles": ["barra_opciones", "contenedor_der",
                     "alto_contraste", "btn_regresar", "categoria_votada"]
  },
  {"id": "pantalla_listas",
   "template": "contenedor_listas",
   "context_tiles": ["barra_opciones", "alto_contraste", "btn_regresar"]
  },
  {"id": "pantalla_confirmacion",
   "template": "confirmacion",
   "context_tiles": ["si_confirmar_voto", "no_confirmar_voto", "barra_opciones", "alto_contraste"]
  },
  {"id": "pantalla_consulta",
   "template": "consulta_seleccion"
  },
  {"id": "pantalla_agradecimiento",
   "template": "agradecimiento"
  },
  {"id": "pantalla_mensaje_final",
   "template": "mensaje_final"
  },
  {"id": "consulta_popular_container",
   "template": "consulta_popular",
   "context_tiles": ["barra_opciones", "alto_contraste", "categoria_votada"]
  },
  {"id": "asistida_container",
   "template": "asistida",
   "context_tiles": ["indicador_asistida"]
  },
  {"id": "pantalla_partidos_categoria",
   "context_tiles": ["barra_opciones", "voto_blanco",
                     "alto_contraste", "categoria_votada", "btn_regresar"]
  },
  {"id": "pantalla_partidos_completa",
   "context_tiles": ["barra_opciones", "voto_blanco",
                     "alto_contraste", "btn_regresar"]
  },
  {"id": "pantalla_idiomas",
   "template": "idiomas",
   "context_tiles": ["barra_opciones", "alto_contraste"]
  },
  {"id": "pantalla_menu",
   "template": "menu",
   "context_tiles": ["barra_opciones", "btn_regresar"],
   "button_filter": ".opcion-salida",
   "callback_click": click_salir,
   "template_data_callback": popular_pantalla_menu
  },
];

var contexto = [
  {"id": "voto_blanco",
   "container": "#contenedor_opciones",
   "template": "voto_blanco"
  },
  {"id": "agrupaciones_municipales",
   "container": "#contenedor_opciones",
   "template": "btn_agrupaciones_municipales"
  },
  {"id": "confirmar_seleccion",
   "container": "#contenedor_opciones",
   "template": "confirmar_seleccion",
   "button_filter": "#confirmar_seleccion",
   "callback_click": click_confirmar_seleccion
  },
  {"id": "barra_opciones",
   "container": "#contenedor_opciones",
   "template": "barra_opciones"
  },
  {"id": "contenedor_der",
   "container": "#contenedor",
   "template": "candidatos_seleccionados",
   "insert_before": true
  },
  {"id": "categoria_votada",
   "container": "#contenedor_solapa",
   "callback_show": function(){
     $('#encabezado').addClass("con-categoria-votada");
   },
   "callback_hide": function(){
     $('#encabezado').removeClass("con-categoria-votada");
   },
  },
  {"id": "alto_contraste",
   "container": "#accesibilidad",
   "template": "alto_contraste",
   "button_filter": "#alto_contraste",
   "callback_click": click_alto_contraste
  },
  {"id": "btn_regresar",
   "container": "#accesibilidad",
   "template": "btn_regresar"
  },
  {"id": "indicador_asistida",
   "container": "#asistida_container"
  },
];
 
var confirmacion_barra_horizontal = [
  {"id": "si_confirmar_voto",
   "container": "#contenedor_opciones",
   "template": "si_confirmar_voto",
   "button_filter": "#si_confirmar_voto",
   "callback_click": click_si
  },
  {"id": "no_confirmar_voto",
   "template": "no_confirmar_voto",
   "button_filter": "#no_confirmar_voto",
   "container": "#contenedor_opciones",
   "callback_click": click_no
  }
];

var confirmacion_barra_vertical = [
  {"id": "no_confirmar_voto",
   "template": "no_confirmar_voto",
   "button_filter": "#no_confirmar_voto",
   "container": "#contenedor_izq",
   "callback_click": click_no
  },
  {"id": "si_confirmar_voto",
   "template": "si_confirmar_voto",
   "button_filter": "#si_confirmar_voto",
   "container": "#contenedor_izq",
   "callback_click": click_si
  }
];
