var speed = 'fast';
var effects;


//Show hide
function show_elements(selector, callback) {
    var elems = $(selector);
    if (effects) {
        elems.fadeIn(speed, callback);
    } else {
        elems.show();
        if (callback != null) callback();
    }
}

function hide_elements(selector, callback) {
    var elems = $(selector);
    if (effects) {
        elems.fadeOut(speed, callback);
    } else {
        elems.hide();
        if (callback != null) callback();
    }
}

function show_dialogo_error(dialogo) {
    $(".popup-datos .popup .btn").on("click", click_popup_error_datos);
    $(".popup-datos .mensaje-popup p").text("");
    for (var key in dialogo.mensaje) {
        $(".popup-datos .mensaje-popup ." + key).html(dialogo.mensaje[key]);
    }
    $(".popup-datos .btn").hide();
    if (dialogo.btn_cancelar) {
        $(".popup-datos .btn-cancelar").show();
    }
    if (dialogo.btn_aceptar) {
        $(".popup-datos .btn-aceptar").show();
        if (typeof dialogo.btn_aceptar != "boolean") {
            $(".popup-datos .btn-aceptar").addClass(dialogo.btn_aceptar);
        }
    }
    show_elements(".popup-datos");
}

function show_dialogo_accion(dialogo) {
    show_dialogo_error(dialogo);
    $(".popup-datos .popup .btn").off();
    $(".popup-datos .popup .btn").on("click", click_popup_accion);
}

function hide_dialogo() {
    hide_elements(".popup-box");
    hide_elements(".popup-datos");
}

function show_dialogo_confirmacion() {
    $(".acciones div").on("click", click_boton_confirmacion);
    hide_elements("#keyboard");
    show_elements(".placeholder-confirma");
}

function click_boton_confirmacion(){
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-box").hide();
    setTimeout(function(){procesar_dialogo(respuesta);},
               100);
}

function click_popup_error_datos(){
    $(".popup-datos").hide();
    hide_dialogo_confirmacion();
    $("input:invalid").first().focus();
}

function click_popup_accion(){
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-datos").hide();
    setTimeout(function(){procesar_dialogo(respuesta);},
               100);
}

function hide_dialogo_confirmacion() {
    hide_elements(".placeholder-confirma");
    show_elements("#keyboard");
}

function hide_all(callback) {
    //En apertura
    hide_elements("#pantalla_inicio");
    hide_elements("#contenedor_opciones"); 
    hide_elements("#pantalla_confirmacion"); 
    // En recuento
    hide_elements(".contenedor-datos");
    hide_elements(".contenedor-opciones-recuento");
    hide_elements(".contenedor-izq");
    hide_elements(".contenedor-der", callback);
}

//Funciones que muestran pantallas
function pantalla_ingresoacta(data) {
    hide_all();
    var template = get_template("ingreso_acta", "pantallas/ingresodatos");
    var template_popup = get_template("popup", "pantallas/ingresodatos");
    var template_data = {
        mensaje: data['mensaje']
    };
    var html_pantallas = $(Mustache.to_html(template, template_data));
    var html_popup = Mustache.to_html(template_popup);

    var img_svg = decodeURIComponent(data['imagen_acta']);
    $(html_pantallas).find('#ingresoacta_svg').html(img_svg);
    var svg = $(html_pantallas).find('#ingresoacta_svg svg');
    svg.css('transform', 'scale(0.55)');

    $('.contenedor-datos').html(html_pantallas);
    $('.popup-box-datos').html(html_popup);
    $("#accesibilidad").on("click", "#btn_salir", salir);
    hide_elements(".barra-titulo");
    show_elements("#contenedor_izq");
    show_elements("#contenedor_opciones");
    show_elements(".contenedor-datos");
}

function pantalla_mesaypin(data) {
    var teclado_fisico = data[0];
    var callback_aceptar = data[1];
    var mesa = data[2];
    hide_all();
    var template = get_template("mesa_y_pin", "pantallas/ingresodatos");
    var template_teclado = get_template("teclado", "pantallas/ingresodatos");
    var template_popup = get_template("popup", "pantallas/ingresodatos");
    var template_data = {
        pattern_mesa: "[0-9]*[F|M|X]?",
        pattern_pin: "([A-Z]{0,3}[0-9]{0,3})",
        mesa: mesa,
    };
    template_data.af_mesa = mesa === "";
    template_data.af_pin = mesa !== "";
    html_pantallas = Mustache.to_html(template, template_data,
                                      {teclado: template_teclado});
    html_popup = Mustache.to_html(template_popup);
    $(".barra-titulo p").attr("id","_txt_ingrese_datos_solicitados");
    $(".btn-cancelar p").attr("id","_txt_cancelar");
    $(".btn-aceptar p").attr("id","_txt_aceptar");
    $('.contenedor-datos').html(html_pantallas);
    $('.popup-box-datos').html(html_popup);
    inicializar_teclado(eval(callback_aceptar));
    show_elements(".barra-titulo");
    show_elements(".contenedor-datos", function(){
        if(!teclado_fisico){
            deshabilitar_teclado();
        }
    });
}

