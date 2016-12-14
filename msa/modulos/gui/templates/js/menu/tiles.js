var pantallas = [
    {
        "id": "botonera",
        "template": "botonera",
        "button_filter": ".boton-menu",
        "callback_click": click_boton,
        "context_tiles": ["titulo"]
    },
    {
        "id": "lockscreen",
        "template": "lockscreen"
    }
];

var contexto = [
    {
        "id": "titulo",
        "container": ".barra-titulo",
        "template": "titulo",
        "template_data_callback": popular_titulo,
        "callback_show": function(){
            $(".barra-titulo").show();
        },
        "callback_hide": function(){
            $(".barra-titulo").hide();
        }
    }
];
