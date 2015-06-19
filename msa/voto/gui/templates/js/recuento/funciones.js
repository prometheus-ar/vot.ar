var ultimo_estado = null;
var seleccion_actual = null;
var puede_cambiar_vista = false;
var scroll_tabla_original_height = null;
var row_height = 22;
var mostrar_partidos = false;

function document_ready(){
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();

    $("body").on("click", ".contenedor-votado", resaltar_seleccion);
    $(".tabla-recuento").on('click', toggle_vista);

    setTimeout(function(){
        achicar_tabla_recuento();
        bindear_botones_instructivo();
        scroll_tabla_original_height = $(".tabla-scrolleable").height();
        $("#boleta").on('click', show_boletabox);
        $(".boletabox").on('click', hide_boletabox);
        $(".qrbox").on('click', hide_qrbox);
    }, 2000);

    $(".popup .btn").on('click', click_boton_popup);
    $("#btn_qr").on('click', show_qrbox);

}

$(document).ready(document_ready);

function popular_html(){

    var pantallas = ["pre_recuento", "durante_recuento", "terminando_recuento",
                     "imprimiendo_recuento", "post_recuento"];
    var html_pantallas = "";
    for(var i in pantallas){
        html_pantallas += get_template(pantallas[i], "pantallas/recuento");
    }
    $(".contenedor-der").html(html_pantallas);

    var template_header = get_template("encabezado", "partials");
    var template_instructivo = get_template("instructivo",
                                            "pantallas/recuento");
    var template_impresion = get_template("slides_impresion",
                                          "pantallas/recuento");
    var template_asistente = get_template("asistente_cierre",
                                          "pantallas/recuento");

    var html_header = Mustache.to_html(template_header, {'escrutinio': true,
                                                         'mesa': true});
    var html_instructivo = Mustache.to_html(template_instructivo);
    var html_asistente = Mustache.to_html(template_asistente);

    $('#encabezado').html(html_header);
    $('#instructivo').html(html_instructivo);
    $('.slides-impresion').html(template_impresion);
    $('#asistente_cierre').html(html_asistente);
}

function bindear_botones_instructivo() {
    $("#instructivo").on('click', ".btn-anterior", prev_slide);
    $("#instructivo").on('click', ".btn-siguiente", next_slide);
    $("#instructivo").on('click', ".btn-iniciar", next_slide);
    $("#instructivo").on('click', "#btn_finalizar", reset_instructivo);
}

function preparar_acta(data){
    $("#campos_extra").off('click', ".btn-campo");
    // Oculto el boton mientras espero a que se genere la imagen del acta.
    hide_elements("#terminar_escrutinio");
    // Muestro el mensaje "Generando".
    set_panel_estado(8);
    show_elements("#panel_estado");

    var campos_recuento = get_valores_campos();
    set_campos_extra(campos_recuento);
}

function generar_lista_campos(campos){
    $("#acta").hide();
    var html = "";
    var lista_campos = $("#campos_extra");
    lista_campos.html(html);
    for(var i in campos){
        var campo = generar_campo(campos[i]);
        html += campo;
    }
    lista_campos.html(html);
    actualizar_total();
}

function generar_campo(campo){
    var template = get_template("campo", "pantallas/recuento");

    var id_campo = "campo_" + campo.codigo;
    var es_editable = "";
    if(campo.editable){
        es_editable = "campo-editable";
    }

    var template_data = {"campo": campo,
                         "id_campo": id_campo,
                         "editable": campo.editable,
                         "class_editable": es_editable,
                        };

    var html = Mustache.to_html(template, template_data);
    return html;
}


function mostrar_acta(image_data){
    var img = decodeURIComponent(image_data);
    var contenedor = $("#img_acta");
    contenedor.html(img);
    contenedor.css("margin", "auto");
    var svg = $("#img_acta svg");
    svg.css("transform", "scale(0.45)");
    svg.css("transform-origin", "50% 0px");

    /* Scroll del preview del acta */
    var botones = $(".desplazar-acta");
    $(botones[0]).click({"element": "#img_acta", "pixels":-100}, mover);
    $(botones[1]).click({"element": "#img_acta", "pixels":100}, mover);
}

function generar_tabla_campos(campos){
    var template = get_template("tabla_campos", "pantallas/recuento");

    var tabla_campos = $("#tabla_campos");
    //tabla_campos.html("");
    var filas = [];
    for(var i in campos){
        filas.push(crear_fila_campo(campos[i]));
    }

    var template_data = {
        "palabra_categoria": constants.palabra_categoria.toUpperCase(),
        "campos": filas
    };

    var html = Mustache.to_html(template, template_data);
    tabla_campos.html(html);
}

function crear_fila_campo(campo){
    var codigo = campo.codigo;
    if(constants.listas_especiales.indexOf(codigo) != -1){
        codigo = codigo.split(".").slice(-1); 
    }
    var template_data = {"codigo": codigo,
                         "titulo": campo.titulo,
                         "valor": campo.valor};
    return template_data;
}

function profiler() {
    console.timeline();
    console.profile();
    setTimeout(function() {
        console.timelineEnd();
        console.profileEnd();
    }, 10000);
}

function modificar_campo(){
    var boton = $(this);
    var input = boton.siblings('input');
    var valor_viejo = parseInt(input.val());
    var es_incremento = boton.hasClass('incremento');
    
    var valor_nuevo = valor_viejo;
    if(es_incremento){
        valor_nuevo = valor_viejo + 1;
    } else if(valor_viejo > 0) {
        valor_nuevo = valor_viejo - 1;
    }

    input.attr('value',valor_nuevo);
    actualizar_total();
}

