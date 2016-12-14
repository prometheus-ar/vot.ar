var constants = {};

get_url = get_url_function("voto");

function load_ready_msg(){
    send('document_ready');
}

function load_mantenimiento(){
    send('load_maintenance');
}

function set_constants(data){
    constants = data;
    popular_header();
    load_patio();
    place_text(data.i18n);
    place_text(data.encabezado);
    $(".barra-titulo").show();
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
}

function change_screen(pantalla){
    func = window[pantalla[0]];
    func(pantalla[1]);
}

function apagar(){
    send('apagar');
}

function calibrar(){
    send('calibrar');
}

function salir_a_modulo(modulo){
    send("click_boton", modulo);
}
