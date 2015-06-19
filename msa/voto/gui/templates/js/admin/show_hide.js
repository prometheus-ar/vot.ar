var speed = 'fast'
var effects;

function show_elements(selector, callback){
    var elems = $(selector);
    if(effects){
        elems.fadeIn(speed, callback)
    } else {
        elems.show();
        if(callback != null) callback();
    }
}

function hide_elements(selector, callback){
    var elems = $(selector);
    if(effects){
        elems.fadeOut(speed, callback)
    } else {
        elems.hide();
        if(callback != null) callback();
    }
}

function show_pantalla_inicio(){
    show_elements("#pantalla_inicio");
}

function hide_pantalla_inicio(){
    hide_elements("#pantalla_inicio");
}

function hide_menu() {
    hide_elements("#menu");
} 

function show_pantalla_mantenimiento(){
    hide_elements("#btn_inicio");
    show_elements("#pantalla_mantenimiento");
    show_elements("#btn_volver_admin");
}

function hide_pantalla_mantenimiento(){
    hide_elements("#pantalla_mantenimiento");
    hide_elements("#btn_volver_admin");
    hide_elements("#btn_mantenimiento");
    show_elements("#btn_inicio");
    show_pantalla_inicio();
}

function show_btn_mantenimiento(){
    show_elements("#btn_mantenimiento");
}

function hide_btn_mantenimiento(){
    hide_elements("#btn_mantenimiento");
}

function show_btn_demo(){
    show_elements("#btn_demo");
}

function hide_btn_demo(){
    hide_elements("#btn_demo");
}

function show_modo_ventilador(){
    show_elements("#modo_ventilador");
}

function hide_modo_ventilador(){
    hide_elements("#modo_ventilador");
}

function show_velocidad_ventiladores(){
    show_elements("#velocidad_ventiladores");
}

function hide_velocidad_ventiladores(){
    hide_elements("#velocidad_ventiladores");
}

function show_chequeo_ventilador(){
    show_elements("#chequeo_ventilador");
}

function hide_chequeo_ventilador(){
    hide_elements("#chequeo_ventilador");
}

function show_dialogo(dialogo){
    $(".mensaje-popup p").text("");
    for(key in dialogo.mensaje){
        $(".mensaje-popup ." + key).html(dialogo.mensaje[key]);
    }
    $(".popup-box .btn").hide();
    if(dialogo.btn_cancelar){
        $(".btn-cancelar").show();
    }
    if(dialogo.btn_aceptar){
        $(".btn-aceptar").show();
    }
    show_elements(".popup-box");
}

function hide_dialogo(){
    hide_elements(".popup-box");
}

function show_boletabox(){
    $(".popboleta-box, .popboleta-box .cerrar-popup").on("click", hide_boletabox);
    show_elements(".popboleta-box");
}

function hide_boletabox(){
    $(".popboleta-box, .popboleta-box .cerrar-popup").off();
    hide_elements(".popboleta-box");
}

function show_resetbox(){
    $(".popreset-box, .popreset-box .cerrar-popup").on("click", hide_resetbox);
    show_elements(".popreset-box");
}

function hide_resetbox(){
    $(".popreset-box, .popreset-box .cerrar-popup").off();
    hide_elements(".popreset-box");
}

function show_qualitybox(){
    $(".popquality-box, .popquality-box .cerrar-popup").on("click", hide_qualitybox);
    show_elements(".popquality-box");
}

function hide_qualitybox(){
    $(".popquality-box, .popquality-box .cerrar-popup").off();
    hide_elements(".popquality-box");
}
