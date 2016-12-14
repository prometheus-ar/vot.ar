var _pantalla_clasificacion_cargada = false;

function volver_al_recuento(){
    $("#cantidad_escrutadas").show();
    send("habilitar_recuento");
    pantalla_inicial();
}

function anterior_clasificacion(){
    sonido_tecla();
    var index = _campo_get_index();
    if(index){
        _campo_get(index - 1);
        actualizar_botones_panel();
    } else {
        volver_al_recuento();
    }
}

function siguiente_clasificacion(){
    sonido_tecla();
    var index = _campo_get_index();
    _campo_get(index + 1);
    actualizar_botones_panel();
}

function actualizar_botones_panel(){
    var index = _campo_get_index();
    var len_campos = _campo_get_ids().length;
    if(index == len_campos - 1){
        $("#boton_siguiente").hide(); 
        $("#boton_imprimir").show(); 
        $("#_txt_volver").html(constants.i18n.palabra_anterior);
    } else if (index === 0){
        $("#boton_siguiente").show(); 
        $("#boton_imprimir").hide(); 
        $("#_txt_volver").html(constants.i18n.volver);
    } else {
        $("#boton_siguiente").show(); 
        $("#boton_imprimir").hide(); 
        $("#_txt_volver").html(constants.i18n.palabra_anterior);
    }

    var cod_especial = $(".seleccionado").attr("id").split("_")[1];
    var titulo = constants.titulos_especiales[cod_especial];
    var contenido = constants.descripcion_especiales[cod_especial];
    $("#definiciones .titulo").html(titulo);
    $("#definiciones .contenido").html(contenido);
}

function generar_clasificacion_de_votos(datos){
    _pantalla_clasificacion_cargada = true;
    listas = [];
    var obj_procesadas = {
        "id_campo": "boletas_procesadas",
        "cantidad": datos.boletas_procesadas,
        "titulo": constants.i18n.boletas_procesadas,
        "editable": false,   
    };
    listas.push(obj_procesadas);

    for(var i in datos.listas_especiales){
        var codigo = datos.listas_especiales[i];
        var obj_especial = {
            "id_campo": codigo,
            "cantidad": 0,
            "titulo": constants.titulos_especiales[codigo],
            "editable": true,
        };
        listas.push(obj_especial);
    }

    var obj_totales = {
        "id_campo": "boletas_totales",
        "cantidad": datos.boletas_totales,
        "titulo": constants.i18n.total_general,
        "editable": false,   
    };
    listas.push(obj_totales);
    var contenedor_campos = $("#campos_extra");
    contenedor_campos.html("");
    var template = get_template("campo_extra", "pantallas/escrutinio");
    for(var j in listas){
        var rendered = template(listas[j]);
        contenedor_campos.append(rendered);
    }
    $(".btn-bajar").on("click", bajar_numero);
    $(".btn-subir").on("click", subir_numero);
}

function bajar_numero(){
    sonido_tecla();
    var target = $(this).data("target");
    var elemento = $("#" + target);
    var numero = parseInt(elemento.text());
    if(numero > 0){
        elemento.text(numero - 1);
        elemento.attr("data-value", numero - 1);
        elemento.trigger("change");
    }
}

function subir_numero(){
    sonido_tecla();
    var target = $(this).data("target");
    var elemento = $("#" + target);
    var numero = parseInt(elemento.text());
    elemento.text(numero + 1);
    elemento.attr("data-value", numero + 1);
    elemento.trigger("change");
}

function pantalla_clasificacion_votos(datos){
    /*
     * muestra la pantalla de clasificacion de votos
     */
    var pantalla = patio.pantalla_clasificacion_votos;
    var mostrar_pantalla = false;
    if(!_pantalla_clasificacion_cargada){
        if(datos.listas_especiales.length){
            mostrar_pantalla = true;
            generar_clasificacion_de_votos(datos);

            $(".valor.editable").on("change", total_boletas);
            $("#panel_clasificacion").on("click", "#boton_volver",
                                         anterior_clasificacion);
            $("#panel_clasificacion").on("click", "#boton_siguiente",
                                         siguiente_clasificacion);
            $("#panel_clasificacion").on("click", "#boton_imprimir",
                                         mensaje_fin_escrutinio);
            $("#campos_extra").on("click", ".campo_editable",
                                  _campo_seleccionar);
        } else {
           iniciar_secuencia_impresion(); 
        }
    } else {
        mostrar_pantalla = true;
        $("#numero_boletas_procesadas").html(datos.boletas_procesadas);
        total_boletas();
    }

    if(mostrar_pantalla){
        pantalla.only();
        _campo_get(0);
        actualizar_botones_panel();
    }
}

function _campo_get_index(){
    var campos = _campo_get_ids();
    var campo_actual = $(".seleccionado.campo_editable").attr("id");
    var index = campos.indexOf(campo_actual);
    return index;
}

function _campo_get_ids(){
    var campos = $(".campo_editable").map(
        function(){
            return this.id;
        }
    );
    return campos.get();
}

function _campo_get(index){
    $("#campos_extra .campo").removeClass("seleccionado");
    var campo = $(".campo_editable").get(index);
    $(campo).addClass("seleccionado");
}

function _campo_seleccionar(){
    sonido_tecla();
    $("#campos_extra .campo").removeClass("seleccionado");
    $(this).addClass("seleccionado");
    actualizar_botones_panel();
}

function cargar_clasificacion_de_votos(){
    $("#cantidad_escrutadas").hide();
    send("cargar_clasificacion_de_votos");
}

function guardar_listas_especiales(){

    var listas = {};
    var campos = $(".valor.editable").each(function(index, element){
        var parts = this.id.split("_");
        listas[parts[1]] = parseInt($(this).text());
    });
    send("guardar_listas_especiales", listas);
}

function total_boletas(){
    var numeros = $(".valor.editable").map(
        function(){ 
            return parseInt($(this).text());
        }
    ).get();
    numeros.push(parseInt($("#numero_boletas_procesadas").text()));
    var total = numeros.reduce(
        function(a,b){
            return parseInt(a) + parseInt(b);
        });
    $("#valor_boletas_totales").text(total);
}
