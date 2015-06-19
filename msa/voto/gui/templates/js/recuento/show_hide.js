var speed = 'fast';
var effects;

function show_elements(selector, callback){
    var elems = $(selector);
    if(effects){
        elems.fadeIn(speed, callback);
    } else {
        elems.show();
        if(callback !== null && callback !== undefined) callback();
    }
}

function hide_elements(selector, callback){
    var elems = $(selector);
    if(effects){
        elems.fadeOut(speed, callback);
    } else {
        elems.hide();
        if(callback !== null && callback !== undefined) callback();
    }
}

function toggle_vista(){
    //TODO: Ver si es posible ampliar la tabla aun cuando esté el instructivo
    var elem = $("body");
    if(puede_cambiar_vista && $("#instructivo").is(":hidden")){
        if(elem.attr('data-vista') == 'vista-boleta') {
            elem.attr('data-vista', 'vista-tabla');
            $("#boleta").hide();
        } else {
            elem.attr('data-vista', 'vista-boleta');
            $("#boleta").show();
        }
    }
}

function agrandar_tabla_recuento(fast, callback){
    if(effects && !fast){
        $(".tabla-scrolleable").animate({"height": scroll_tabla_original_height}, 500, callback);
    } else {
        $(".tabla-scrolleable").height(scroll_tabla_original_height);
        if(callback !== null && callback !== undefined) callback();
    }

    if($(".tabla-recuento").height() <= $(".contenedor-tabla")[0].scrollHeight){
        $(".desplazar").hide();
    }
}

function achicar_tabla_recuento(fast, callback){
    var height = null;
    var padding_tabla_recuento =  parseInt($(".tabla-scrolleable").css("padding-top"));
    var alto_tabla_recuento = $(".tabla-scrolleable").height();
    var alto_tabla_campos = $(".tabla-campos").height();
    var alto_contenedor_tabla = $(".contenedor-tabla").height();

    if(alto_tabla_recuento + padding_tabla_recuento + alto_tabla_campos > alto_contenedor_tabla){
        height = alto_contenedor_tabla - (padding_tabla_recuento + alto_tabla_campos + 10);
    } else {
        height = alto_tabla_recuento + 2;
    }
    if(effects && !fast){
        $(".tabla-scrolleable").animate({"height": height}, 500, callback);
    } else {
        $(".tabla-scrolleable").height(height);
        if(callback !== undefined && callback !== null) callback();
    }

    if($("#scroll_tabla").height() > $(".tabla-scrolleable").height()){
        var botones = $(".desplazar");
        $(botones[0]).click({"element":".tabla-scrolleable", "pixels":-100}, mover);
        $(botones[1]).click({"element":".tabla-scrolleable", "pixels":100}, mover);
        botones.show();
    }
}

function show_botones(callback){
    show_elements("#btn_regresar, #terminar_escrutinio", callback);
}

function hide_botones(callback){
    hide_elements("#btn_regresar, #terminar_escrutinio", callback);
}

function show_btn_qr(callback){
    if($("#asistente_cierre").is(":visible")){
        show_elements("#btn_qr", callback);
    }
}

function hide_btn_qr(callback){
    hide_elements("#btn_qr", callback);
}

function show_scroll_acta(callback){
    show_elements(".desplazar-acta", callback);
}

function hide_scroll_acta(callback){
    hide_elements(".desplazar-acta", callback);
}

function show_lista_campos(callback){
    show_elements("#campos_extra", callback);
}

function hide_lista_campos(callback){
    hide_elements("#campos_extra", callback);
}

function show_boletabox(){
    var box  = $(".boletabox");
    box.html($("#boleta").html());
    var svg = $(".boletabox svg");
    svg.css("transform", "scale(0.7)");
    show_elements(".boletabox");
}

function hide_boletabox(){
    hide_elements(".boletabox");
}

function show_qrbox(){
    var path_qr = $("#img_qr2").attr("src");
    $(".qrbox img").attr("src",path_qr);
    show_elements(".qrbox");
}

function hide_qrbox(){
    hide_elements(".qrbox");
}

function show_dialogo(dialogo){
    $(".mensaje-popup p").text("");
    for(var key in dialogo.mensaje){
        $(".mensaje-popup ." + key).text(dialogo.mensaje[key]);
    }
    $(".popup-box .btn").hide();
    if(dialogo.btn_cancelar){
        $(".btn-cancelar").show();
    }
    if(dialogo.btn_aceptar){
        $(".btn-aceptar").show();
    }
    if (dialogo.btn_aceptar && dialogo.btn_cancelar && $("#keyboard").is(":visible")) {
        $(".popup").addClass("confirma");
    } else {
        $(".popup").removeClass("confirma");
    }
    show_elements(".popup-box");
}

function hide_dialogo(){
    hide_elements(".popup-box");
}

function hide_pantalla_impresion_certificados(){
    hide_elements("#impresion_certificados");
}


function show_body(){
    show_elements("body");
}
