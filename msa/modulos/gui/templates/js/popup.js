function cargar_dialogo(callback_template){
    /*
     * Funcion que muestra un dialogo, llamando al
     * callback para generar el contenido html del mismo
     * Argumentos:
     * callback_template -- funcion que devuelve el html contenido del popup
     */
    var html_contenido = window[callback_template];
    $('.popup-box').html(html_contenido);
    place_text(constants.i18n);
    $(".popup-box .btn").on("click", click_boton_popup);
    $(".popup-box").show();
}

function cargar_dialogo_default(mensaje){
    /*
     * Funcion que muestra un dialogo, usando el template default de popup
     * que se encuentra en partials/popup/popup.html
     * mensaje -- diccionario que se utiliza para renderizar el template html
     */
    var template = get_template("popup", "partials/popup");
    var html_contenido = template(mensaje);
    $('.popup-box').html(html_contenido);
    place_text(constants.i18n);
    $(".popup-box .btn").on("click", click_boton_popup);
    $(".popup-box").show();
}

function hide_dialogo(){
    $(".popup-box").hide();
    $(".popup-box").trigger("hideDialogo");
}

function click_boton_popup(){
    /*
     * Se ejecuta cuando se apreta un boton en el popup y determina
     * si la respuesta es positiva o no
     */
    respuesta = $(this).hasClass("btn-aceptar");
    hide_dialogo();
    $(this).trigger("clickBtnPopup");
    setTimeout(function(){procesar_dialogo(respuesta)}, 100);
}

// De Ingreso_datos
function restaurar_foco_invalido(){
    $("input:invalid").first().focus();
}

function click_boton_confirmacion(){
    respuesta = $(this).hasClass("btn-aceptar");
    $(this).off("click");
    $("#mensaje").hide();
    setTimeout(function(){procesar_dialogo(respuesta);},
               100);
}

function procesar_dialogo(respuesta){
    send('respuesta_dialogo', respuesta);
}
