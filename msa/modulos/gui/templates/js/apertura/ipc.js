var constants = {}

get_url = get_url_function("voto");

function load_ready_msg(){
    /* Envia el evento de document ready al backend. */
    send('document_ready');
}

function set_constants(data){
    /* Establece las constantes de la aplicacion. */
    constants = data;
    popular_header();
    place_text(data.i18n);
    place_text(data.encabezado);
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
        $("input").css("cursor", "none");
        $("label").css("cursor", "none");
    }
}

function change_screen(pantalla){
    /* Llama a la funcion de cambio de pantalla para cierta pantalla.*/
    func = window[pantalla[0]];
    func(pantalla[1]);
}
