function document_ready(){
    send("document_ready");
}

$(document).ready(document_ready);

function popular_header(){
    var template_header = get_template("encabezado", "partials");
    var html_header = Mustache.to_html(template_header, {'voto': false});
    $('#encabezado').html(html_header);
}

function click_boton_popup(){
    $(".acciones div").off("click");
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-datos").hide();
    $("input:invalid").first().focus();
}

function pantalla_confirmacion_apertura(data) {
    var template = get_template("confirmacion", "pantallas/ingresodatos");
    hide_all();

    var img = decodeURIComponent(data[1]);
    
    var template_data = {
        titulo: data[0],
    };

    html_pantallas = Mustache.to_html(template, template_data);
    $(".contenedor-confirmacion").html(html_pantallas);
    $(".texto-confirmacion").html(img);
    $(".aceptar").on("click", confirmar_apertura);
    $(".cancelar").on("click", cancelar_apertura);
    show_elements(".contenedor-confirmacion");
}

function confirmar_apertura() {
    hide_elements(".cancelar, .aceptar", function(){
        $(".acciones").html('<h1 class="texto-imprimiendo">Imprimiendo</h1>');
        send("msg_confirmar_apertura", true);
    });
}

function cancelar_apertura() {
    send("msg_confirmar_apertura", false);
}

function show_body(){
    show_elements("body");
}