function pantalla_datospersonales(data) {
    var datos_precargados = false;
    var teclado_fisico = data['teclado_fisico'];
    var template = get_template("datos_personales", "pantallas/ingresodatos");
    var template_teclado = get_template("teclado", "pantallas/ingresodatos");
    var template_popup = get_template("popup", "pantallas/ingresodatos");
    hide_all();

    var autoridades = [
        {"cargo": "Presidente", "id_cargo": "presidente"}
    ];
    if(constants.cantidad_suplentes.length > 1){
        for (var i = 1; i <= constants.cantidad_suplentes; i++) {
            autoridades.push({"cargo": "Suplente " + i, "id_cargo": "suplente" + i});
        }
    } else if(constants.cantidad_suplentes == 1){
        autoridades.push({"cargo": "Suplente", "id_cargo": "suplente"});
    }

    var tipo_doc = [];
    for (var j = 0; j < constants.tipo_doc.length; j++) {
        tipo_doc.push(constants.tipo_doc[j][1]);
    }

    var template_data = {
        autoridades: autoridades,
        scroll: constants.cantidad_suplentes > 2,
        tipo_doc_default: tipo_doc[0],
        disabled_default: false
    };

    html_pantallas = Mustache.to_html(template, template_data,
                                      {teclado: template_teclado});
    html_popup = Mustache.to_html(template_popup);
    $(".contenedor-datos").html(html_pantallas);
    $('.popup-box-datos').html(html_popup);
    
    //Rellena los datos en los campos
    if (data["hora"]) {
        var datos_precargados = true;
        $("input[name='hora']").val(data["hora"]["horas"]);
        $("input[name='minutos']").val(data["hora"]["minutos"]);
    }
    if (data["autoridades"] && data["autoridades"].length) {
        var datos_precargados = true;
        for(var j = 0; j < data["autoridades"].length; j++) {
            for (valor in data["autoridades"][j]) {
                try{
                    var dato = data["autoridades"][j][valor].replace('&#39;', "'");
                } catch(TypeError){
                    var dato = data["autoridades"][j][valor];
                }
                var campo = $("[name='" + autoridades[j]["id_cargo"] + "_" + valor + "']");
                campo.attr("disabled", false);
            if (valor == "tipo_documento" && !isNaN(dato)) {
                    campo.val(tipo_doc[dato]);
                } else {
                    campo.val(dato);
                }
            }
        }
    }

    $(".barra-titulo p").attr("id", "_txt_ingrese_datos_solicitados");
    inicializar_teclado(eval(data["callback_aceptar"]));
    show_elements(".barra-titulo");
    show_elements(".contenedor-datos", function(){
        if(!teclado_fisico){
            deshabilitar_teclado();
        }
    });
 
    if (datos_precargados && !data.foco_hora) {
        $("input:last").focus();
    } else {
        $("input:first").focus();
    }
}

//Funciones que envian datos
function enviar_mesaypin() {
    // Envía al backend la mesa y pin ingresada por el usuario
    var nro_mesa = $("input[name='nro_mesa']").val();
    var nro_pin = $("input[name='nro_pin']").val();
    var data = {"mesa": nro_mesa,
        "pin": nro_pin};
    send("recibir_mesaypin", data);
}

function enviar_datospersonales() {
    // Envía al backend la hora y los datos de las autoridades de mesa
    // Obtenemos los cargos que hay en la pantalla
    
    var lista_cargos = [];
    $('.cargo').each(function (i, value) {
        lista_cargos.push(value.textContent.replace(' ', '').toLowerCase());
    });

    var tipo_doc = [];
    for (var j = 0; j < constants.tipo_doc.length; j++) {
        tipo_doc.push(constants.tipo_doc[j][1]);
    }

    var autoridades = [];
    for (var j = 0; j < lista_cargos.length; j++) {
        var autoridad = [];
        var input_cargo = $("#" + lista_cargos[j] + " input");
        input_cargo.each(function (k, ingreso) {
            var valor = $(ingreso).val();
            if (valor) {
                if(ingreso.name.split("_")[1] == "tipo") {
                    valor = tipo_doc.indexOf(valor);
                    valor = valor.toString();
                }
                autoridad.push(valor);
            } else {
                autoridad.push("");
            }
        });
        autoridades.push(autoridad);
    }

    // Obtenemos hora
    var hora = { 'horas': NaN, 'minutos': NaN };
    if ($("input[name='hora']").val().length > 0 || $("input[name='minutos']").val().length > 0) {
        hora = {'horas': filterInt($("input[name='hora']").val()),
                'minutos': filterInt($("input[name='minutos']").val())
        };
        if (isNaN(hora['horas']) || isNaN(hora['minutos'])) {
            hora['horas'] = 99;
            hora['minutos'] = 99;
        }
    }

    var data = {
        'hora': hora,
        'autoridades': autoridades
    };

    send("recibir_datospersonales", data);
}

