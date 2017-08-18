var constants = {};


function load_ready_msg(){
    /*
     * Envia la señar "document_ready" al backend.
     */
    send('document_ready');
}

function inicializar_interfaz(){
    /* Manda la señal de inicializar la interfaz de votacion. */
    send('inicializar_interfaz');
}

function cargar_cache(){
    /* Mand la señal de cargar el cache. */
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
    load_templates_sufragio(constants.templates);
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
    preload(constants.imagenes);
    if(constants.mostrar_indicador_capacitacion){
        $("#barra_opciones .cinta").show();
        $("#encabezado .cinta-capacitacion").show();
    }
}

function load_templates_sufragio(templates){
    /* Cargalos templates de sufragio. */
    if(constants.templates_compiladas){
        var url = constants.PATH_TEMPLATES_FLAVORS + constants.flavor + "/templates.html";
        load_template_comp(url);

        var url = constants.PATH_TEMPLATES_VAR + "sufragio.html";
        load_template_comp(url);
        cargar_templates_en_dom()
    } else {
        load_templates(templates);
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
    /* Envia la señal avisandole al backend que queremos previsualizar el
     * voto.
     */
    send("previsualizar_voto");
}

function confirmar_seleccion(){
    /* Envia la señal avisandole al backend que queremos confirmar la
     * seleccion.
     */
    send('confirmar_seleccion');
}

function asterisco(numero){
    /* le avisa al backend que apretamos el asterisco de asistida. */
    send('asterisco', numero);
}

function numeral(numero){
    /* le avisa al backend que apretamos el numeral de asistida. */
    send('numeral', numero);
}

function sonido_tecla(){
    /* le avisa al backend que tiene que lanzar el sonido de tecla apretada. */
    send("sonido_tecla");
}

function sonido_warning(){
    /* le avisa al backend que tiene que lanzar el sonido de alerta. */
    send("sonido_warning");
}
