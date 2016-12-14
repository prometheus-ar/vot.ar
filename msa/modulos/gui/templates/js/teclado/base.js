var get_url = null;
var patio_teclado = null;
var destination = null;

(function ($) {
    $.fn.load_teclados = function (options) {
        /*
         * Funcion que carga los teclados usando Patio y asocia los callbacks
         * de las teclas. Todos los argumentos son opcionales
         * Argumentos:
         * layout -- lista de layouts que debe cargar.
         *     Se corresponden con tiles del Patio cargado.
         * first_input -- selector del primer campo que utiliza el teclado
         * callback_finish -- funcion callback al llegar al ultimo campo
         *     de carga del formulario
         */
        var settings = $.extend({
            // These are the defaults.
            layout: ["qwerty"],
            first_input: "input.text:first",
            callback_finish: null,
        }, options);

        if(patio_teclado === null){
            patio_teclado = new Patio(this, layouts, [], "partials/teclado");
        }

        for(var t in settings.layout){
            var teclado = settings.layout[t];
            if(!$(patio_teclado[teclado].id).length){
                patio_teclado[teclado].load();
            }
            $(patio_teclado[teclado].button_filter).on('mousedown', resaltar_letra)
                                                   .on('mouseup', desresaltar_letra);
        }

        if(settings.callback_finish !== null){
            set_callback_aceptar(settings.callback_finish)
        }

        destination = jQuery(settings.first_input);
        $("body").on('mouseup', desresaltar_letra);
    }
})(jQuery);

function popular_teclado(id){
    /*
     * Parsea los layouts en arrays de diccionarios
     * con todas las teclas
     * Argumentos:
     * id - id del tile en la configuracion de Patio,
     *     debe coincidir con el nombre del tile en layouts
     */
    var rows = [];
    var keyname = id.slice(1);
    for(var i in keyboard_layouts[keyname]){
        var row = [];
        var fila = keyboard_layouts[keyname][i];
        if(fila.length){
            var boton = fila[0].split(" ");
            for (var j in boton){
                if (boton[j].slice(0,1) === "{"){
                    contenido = boton[j].slice(1,-1).split("|");
                    texto = (contenido.length == 2)? contenido[1] : contenido[0];
                    classname = contenido[0].toLowerCase();
                    action_key = true;
                } else {
                    texto = boton[j];
                    action_key = false;
                    classname = "regular";
                }
                row.push({"texto": texto,
                          "action_key": action_key,
                          "accion": classname,
                          "classname": "ui-keyboard-" + classname});
            }
        }
        rows.push(row);
    }
    return {"id": keyname, "rows": rows};
}

function mostrar_mensaje(mensaje, callback_positivo, callback_negativo){
    /*
     * Muestra un mensaje en el area del teclado
     * Argumentos:
     * mensaje -- contenido del mensaje que se muestra, acepta html
     * callback_positivo -- callback que se llama cuando se
     *     presiona aceptar
     * callback_negativo -- callback que se llama cuando se
     *     presiona cancelar. En caso de no estar, simplemente oculta
     *     el mensaje
     */
    if (!callback_negativo){
        var callback_negativo = ocultar_mensaje;
    }
    var selector = patio_teclado.mensaje.id;
    $(selector + " .texto").html(mensaje);
    $(selector + " .btn-aceptar").on("click",callback_positivo);
    $(selector + " .btn-cancelar").on("click",callback_negativo);
    $(".placeholder-confirma").show();
    patio_teclado.mensaje.only();
    destination.removeClass("seleccionado");
}

function ocultar_mensaje(){
    var selector = patio_teclado.mensaje.id;
    patio_teclado.mensaje.hide();
    $(".placeholder-confirma").hide();
    $(selector + " .action-button").off("click");
    procesar_dialogo(false);
    destination.addClass("seleccionado");
    destination.focus();
}

function set_callback_aceptar(callback_aceptar){
    /*
     * Asigna el callback al boton "aceptar"
     * Argumentos:
     * callback_aceptar -- funcion a asignar como callback
     */
    callbacks_especiales.aceptar = callback_aceptar;
}

function click_letra(data) {
    /*
     * Funcion que se ejecuta cuando se apreta una tecla del teclado
     * y decide que el callback que se llama segun si es especial o no
     * Argumentos:
     * data -- elemento de DOM que se presiono
     */
    if ($(data).hasClass("ui-keyboard-actionkey")){
        var accion = $(data).attr("data-accion");
        callbacks_especiales[accion](data);
    } else {
        var letra = $(data).text();
        escribir_letra(letra);
    }
}

function escribir_letra(letra){
    /*
     * Le agrega al campo destino el contenido de la tecla
     * Argumentos:
     * letra -- contenido de la tecla que se presiono
     */
    if(typeof(destination.attr("maxlength")) == "undefined"
       || destination.attr("maxlength") > destination.val().length){
        destination.val(destination.val() + letra);
        destination.focus();
        destination.trigger("change");
    }
}

//A continuación estan los callbacks de las teclas especiales
function boton_espacio(){
    escribir_letra(' ');
}