//Auxiliares y otras
function deshabilitar_teclado() {
    $(".contenedor-datos input, .contenedor-datos select")
        .bind('keydown', function(event){
            event.preventDefault();
        });
}

function set_mensaje(data) {
    //$(".titulo_mensaje").html(data);
    $(".mensaje h1").html(data);
}

function inicializar_teclado(callback_aceptar) {
    var usa_tildes = constants.usa_tildes;
    $('#keyboard-qwerty').build_keyboard({callback_finish: callback_aceptar, usa_modifier: usa_tildes});
    $('#keyboard-alpha').build_keyboard({layout: "alpha", callback_finish: callback_aceptar, usa_modifier: usa_tildes});
    $('#keyboard-docs').build_keyboard({layout: "docs", callback_finish: callback_aceptar});
    $('#keyboard-num').build_keyboard({layout: "num", callback_finish: callback_aceptar});
    $("input[type='text']").keyboard();
}

function bindear_scrolls() {
    $("#_btn_scroll_arriba").on("click", scroll_up);
    $("#_btn_scroll_abajo").on("click", scroll_down);
}

function aceptar_mesa_y_pin(){
    var datos_invalidos = $(".mesaypin input").is(":invalid");
    if(!datos_invalidos){
        send("msg_confirmar_ingreso");
    } else {
        show_dialogo_error({"mensaje": {"alerta": constants.mensajes_error.mesa_pin_incorrectos},
                            "btn_aceptar": "error-validacion"});
    }
}


function aceptar_datos_personales() {

    function filtro_largo(index) {
        return ($(this).val().length === 1);
    }

    function filtro1(index){ 
        return $("input:not('.tipo_documento')", this).is(
            function(){ return $(this).val().length});
    }

    function filtro2(index){
    return $("input", this).is(
        function(){ return $(this).val().length === 0 });
    }

    var datos_invalidos = $(".nombre-autoridades input:not(.nro_documento)").is(":invalid");
    var largo_invalido = $(".nombre-autoridades input:not(.nro_documento)").is(filtro_largo);
    var documentos_invalidos = $(".nombre-autoridades input.nro_documento").is(":invalid");
    var documentos_numeros_invalidos = parseInt($(".nombre-autoridades input.nro_documento").val()) === 0;
    var hora_invalida = $(".hora input").is(":invalid");
    var hora_incompleta = !($("input[name='hora']").val()) ^ !($("input[name='minutos']").val());

    //Autoridades de las cuales se cargo al menos un campo
    var autoridades_presentes = $("form.autoridad").filter(filtro1);
    //Dentro de las que se empezaron a cargarse, las que tienen campos vacios
    var autoridades_incompletas = autoridades_presentes.filter(filtro2);
    
    //Si esta todo bien, confirma ingreso
    if(!datos_invalidos && !documentos_invalidos && !documentos_numeros_invalidos &&
       !autoridades_incompletas.length && !largo_invalido &&
       !hora_incompleta && !hora_invalida){
        send("msg_confirmar_ingreso");
    } else {
        var mensaje = "";
        var error = constants.mensajes_error;
        if (hora_incompleta) {
            mensaje += "<li>" + error.hora_incompleta + "</li>";
        }
        if (hora_invalida) {
            mensaje += "<li>" + error.hora_invalida + "</li>";
        }
        if(largo_invalido) {
            mensaje += "<li>" + error.largo_invalido + "</li>";
        }
        if (datos_invalidos){
            mensaje += "<li>" +  error.autoridades_invalidas + "</li>";
        }
        if (documentos_invalidos){
            mensaje += "<li>" +  error.documentos_invalidos + "</li>";
        }
        if (documentos_numeros_invalidos){
            mensaje += "<li>" +  error.documentos_numeros_invalidos + "</li>";
        }
        if (autoridades_incompletas.length){
            mensaje += "<li>" + error.autoridades_incompletas + "</li>";
        }
        show_dialogo_error({"mensaje": {"alerta": mensaje},
                            "btn_aceptar": "error-validacion"});
    }
}

function salir() {
    send("salir");
}

function scroll_up() {
    var elem = $(".nombre-autoridades");
    var pos = elem.scrollTop();
    elem.scrollTop(pos - 200);
}

function scroll_down() {
    var elem = $(".nombre-autoridades");
    var pos = elem.scrollTop();
    elem.scrollTop(pos + 200);
}

function filterInt(value) {
    if(/^(\-|\+)?([0-9]+|Infinity)$/.test(value)) {
        return Number(value);
    } else {
        return NaN;
    }
}

function show_body(){
    /**/
}

jQuery.extend(jQuery.expr[':'], {
    invalid : function(elem, index, match){
        var invalids = document.querySelectorAll(':invalid'),
            result = false,
            len = invalids.length;

        if (len) {
            for (var i=0; i<len; i++) {
                if (elem === invalids[i]) {
                    result = true;
                    break;
                }
            }
        }
        return result;
    }
});
