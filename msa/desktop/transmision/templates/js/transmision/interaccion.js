function bindear_botones() {
    $('#btn_conectar').click(conectar);
    $('#btn_desconectar').click(desconectar);
    $('#btn_preferencias').click(preferencias);
    $('#btn_configurar_red').click(configurar_red);
    $('#btn_importar').click(importar);
    $('#btn_descargar').click(descargar);
    $('#btn_salir').click(salir);
    $('#btn_status').click(status);
    $('#btn_si').click(click_si);
    $('#btn_no').click(click_no);
    $('#btn_diagnostico').click(diagnostico);
    $('#btn_aplicaciones').click(aplicaciones);
}

function conectar() {
   hide_vista_acta();
   send('web_conectar');
}

function desconectar() {
    limpiar_ui();
    send('web_desconectar');
}
function preferencias() {
    send('web_mostrar_preferencias');
}
function configurar_red() {
    send('web_configurar_red');
}
function importar() {
    send('web_mostrar_importar_claves');
}
function descargar() {
    send('web_mostrar_autenticacion');
}

function salir() {
    send('web_salir');
}

function status() {
    limpiar_ui();
    msg_anterior = $('#mensaje').html();
    send('web_pantalla_status');
}

function click_si() {
    send('web_boton_si', _datos_tag);
    ocultar_confirmacion();
}

function click_no() {
    send('web_boton_no');
    ocultar_confirmacion();
}

function diagnostico() {
    send('web_pantalla_diagnostico');
}

function aplicaciones() {
    limpiar_ui();
    msg_anterior = $('#mensaje').html();
    send('web_pantalla_aplicaciones');
}
