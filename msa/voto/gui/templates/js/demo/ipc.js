var constants = {}

get_url = get_url_function("demo")

function set_constants(data){
    constants = data;
    popular_header();
    place_text(data.i18n);
    place_text(data.encabezado);
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
}

function load_ready_msg(){
    send("document_ready");
}
