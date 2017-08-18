var constants = null;

get_url = get_url_function("voto");

function set_constants(data){
    constants = data;
    popular_header();
    place_text(data.i18n);
    place_text(data.encabezado);
    $(".barra-titulo").show();
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
}

function load_ready_msg(){
    registrar_helper_i18n();
    send("document_ready");
}

function activar_impresion(nro_mesa){
    send("activar_impresion", nro_mesa);
}

function cancelar_impresion(){
    send("cancelar_impresion");
}
