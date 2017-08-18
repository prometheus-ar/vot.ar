function document_ready(){
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    $(".popup-box").on("hideDialogo", restaurar_foco_invalido);
}

$(document).ready(document_ready);

//Funciones que envian datos
function enviar_mesaypin(){
    // Envía al backend la mesa y pin ingresada por el usuario
    var nro_mesa = document.getElementsByName("nro_mesa")[0].value;
    var nro_pin = obtener_pin();

    mensaje_validando_mesa();

    setTimeout(
        function(){
            if(validar_pin(nro_pin)) {
                var data = {
                    "mesa": nro_mesa,
                    "pin": nro_pin.substr(0, nro_pin.length - 1)
                };
                send("recibir_mesaypin", data);
            }
        
        },
        200);
}

function enviar_datospersonales() {
    // Envía al backend la hora y los datos de las autoridades de mesa
    // Obtenemos los cargos que hay en la pantalla
    
    var lista_cargos = [];
    var elem_cargos = document.querySelectorAll(".cargo");
    elem_cargos.forEach(function(elem, index, lista){
        lista_cargos.push(elem.dataset.cargo);
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
    var hora = {'horas': filterInt($("input[name='hora']").val()),
            'minutos': filterInt($("input[name='minutos']").val())
    };

    var data = {
        'hora': hora,
        'autoridades': autoridades
    };

    send("recibir_datospersonales", data);
}

function msg_mesa_y_pin_incorrectos(){
    var template = get_template("popup", "partials/popup");
    var mensaje = constants.i18n.mesa_pin_incorrectos;
    var datos_invalidos = $(".mesaypin input").is(":invalid");
    var template_data = {
        alerta: mensaje,
        btn_aceptar: true,
        btn_cancelar: false,
        clase_aceptar: (datos_invalidos)? "error-validacion" : false
    }
    var html_contenido = template(template_data);
    return html_contenido;
}

function msg_error_validacion(mensaje){
    var template = get_template("popup", "partials/popup");
    var template_data = {
        alerta: mensaje,
        btn_aceptar: true,
        btn_cancelar: false,
        clase_aceptar: "error-validacion"
    } 
    var html_contenido = template(template_data); 
    return html_contenido;
}

function aceptar_mesa_y_pin(){
    var datos_invalidos = $(".mesaypin input").is(":invalid");
    var pin = obtener_pin();
    if(!datos_invalidos && validar_pin(pin)){
        send("msg_confirmar_ingreso");
    } else {
        cargar_dialogo("msg_mesa_y_pin_incorrectos");
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

    function validacion_documento(){
        var campos = $(".nombre-autoridades input.nro_documento");
        var array_valores = $.map(campos, function(item){ return $(item).val().length < 9 });
        return $.inArray(false, array_valores) !== -1;
    }

    var datos_invalidos = $(".nombre-autoridades input:not(.nro_documento)").is(":invalid");
    var largo_invalido = $(".nombre-autoridades input:not(.nro_documento)").is(filtro_largo);
    var documentos_invalidos = $(".nombre-autoridades input.nro_documento").is(":invalid");
    var documentos_numeros_invalidos = validacion_documento();
    var hora_vacia = !($("input[name='hora']").val()) && !($("input[name='minutos']").val());
    var hora_invalida = $(".hora input").is(":invalid") || $("input[name='hora']").val() === "1";
    var hora_incompleta = !($("input[name='hora']").val()) ^ !($("input[name='minutos']").val());

    //Autoridades de las cuales se cargo al menos un campo
    var autoridades_presentes = $("form.autoridad").filter(filtro1);
    var hay_autoridades = autoridades_presentes.length > 0;
    //Dentro de las que se empezaron a cargarse, las que tienen campos vacios
    var autoridades_incompletas = autoridades_presentes.filter(filtro2);
    
    //Si esta todo bien, confirma ingreso
    if(!datos_invalidos && !documentos_invalidos && !documentos_numeros_invalidos &&
       !autoridades_incompletas.length && !largo_invalido && hay_autoridades &&
       !hora_incompleta && !hora_invalida && !hora_vacia){
        send("msg_confirmar_ingreso");
    } else {
        var mensaje = "";
        var error = constants.mensajes_error;
        if (hora_vacia) {
            mensaje += "<li>" + error.hora_vacia + "</li>";
        }
        if (hora_incompleta) {
            mensaje += "<li>" + error.hora_incompleta + "</li>";
        }
        if (hora_invalida) {
            mensaje += "<li>" + error.hora_invalida + "</li>";
        }
        if (!hay_autoridades){
            mensaje += "<li>" +  error.debe_cargar_autoridad + "</li>";
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
        //Refactorear este popup de error
        cargar_dialogo_default({pregunta: mensaje,
                                btn_aceptar: true});

      $( ".mensaje-popup" ).addClass( "lista-popup" );
    }
}

function mostrar_tooltip(){
    if(typeof($(destination).data("tooltip")) !== "undefined"
            && $(destination).data("tooltip")){
        $(".ingreso").addClass("con-tooltip");
        $(".ingreso + .tooltip").show();
    } else {
        $(".ingreso").removeClass("con-tooltip");
        $(".ingreso + .tooltip").hide();
    }
}

//Auxiliares y otras
function obtener_pin(){
    var campos = document.querySelectorAll("[name^=nro_pin]");
    var pin = "";
    for(var i=0; i < campos.length; i++){
        pin = pin.concat(campos[i].value);
    }
    return pin;
}

function validar_pin(nro_pin){
    var suma = 0;
    var pin = nro_pin.split("");
    var digito_verificador = pin.pop();
    for(var letra in pin){
        suma += pin[letra].charCodeAt();
    }
    caracter = suma % 10;
    return caracter == parseInt(digito_verificador);
}

function revalida_hora(){
    var elemento = document.getElementsByName("hora")[0];
    var activo = document.activeElement;
    if ((elemento.value == 2 || elemento.value == 1) &&
         elemento != activo && !elemento.classList.contains("seleccionado")){
        elemento.setCustomValidity("Invalid");
    } else {
        elemento.setCustomValidity("");
    }
}

function autopasa_campo(event){
    var elemento_hora = document.getElementsByName("hora")[0];
    var elemento_minutos = document.getElementsByName("minutos")[0];
    var activo = document.activeElement;

    var hora_valida_apertura = (event.data === "apertura" && activo == elemento_hora &&
        (elemento_hora.value == 8 || elemento_hora.value == 9));

    if (hora_valida_apertura || activo.value.length == 2){
        seleccionar_siguiente();
    }
}

function autopasa_campo_datos(){
  var activo = $(this);
  var atributo =  activo.attr("maxlength");

  if (activo.val().length >= atributo){
      seleccionar_siguiente();
  }
}

function deshabilitar_teclado() {
    $(".contenedor-datos input, .contenedor-datos select")
        .bind('keydown', function(event){
            event.preventDefault();
        });
}

function set_mensaje(data) {
    $(".contenedor-texto h1").html(data);
}

function inicializar_teclado(lista_teclados, callback_aceptar) {
    $("#keyboard").load_teclados({layout: lista_teclados,
                                  callback_finish: callback_aceptar});
    $("input[type='text']").keyboard();
}


function salir() {
    send("salir");
}

function bindear_scrolls() {
    $("#_btn_scroll_arriba").on("click", scroll_up);
    $("#_btn_scroll_abajo").on("click", scroll_down);
}

function scroll_up() {
    var elem = $(".nombre-autoridades");
    var pos = elem.scrollTop();
    elem.scrollTop(pos - 50);
}

function scroll_down() {
    var elem = $(".nombre-autoridades");
    var pos = elem.scrollTop();
    elem.scrollTop(pos + 50);
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
