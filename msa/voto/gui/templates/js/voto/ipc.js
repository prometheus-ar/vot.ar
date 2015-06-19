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
    place_text(data.i18n);
    place_text(data.encabezado);
    var body = $("body");
    if(!constants.mostrar_cursor){
        body.css("cursor", "none");
    }
    body.addClass(constants.flavor);
    body.attr('data-ubicacion', constants.ubicacion);
    effects = constants.effects;
    preload(constants.imagenes)
}

function get_candidatos(_id_categoria, revisando, id_interna){
    /*
     * Pide los candidatos al backend.
     */
    if(_id_categoria === undefined) {
        _id_categoria = null;
    }
    if(revisando === undefined) {
        revisando = false;
    }
    if(id_interna === undefined) {
        id_interna = null;
    }

    send('get_candidatos', [_id_categoria, revisando, id_interna]);
}

function recargar_categorias(cod_categoria){
    /*
     * Pide la recarga de categorias al backend
     */
    send('cargar_categorias', [cod_categoria]);
}

function seleccionar_candidatos(cod_categoria, ids_candidatos){
    /*
     * Envia la solicitud de seleccion de candidatos al backend.
     */
    send('seleccionar_candidatos', [cod_categoria, ids_candidatos]);
}

function seleccionar_lista(id_lista, categoria_adhesion, candidatos_adhesion,
                           es_ultima){
    /*
     * Selecciona una lista dada.
     */
    send('seleccionar_lista', 
         [id_lista, categoria_adhesion, candidatos_adhesion, es_ultima]);
}

function seleccionar_partido(id_partido, id_categoria){
    /*
     * Selecciona un partido dado.
     */
    send('seleccionar_partido', [id_partido, id_categoria]);
}

function seleccionar_modo(modo){
    /*
     * Selecciona un modo dado.
     */
    send('seleccionar_modo', modo);
}

function seleccionar_idioma(modo){
    /*
     * Selecciona un idioma dado.
     */
    send('seleccionar_idioma', modo);
}

function get_pantalla_partidos(){
    /*
     * Solicita la pantalla de internas.
     */
    send('get_partidos');
}

function confirmar_seleccion(){
    /*
     * confirma la seleccion de candidatos.
     */
    send('confirmar_seleccion');
}

function change_screen(pantalla){
    /*
     * Recibe la pantalla a la que se debe cambiar y los parametros con los que
     * esa pantalla debe ser llamada.
     */
    func = eval(pantalla[0]);
    func(pantalla[1]);
}

function get_pantalla_voto(){
    /*
     * Solicita al backend la pantalla de voto.
     */
    send('get_pantalla_voto');
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

function procesar_dialogo(respuesta){
    /*
     * Procesa la respuesta del popup.
     */
    send('dialogo', respuesta);
}


function asterisco(numero){
    send('asterisco', numero);
}

function numeral(numero){
    send('numeral', numero);
}

