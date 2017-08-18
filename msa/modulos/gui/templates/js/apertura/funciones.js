function document_ready(){
    /* Corre cuando termina de cargar la pagina */
    // hookeamos los eventos
    preparar_eventos();
    // y le avisamos al backend que ya terminamos de cargar.
    send("document_ready");
}

$(document).ready(document_ready);

function pantalla_confirmacion_apertura(data) {
    /* Muestra la pantalla de confirmacion de la apertura
     *
     * Argumentos:
     *     data -- un array con los datos a mostrar en la pantalla
     */
    // traemos el template
    var template = get_template("confirmacion", "pantallas/apertura");
    // decodificamos la imagen.
    var img = decodeURIComponent(data[1]);
    
    var template_data = {
        titulo: data[0],
    };
    // armamos la pantalla.
    html_pantallas = template(template_data);
    $(".contenedor-confirmacion").html(html_pantallas);
    $(".texto-confirmacion").html(img);
    // hookeamos los eventos
    $(".aceptar").on("click", confirmar_apertura);
    $(".cancelar").on("click", cancelar_apertura);
    // aplicamos la internacionalizacion
    place_text(constants.i18n);
    // mostramos la pantalla
    $(".contenedor-confirmacion").show();
}

function pantalla_proxima_acta(data){
    /* Muestra el mensaje de "proxima acta" */
    $("#imprimiendo").hide();
    $("#otra_acta").show();
}

function imprimiendo(){
    /* Muestra el mensaje de "imprimiendo" */
    $("#acciones").hide();
    $("#otra_acta").hide();
    $("#imprimiendo").show();
}

function confirmar_apertura(){
    /* callback del click de confirmacion de apertura */
    imprimiendo();
    send("msg_confirmar_apertura", true);
}

function cancelar_apertura(){
    /* callback del click de cancelacion de apertura */
    send("msg_confirmar_apertura", false);
}

function show_body(){
    /* muestra el body */
    $("body").show();
}

function msg_papel_no_puesto(){
    /* Genera el popup de papel no puesto */
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
    /* Genera el popup de "apertura no almacenada" (error de registro) */
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

