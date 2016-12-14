var constants = {};


function load_ready_msg(){
    /*
     * Envia la señar "document_ready" al backend.
     */
    send('document_ready');
}

function inicializar_interfaz(){
    send('inicializar_interfaz');
}

function cargar_cache(){
    send('cargar_cache');
}

function set_constants(data){
    /*
     * Establece las constantes que llegan desde el backend.
     * Arguments:
     * data -- un objeto con las constantes
     */
    constants = data;
    var head = $("head");
    popular_html();
    load_patio();
    place_text(data.i18n);
    place_text(data.encabezado);
    var body = $("body");
    if(!constants.mostrar_cursor){
        body.css("cursor", "none");
    }
    body.addClass(constants.flavor);
    load_css(constants.flavor);
    body.attr('data-ubicacion', constants.ubicacion);
    load_templates(constants.templates);
    preload(constants.imagenes);
    if(constants.mostrar_indicador_capacitacion){
        $("#barra_opciones .cinta").show();
        $("#encabezado .cinta-capacitacion").show();
    }
}

function seleccionar_idioma(modo){
    /*
     * Selecciona un idioma dado.
     */
    send('seleccionar_idioma', modo);
}

function change_screen(pantalla){
    /*
     * Recibe la pantalla a la que se debe cambiar y los parametros con los que
     * esa pantalla debe ser llamada.
     */
    func = window[pantalla[0]];
    func(pantalla[1]);
}

function prepara_impresion(){
    /*
     * Envia la señal para preparar la impresion.
     */
    send('prepara_impresion');
}

function previsualizar_voto(){
    send("previsualizar_voto");
}

function confirmar_seleccion(){
    send('confirmar_seleccion');
}

function asterisco(numero){
    send('asterisco', numero);
}

function numeral(numero){
    send('numeral', numero);
}

function sonido_tecla(){
    send("sonido_tecla");
}

function sonido_warning(){
    send("sonido_warning");
}
