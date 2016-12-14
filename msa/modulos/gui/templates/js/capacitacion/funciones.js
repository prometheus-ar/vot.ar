function click_boton_simulador(){
    send("configurar_mesa", ["sufragio", this.id.split("_")[1]]);
}

function click_boton_asistida(){
    send("configurar_mesa", ["asistida", this.id.split("_")[1]]);
}

function click_boton_boleta(){
    var dic_ = {
        pregunta: constants.i18n.inserte_boleta_capacitacion,
        aclaracion: constants.i18n.imprimira_voto_en_blanco,
        alerta: constants.i18n.imprimir_boleta_demostracion,
        btn_cancelar: true,
    };
    activar_impresion(this.id.split("_")[1]);
    cargar_dialogo_default(dic_);
    $(".btn-cancelar").click(
        function(){
            cancelar_impresion();
        }
    );
}

function error_impresion_boleta(){
    var dic_ = {
        alerta: constants.i18n.error_imprimir_boleta_demostracion,
        btn_aceptar: true,
    };
    cargar_dialogo_default(dic_);
    $(".btn-cancelar").click(
        function(){
        }
    );
}

function document_ready(){
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});

    load_ready_msg();

}

$(window).load(document_ready);

function cargar_botones_ubicaciones(data){
    var clase = "";
    var datos_ubicaciones = data;
    var botones_ubicacion = $("#botones-ubicacion");
    var columnas = [];
    var items = [];
    for (i=0; i<datos_ubicaciones.length; i++){
        var ubicacion = datos_ubicaciones[i];

        var data_template = {
            'nro_mesa': ubicacion[0],
            'departamento': (constants.mostrar_departamentos)? ubicacion[1] : false,
            'municipio': ubicacion[2],
            'extranjera': ubicacion[3],
            'mostrar_boton_impresion': constants.preimpresion_boleta,
        }

        items.push(data_template);
    }

    var numero_cols = Math.floor(items.length / constants.items_columna);
    if (items.length % constants.items_columna){
        //Si es cero, el número de items por columnas es exacto
        numero_cols = numero_cols + 1;
    }
    var template = get_template("boton_ubicacion", "pantallas/capacitacion");
    var html = template({"ubicaciones": items, "numero_cols": numero_cols});
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
    $("#contenedor_opciones").hide();
    $(".btn .demo").click(click_boton_simulador);
    $(".btn .asistida").click(click_boton_asistida);
    $(".btn .imprimir").click(click_boton_boleta);
}
