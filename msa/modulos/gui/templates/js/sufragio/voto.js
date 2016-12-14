var _categoria_actual = null;
var _categorias = null;
var _candidatos_seleccionados = null;
var _modo = null;
var revisando = false;
var _lista_seleccionada = null;

function cambiar_categoria(categoria){
    /*
     * Cambia la categoria actual.
     */
    _categoria_actual = categoria;
}

function limpiar_categorias(){
    /*
     * Limpia el recuadro de la seleccion de los candidatos.
     */
    $("#candidatos_seleccionados .candidato").removeClass("seleccionado");
}

function limpiar_data_categorias(){
    /*
     * Limpia la informacion de las categorias que se estan votando actualmente.
     */
    _categorias = null;
}

function get_categoria_actual(){
    /*
     * devuelve el codigo de la categoria actual.
     */
    return _categoria_actual;
}

function guardar_modo(modo){
    /*
     * Guarda el modo actual de votacion.
     */
    _modo = modo;
}

function get_modo(){
    /*
     * Devuelve el modo actual de votacion.
     */
    return _modo;
}

