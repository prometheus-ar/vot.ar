var old_width = null;

function repetir_pruebas() {
    send('web_get_status');
}

// Función llamada para mostrar las pruebas que se van a realizar
function cargar_pruebas(msg) {

    $('#btn_status').attr('disabled', 'disabled');
    $('#btn_conectar').attr('disabled', 'disabled');
    $('#btn_desconectar').attr('disabled', 'disabled');

    var spinner = get_template_spinner();
    var template = get_template_prueba();

    var rendered = '';

    for (var i = 0; i < msg.length; i++) {
        rendered += Mustache.render(template, { id_prueba: msg[i][0],
                                                desc_prueba: msg[i][1] });
    }

    var html = get_template_pantalla_pruebas(rendered);

    $('#contenedor_imagen_acta').html(html);
    $('#contenedor_imagen_acta').show();

    $('#btn-repetir').click(function() {
        repetir_pruebas();
        $('.res-prueba').html(spinner);
    });
    $('#btn-volver').click(function() {
        set_message(msg_anterior);
        $('#contenedor_imagen_acta').hide();
        $('#btn_status').removeAttr('disabled');
        $('#btn_conectar').removeAttr('disabled');
        $('#btn_desconectar').removeAttr('disabled');
        send('web_salir_pantalla_status');
    });
}


function estado_mesas(msg) {
    var html = '<ul class= "list-group" id="accordion" data-toggle="collapse"';
    html += ' data-parent="#accordion">';
    for (var i in msg) {
        var mesa = msg[i][0][0];
        var id_mesa = mesa.replace('&nbsp;', '-');
        var estado = msg[i][0][1];


        html += '<li class="list-group-item mesa-estados noselect ';
        html += get_color_class(estado) + '" id="' + id_mesa + '">';
        html += mesa;
        html += '<div class="pull-right estado-base ';
        html += get_color_class(estado) + '">' + estado + '</div>';
        html += '</li>';
        var clases = 'panel-collapse collapse lista-estados noselect';
        if (id_mesa == mesa_activa) {
            clases += ' in';
        }
        html += '<div class="' + clases + '" id="list_';
        html += id_mesa + '">';

        for (var j = 1; j < msg[i].length; j++) {
            var cargo = msg[i][j][0];
            var estado = msg[i][j][1];

            html += '<li class="list-group-item cargo-estados">';
            html += cargo;
            if (estado != 0) {
                var icono = 'glyphicon glyphicon-ok';
            } else {
                var icono = 'glyphicon glyphicon-minus';
            }
            html += '<div class="pull-right icono-estado ' + icono + '"></div>';
            html += '</li>';
        }
        html += '</div>';
    }
    html += '</ul>';
    $('#estado_mesas').html(html);
    $('.mesa-estados').click(bindear_estado_mesa);
}


function pantalla_aplicaciones(data) {
    set_message('Aplicaciones');
    old_width = $('#contenedor_izquierdo').attr('class');
    $('#contenedor_izquierdo').removeClass(old_width);
    $('#contenedor_izquierdo').addClass('col-md-12');
    $('#btn_status').attr('disabled', 'disabled');
    $('#btn_diagnostico').attr('disabled', 'disabled');

    var template_app = get_template_aplicacion();
    var rendered = '';

    for (var i = 0; i < data.length; i++) {
        var app = data[i];

        rendered += Mustache.render(template_app, app);
    }

    var html = get_template_pantalla_aplicaciones(rendered)

    $('#contenedor_imagen_acta').html(html);
    $('#contenedor_imagen_acta').show();

    var botonera = '\
        <div class="col-md-offset-1">\
            <button class="btn btn-default navbar-btn btn-lg pull-left" id="btn_volver"><span class="glyphicon glyphicon-arrow-left"></span><br />Volver</button>\
        </div>';

    show_botonera(botonera);

    $('.lanzador').click(function() {
        var cmd = $('#comando_' + $(this).attr('id')).text();
        send('web_run_app', cmd);

        // Agrego un timeout para que no sea tan brusca la salida
        setTimeout(salir_pantalla_aplicaciones, 300);
    });

    $('#btn_volver').click(salir_pantalla_aplicaciones);
}

function salir_pantalla_aplicaciones() {
    set_message(msg_anterior);

    $('#contenedor_imagen_acta').html('');
    $('#contenedor_izquierdo').removeClass('col-md-12');
    $('#contenedor_izquierdo').addClass(old_width);
    $('#btn_status').removeAttr('disabled');
    $('#btn_diagnostico').removeAttr('disabled');

    hide_vista_acta();
    hide_botonera();

    if ($('#btn_desconectar').is(":visible")) {
        show_vista_estados();
    }
}
