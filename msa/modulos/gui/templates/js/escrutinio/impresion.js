function iniciar_secuencia_impresion(){
    send("iniciar_secuencia_impresion");
}

function pantalla_pedir_acta(datos){
    var svg_data = decodeURIComponent(datos.imagen);
    var imagen = $("#pantalla_pedir_acta .imagen");
    imagen.html(svg_data);
    imagen.css("transform", "scale(0.6) translateX(70px)");
    imagen.css("transform-origin", "0 0");
    var texto_insercion_acta = constants.i18n["introduzca_acta_" + datos.tipo];
    $("#pantalla_pedir_acta #texto_insercion_acta").html(texto_insercion_acta);

    patio.pantalla_pedir_acta.only();
}

function pantalla_copias(){
    var texto_insercion_acta = constants.i18n.introduzca_acta_escrutinio;
    $("#pantalla_pedir_acta #texto_insercion_acta").html(texto_insercion_acta);
    patio.pantalla_copias.only();
}

function mensaje_popup_recuento(){
    var mensajes = {
        alerta:constants.i18n.recuento_no_almacenado_alerta,
        aclaracion:constants.i18n.recuento_no_almacenado_aclaracion,
    };
    return generar_popup(mensajes);
}

function mensaje_popup_transmision(){
    var mensajes = {
        alerta:constants.i18n.transmision_no_almacenada_alerta,
        aclaracion:constants.i18n.transmision_no_almacenada_aclaracion,
    };
    return generar_popup(mensajes);
}

function mensaje_popup_escrutinio(callback){
    var mensajes = {
        alerta:constants.i18n.certificado_no_impreso_alerta,
        aclaracion:constants.i18n.certificado_no_impreso_aclaracion,
    };
    return generar_popup(mensajes, callback);
}

function mensaje_popup_certificado(){
    return mensaje_popup_escrutinio(show_slide);
}

function mensaje_popup_copia_fiel(){
    return mensaje_popup_escrutinio();
}

function generar_popup(mensajes, callback){
    ocultar_mensaje_imprimiendo(callback);
    var template = get_template("popup", "partials/popup");
    var template_data = {
        alerta: mensajes.alerta,
        aclaracion: mensajes.aclaracion,
        btn_aceptar: true,
        btn_cancelar: false,
    };
    var html_contenido = template(template_data);
    return html_contenido;
}


function mensaje_imprimiendo(){
    patio.mensaje_imprimiendo.only();
}

function ocultar_mensaje_imprimiendo(callback){
    if($("#mensaje_imprimiendo").is(":visible")){
        if(typeof(callback) == "undefined" || callback == 0){
            patio.pantalla_pedir_acta.only();
        } else {
            callback();
        }
    }
}
