function show_elements(selector, callback) {
    var elems = $(selector);
    elems.show();
    if (callback != null) callback();
}

function hide_elements(selector, callback) {
    var elems = $(selector);
    elems.hide();
    if (callback != null) callback();
}

function show_dialogo_confirmacion() {
    mostrar_mensaje(constants.i18n.confirma_datos_correctos,
                    click_boton_confirmacion);
}

function hide_all(callback) {
    //En apertura
    hide_elements("#pantalla_inicio");
    hide_elements("#contenedor_opciones"); 
    hide_elements("#pantalla_confirmaciondatos");
    // En recuento
    hide_elements(".contenedor-datos");
    hide_elements(".contenedor-opciones-recuento");
    hide_elements(".contenedor-izq");
    hide_elements(".contenedor-der", callback);
}

