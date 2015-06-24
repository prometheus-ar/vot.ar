function limpiar_ui() {
    ocultar_confirmacion();
    hide_botonera();
    hide_vista_acta();
    hide_vista_estados();
}

function hide_vista_estados(msg) {
    $('#contenedor_derecho').hide();
}

function show_vista_estados(msg) {
    $('#contenedor_derecho').show();
}

function hide_vista_acta(msg) {
    $('#contenedor_tab_imagenes').hide();
    $('#contenedor_imagen_acta').hide();
}

function mostrar_confirmacion(msg) {
    _datos_tag = msg;
    $('#confirmacion').show();
}

function ocultar_confirmacion(msg) {
    $('#confirmacion').hide();
    _datos_tag = null;
    reset_mesa_activa();
}

function hide_botonera() {
    $('#botonera').hide();
}

function show_botonera(html) {
    $('#botonera').html(html);
    $('#botonera').show();
}
