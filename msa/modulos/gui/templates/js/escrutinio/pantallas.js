function popular_loader(){
    /*
     * Devuelve los datos a usar en la populacion del template de la
     * pantalla_loader.
     */
    return {
        "cargando_interfaz": constants.i18n.cargando_interfaz,
        "espere_por_favor": constants.i18n.espere_por_favor,
    };
}

function pantalla_loader(){
    /*
     * Muestra la pantalla del loader.
     */
    var pantalla = patio.pantalla_loader;
    pantalla.only();
}