function actualizar_total(){
    var total_nuevo = parseInt($(".numero-procesada").text());
    var valores = get_valores_campos();
    for(var i in valores){
        total_nuevo += valores[i];
    }
    $("#campo_TOT .valor-campo").text(total_nuevo);
}

function get_valores_campos(){
    var campos = $(".campo-editable");
    var campos_recuento = {};
    for(var i=0; i<campos.length; i++){
        var campo = $(campos[i]);
        var codigo = campo.attr('id').split('_')[1];
        campos_recuento[codigo] = parseInt(campo.children('input').val());
    }
    return campos_recuento;
}

function actualizar_resultados(data){
    hide_elements("#instructivo");
    $("#tabla_recuento td").removeClass("voto-resaltado");

    $(".numero-procesada").text(data.cant_leidas);
    seleccion_actual = {'seleccion': data.seleccion,
                        'image_data': data.image_data};
    hide_elements("#resultado, #boleta", actualizar_seleccion);
    hide_dialogo();
    show_elements("#resultado, #boleta", actualizar_tabla);
    puede_cambiar_vista = true;
}

function actualizar_seleccion(){
    var panel_boleta = $("#boleta");
    var panel_seleccion = $("#resultado");
    var img = decodeURIComponent(seleccion_actual.image_data);

    panel_boleta.html(img);
    var svg = $("#boleta");
    svg.css("transform", "scale(0.52)");
    svg.css("transform-origin", "0 0");
    panel_seleccion.html("");
    var html = "";

    var seleccion = seleccion_actual.seleccion;
    if(seleccion.length){
        panel_seleccion.show();
        for(var i in seleccion){
            html += crear_item_candidato(seleccion[i]);
        }
        panel_seleccion.html(html);
    } else {
        panel_seleccion.hide();
    }
    hide_boletabox();
    $("body").attr('data-vista', 'vista-boleta');
    $("#boleta").show();
}

function crear_item_candidato(data){

    var template = get_template("candidato", "pantallas/recuento");

    var blanco = "";
    var nombre_partido = "";
    var candidato = data.candidato;
    var categoria = data.categoria;

    if(candidato.cod_lista == constants.cod_lista_blanco){
        blanco = "blanco";
        path_imagen_candidato = "img/opcion_blanco.png";
        path_imagen_partido = "img/opcion_blanco.png";

    } else {
        nombre_partido = candidato.nombre_lista;
        path_imagen_candidato = get_path_candidato(candidato);
        path_imagen_partido = get_path_lista(candidato.lista.imagen);
    }
    var id_contenedor = "contenedor_" + categoria.codigo;
    var consulta_popular = categoria.consulta_popular == "SI";
    var div_colores = crear_div_colores(candidato.lista.color);
    var template_data = {
        'blanco': blanco,
        'consulta_popular': consulta_popular?"consulta-popular":"",
        'nombre_cargo': categoria.nombre,
        'palabra_lista': consulta_popular && blanco!="blanco"?" ":constants.palabra_lista,
        'lista_numero': consulta_popular && blanco!="blanco"?" ":trimNumber(candidato.lista.numero),
        'lista_codigo': candidato.cod_lista,
        'path_imagen_candidato': path_imagen_candidato,
        'path_imagen_partido': path_imagen_partido,
        'partido_nombre': nombre_partido,
        'candidato_nombre': candidato.nombre,
        'candidato_secundario': candidato.secundarios,
        'id_contenedor': id_contenedor,
        'colores': div_colores
    };

    var item = Mustache.to_html(template, template_data);
    return item;
}

function limpiar_panel_estado(){
    var panel_estado = $("#panel_estado");
    panel_estado.removeClass("panel-estado-" + ultimo_estado);

    var mensaje = constants.mensajes_panel[constants.cod_estado_espera][0];
    var clase = "panel-estado-" + constants.cod_estado_espera;
    if(ultimo_estado == constants.cod_estado_imprimiendo || ultimo_estado == constants.cod_estado_generando){
        mensaje = "";
    }
    panel_estado.children('p').text(mensaje);
    panel_estado.addClass(clase);

    ultimo_estado = constants.cod_estado_espera;
}

function reset_instructivo(){
    var slides = $(".contenedor-central div.slide");
    slides.hide();
    slides.first().show();
    $(".btn-anterior img").hide();
    $(".btn-siguiente img").hide();
}

function pedir_acta(data){
    var tipo = data.tipo;
    var img = decodeURIComponent(data.imagen);

    hide_elements("#acta, #acta .encabezado, .desplazar-acta");

    var id_contenedor = '#insercion_' + tipo;
    $(id_contenedor).find('.imagen').html(img);

    var svg = $(id_contenedor).find('svg');
    svg.css('transform', 'scale(0.55)');
    svg.css('transform-origin', '110% -40% 0');

    show_elements("#insercion_" + tipo);
}

function preview_acta(data){
    hide_elements("#instructivo");
    hide_elements("#insercion_" + data.tipo[0]);
    if(data.tipo[0] == constants.CIERRE_ESCRUTINIO || data.tipo[0] == constants.CIERRE_TRANSMISION){
        $("#img_acta").height(600);
    }
    if(data.hide_titulo !== undefined && data.hide_titulo){
        $("#acta .titulo").hide();
    } else {
        $("#acta .titulo").show();
    }
    mostrar_acta(data.imagen);
    show_elements("#acta");
}

function es_interna(lista){
    return lista.hasOwnProperty('cod_interna');
}
