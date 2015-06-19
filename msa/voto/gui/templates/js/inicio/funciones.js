var ultimo_estado = null;
var seleccion_actual = null;
var puede_cambiar_vista = false;

function click_alto_contraste(){
    $("body").toggleClass("alto-contraste");
    ajustar_botones_contraste();
}

function document_ready(){
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    $("#btn_apagar").click(apagar);
    $("#btn_calibrar").click(calibrar);
    $(".popup .btn").click(click_boton_popup);
}

$(document).ready(document_ready);

function popular_header(){
    var template_header = get_template("encabezado", "partials");
    var html_header = Mustache.to_html(template_header, {'voto': false});
    $('#encabezado').html(html_header);
}

function place_text(tuples){
    for(i in tuples){
        var tuple = tuples[i];
        $("#_txt_" + tuple[0] + ", ._txt_" + tuple[0]).html(tuple[1]);
    }
}

function pantalla_inicio(data){
   show_pantalla_inicio();
}

function click_boton_popup(){
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-box").hide();
    setTimeout(function(){procesar_dialogo(respuesta)}, 100);
}
