var _categoria_actual = null;
var _categorias = null;
var _candidatos_seleccionados = null;
var _modo = null;
var revisando = false;
var _lista_seleccionada = null;

function cambiar_categoria(cod_categoria){
    /*
     * Cambia la categoria actual.
     */
    _categoria_actual = cod_categoria;
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

function actualizar_categorias(nuevas_categorias){
    /*
     * Actualiza las categorias que se estan votando.
     */
    _categorias = {};
    _candidatos_seleccionados = [];
    for(var i in nuevas_categorias){
        var cat_actual = nuevas_categorias[i].categoria.codigo;
        _categorias[cat_actual] = nuevas_categorias[i].categoria;
        if(nuevas_categorias[i].candidato !== null){
            _candidatos_seleccionados.push(nuevas_categorias[i].candidato.codigo)
            _categorias[cat_actual].cod_candidato = nuevas_categorias[i].candidato.codigo;
        } else{
            _categorias[cat_actual].cod_candidato = null;
        }
    }
}

function get_data_categoria(codigo){
    /*
     * Devuelve la informacion sobre una categoria dada.
     */
    return _categorias[codigo];
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

