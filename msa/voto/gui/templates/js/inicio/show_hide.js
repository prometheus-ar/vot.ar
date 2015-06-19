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

function show_dialogo(dialogo){
    $(".mensaje-popup p").text("");
    for(key in dialogo.mensaje){
        $(".mensaje-popup ." + key).text(dialogo.mensaje[key]);
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