function document_ready(){
    preparar_eventos();
    send("document_ready");
}

$(document).ready(document_ready);

function pantalla_confirmacion_apertura(data) {
    var template = get_template("confirmacion", "pantallas/apertura");

    var img = decodeURIComponent(data[1]);
    
    var template_data = {
        titulo: data[0],
    };

    html_pantallas = template(template_data);
    $(".contenedor-confirmacion").html(html_pantallas);
    $(".texto-confirmacion").html(img);
    $(".aceptar").on("click", confirmar_apertura);
    $(".cancelar").on("click", cancelar_apertura);
    place_text(constants.i18n);
    $(".contenedor-confirmacion").show();
}

function pantalla_proxima_acta(data){
    $("#imprimiendo").hide();
    $("#otra_acta").show();
}

function imprimiendo(){
    $("#acciones").hide();
    $("#otra_acta").hide();
    $("#imprimiendo").show();
}

function confirmar_apertura(){
    imprimiendo();
    send("msg_confirmar_apertura", true);
}

function cancelar_apertura(){
    send("msg_confirmar_apertura", false);
}

function show_body(){
    $("body").show();
}

function msg_papel_no_puesto(){
    var template = get_template("popup", "partials/popup");
    var mensaje = constants.i18n.papel_no_puesto;
    var template_data = {
        pregunta: mensaje,
        btn_aceptar: true,
        btn_cancelar: false,
    };
    var html_contenido = template(template_data);
    return html_contenido;
}

function msg_apertura_no_almacenada(){
    var template = get_template("popup", "partials/popup");
    var mensaje = constants.i18n.apertura_no_almacenada;
    var template_data = {
        pregunta: mensaje,
        btn_aceptar: true,
        btn_cancelar: false,
    }
    var html_contenido = template(template_data);
    return html_contenido;
}

