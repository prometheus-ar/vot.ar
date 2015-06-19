var constants = {};

get_url = get_url_function("recuento");

function load_ready_msg(){
    send('document_ready');
}

function set_constants(data){
    constants = data;
    popular_html();
    place_text(data.i18n);
    place_text(data.encabezado);
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
    effects = constants.effects;
}

function change_screen(pantalla){
    func = eval(pantalla[0]);
    func(pantalla[1]);
}

function administrador(){
    send('administrador');
}

function salir(){
    send('salir');
}

function volver(){
    send('volver');
}

function terminar_escrutinio(){
    send('terminar_escrutinio');
}

function imprimir(){
    hide_botones();
    hide_scroll_acta();
    hide_btn_qr();
    send('imprimir');
}

function copiar_certificados(){
    send('copiar_certificados');
}

function procesar_dialogo(respuesta){
    send('dialogo', respuesta);
}

function set_campos_extra(campos_recuento){
    send('set_campos_extra', campos_recuento);
}
