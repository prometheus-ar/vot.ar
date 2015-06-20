
function click_boton(){
    send("configurar_mesa", this.id);
}

function document_ready(){
    $(document).bind("dragstart", function(event){event.target.click();});

    load_ready_msg();

}

$(window).load(document_ready);

function popular_header(){
    var template_header = get_template("encabezado", "partials");
    var html_header = Mustache.to_html(template_header, {'voto': false});
    $('#encabezado').html(html_header);
}

function cargar_botones_ubicaciones(data){
    var clase = "";
    var datos_ubicaciones = data;
    var botones_ubicacion = $("#botones-ubicacion");
    var items = []
    for (i=0; i<datos_ubicaciones.length; i++){
        var ubicacion = datos_ubicaciones[i];
        var display_ext = false;

        if (ubicacion[2] != ''){
            display_ext = true;
        }

        var data_template = {
            'nro_mesa': ubicacion[0],
            'municipio': ubicacion[1],
            'extranjera': ubicacion[2],
            'display_ext': display_ext,
        }

        items.push(data_template);
    }
    var template = get_template("boton_ubicacion", "pantallas/demo");
    var html = Mustache.to_html(template, {"ubicaciones": items});
    botones_ubicacion.html(html);

    switch (true) {
        case i <= 11:
            clase = "una-columna";
            break;
        case i <= 22:
            clase = "dos-columnas";
            break;
        case i <= 33:
            clase = "tres-columnas";
            break;
        case i <= 44:
            clase = "cuatro-columnas";
            break;
        default:
            clase = "anidado";
    }

    $("#botones-ubicacion").addClass(clase);
    $(".btn").click(click_boton);

}