function boton_tilde(){
    escribir_letra("\'");
}

function seleccionar_documento(data){
    destination.val($(data).text());
    seleccionar_siguiente();
}

function seleccionar_siguiente() {
    /*
     * Encuentra el siguiente input y le asigna el foco
     */
    var siguiente = find_next_input(destination);
    if (typeof siguiente.attr("name") != "undefined") {
        destination = siguiente;
        destination.focus();
    }
}

function seleccionar_anterior() {
    /*
     * Encuentra el input anterior y le asigna el foco
     */
    var anterior = find_prev_input(destination);
    if (typeof anterior.attr("name") != "undefined") {
        destination = anterior;
        destination.focus();
    }
}

function boton_borrar() {
    /*
     * Borra el ultimo caracter del input seleccionado.
     * Si el campo estaba vacio, mueve el foco al campo anterior
     */
    if (destination.val().length > 0) {
        destination.val(
            destination.val().substring(0, destination.val().length - 1));
        destination.focus();
    } else {
        seleccionar_anterior();
    }
}

function resaltar_letra() {
   $(this).addClass("resaltado");
}

function desresaltar_letra() {
   $(".ui-keyboard-button").removeClass("resaltado");
}

function sonar_beep(data){
    beep(data);
}

function seleccionar_asterisco() {
    apretar_asterisco();
}

function seleccionar_numeral() {
    apretar_numeral();
}

function on_focus(destination) {
    $("input").removeClass("seleccionado");
    destination.addClass("seleccionado");
    var ultimo = destination.val().length;
    var sig = find_next_input(destination);
    var ant = find_prev_input(destination);
    
    if(destination.data("keyboard")){
        var keyboard_type = destination.data("keyboard");
        patio_teclado[keyboard_type].only();
        $(document).trigger("cambioTeclado");
    }

    if (sig.length > 0) {
        $('div.ui-keyboard-aceptar')
            .text('Siguiente')
            .addClass('ui-keyboard-siguiente')
            .removeClass('ui-keyboard-aceptar')
            .attr("data-accion","siguiente")
    } else {
        if(typeof(callbacks_especiales["aceptar"]) !== "undefined"){
            $('div.ui-keyboard-siguiente')
                .text('Aceptar')
                .addClass('ui-keyboard-aceptar')
                .removeClass('ui-keyboard-siguiente')
                .attr("data-accion","aceptar")
        }
    }

    if (sig.length === 0){
        $('div.ui-keyboard-siguiente')
            .addClass('disabled')
            .trigger('btnSiguienteDeshabilitado');
    } else {
        $('div.ui-keyboard-siguiente')
            .removeClass('disabled')
            .trigger('btnSiguienteHabilitado');
    }

    if (ant.length === 0){
        $('div.ui-keyboard-anterior')
            .addClass('disabled');
    } else {
        $('div.ui-keyboard-anterior')
            .removeClass('disabled');
    }

    if (this.setSelectionRange) {
        this.focus();
        this.setSelectionRange(ultimo, ultimo);
    }
    else if (this.createTextRange) {
        var range = this.createTextRange();
        range.collapse(true);
        range.moveEnd('character', ultimo);
        range.moveStart('character', ultimo);
        range.select();
    }
}

//Comportamiento para los inputs
$.fn.keyboard = function () {
    /*
     * Contiene el comportamiento cuando se hace foco en un campo:
     * Muestra el tipo de teclado que corresponde, lo marca como seleccionado
     * y adecua los botones de siguiente/anterior
     */
    this.addClass("text");
    this.focusin(function (){
        destination = $(this);
        on_focus(destination)
    });
    return $(this);
};

/* Auxiliares */
function find_next_input(elem){
    /*
     * Dado un elemento, retorna el proximo input
     * Argumentos:
     * elem -- elemento del dom del cual se busca el input siguiente
     */
    var sig = elem.nextAll("input").first();
    if (sig.length === 0){
        sig = elem.parent().nextAll("form").find("input").first(); 
    }
    if (sig.length === 0){
        sig = elem.parent().nextAll("div").find("input").first();
    }
    if (sig.length === 0){
        sig = elem.parent().parent().nextAll("div").find("input").first();
    }
    return sig;
}

function find_prev_input(elem){
    /*
     * Dado un elemento, retorna el input anterior
     * Argumentos:
     * elem -- elemento del dom del cual se busca el input que lo precede
     */
    var pre  = elem.prevAll("input").first();
    if (pre.length === 0){
        pre = elem.parent().prevAll("form").find("input").last();
    }
    if (pre.length === 0){
        pre = elem.parent().parent().prevAll("div").find("input").last();
    }
    return pre;
}

function sonido_teclado(){
    send("sonido_tecla");
}

function mostrar_teclado_simbolos(){
    var campo = $(".seleccionado").data("keyboard", "simbolos");
    on_focus(campo.first());
}

function mostrar_teclado_qwerty(){
    var campo = $(".seleccionado").data("keyboard", "alpha_sim")
    on_focus(campo.first());
}
