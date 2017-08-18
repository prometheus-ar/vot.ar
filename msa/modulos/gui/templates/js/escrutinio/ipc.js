var constants = {};

get_url = get_url_function("voto");

function load_ready_msg(){
    send('document_ready');
}

function set_constants(data){
    /*
     * Establece las constantes, inicializa la internacionalizacion, carga,
     * patio, muestra el loader y manda a cargar el cache.
     */
    constants = data;
    popular_html();
    load_templates_escrutinio();
    load_patio();
    place_text(data.i18n);
    place_text(data.encabezado);
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
    pantalla_loader();
    setTimeout(function(){send("cargar_cache");}, 300);
}

function sonido_tecla(){
    send("sonido_tecla");
}

function load_templates_escrutinio(){
    if(constants.templates_compiladas){
        var url = constants.PATH_TEMPLATES_VAR + "escrutinio.html";
        load_template_comp(url);
        cargar_templates_en_dom()
    }
}
